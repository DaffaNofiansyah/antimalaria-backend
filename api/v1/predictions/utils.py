import numpy as np
import pickle
import xgboost as xgb
from rdkit import Chem, DataStructs
from rdkit.Chem import AllChem
# import deepchem as dc
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor
from django.conf import settings

# --- Configuration ---
MODEL_DIR = settings.ML_MODEL_DIR
XGB_FEATURE_NAMES = [f"bit{i}" for i in range(2048)]
# --- Pre-loaded Models & Featurizers ---
MODELS = {}
# PUBCHEM_FEATURIZER = dc.feat.PubChemFingerprint()

def load_all_models():
    """
    Loads all supported ML model files from MODEL_DIR into memory.
    Supported formats: .pkl (pickle), .json (xgboost Booster).
    """
    MODEL_DIR.mkdir(parents=True, exist_ok=True)  # Ensure directory exists

    for model_path in MODEL_DIR.iterdir():
        if not model_path.is_file():
            continue  # skip directories, etc.

        try:
            if model_path.suffix == ".pkl":
                with model_path.open("rb") as f:
                    model = pickle.load(f)
            elif model_path.suffix == ".json":
                model = xgb.Booster()
                model.load_model(str(model_path))
            else:
                continue

            # Use model name without extension as key
            model_name = model_path.name
            MODELS[model_name] = model

        except Exception as e:
            print(f"Failed to load model {model_path.name}: {e}")


# --- Featurization Functions (with Caching) ---

# A map to simplify calling the correct featurizer
FEATURIZER_MAP = {
    "ecfp": lambda smiles: smiles_to_ecfp(smiles),
    # "maccs": lambda smiles: smiles_to_maccs(smiles),
    # "pubchemfp": lambda smiles: smiles_to_pubchemfp(smiles)
}

@lru_cache(maxsize=2048) # Increased cache size for batch operations
def smiles_to_ecfp(smiles, radius=3, n_bits=2048):
    """Convert a SMILES string to an ECFP6 fingerprint vector with caching."""
    mol = Chem.MolFromSmiles(smiles)
    if mol is None: return None
    fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius, nBits=n_bits)
    array = np.zeros((n_bits,), dtype=np.float32) # Return a 1D array
    DataStructs.ConvertToNumpyArray(fp, array)
    return array

# @lru_cache(maxsize=2048)
# def smiles_to_maccs(smiles):
#     """Convert SMILES to MACCS keys fingerprint with caching."""
#     mol = Chem.MolFromSmiles(smiles)
#     if not mol: return None
#     fp = MACCSkeys.GenMACCSKeys(mol)
#     array = np.zeros((166,), dtype=np.float32) # MACCS has 166 bits (1-166)
#     # The first bit (index 0) is unused, so we convert the 167-bit vector
#     DataStructs.ConvertToNumpyArray(fp, array)
#     return array

# @lru_cache(maxsize=2048)
# def smiles_to_pubchemfp(smiles):
#     """Convert SMILES to PubChem fingerprint with caching."""
    fingerprints = PUBCHEM_FEATURIZER.featurize(smiles)
#     # Check if featurization was successful before accessing the array
#     return fingerprints[0] if fingerprints.size > 0 else None

# --- Prediction Logic ---

def predict_batch_ic50(smiles_list, model_name, model_method, model_descriptor):
    """
    Predict IC50 for a batch of SMILES using a pre-loaded model.
    """
    model = MODELS.get(model_name)
    if model is None:
        raise ValueError(f"Model '{model_name}' not found or failed to load.")

    # Step 1: Featurize all SMILES in a batch
    featurizer = FEATURIZER_MAP.get(model_descriptor)
    if featurizer is None:
        raise ValueError("Unsupported model descriptor.")
    
    # Use a ThreadPoolExecutor to process featurization in parallel
    with ThreadPoolExecutor() as executor:
        # map() maintains the order of the input smiles_list
        results = list(executor.map(featurizer, smiles_list))

    fingerprints, valid_smiles, errors = [], [], {}
    for i, fp in enumerate(results):
        smiles = smiles_list[i]
        if fp is not None:
            fingerprints.append(fp)
            valid_smiles.append(smiles)
        else:
            errors[smiles] = "Invalid SMILES input"
    
    if not fingerprints:
        return errors # Return only errors if no valid SMILES were found

    # Step 2: Stack fingerprints into a single NumPy array for batch prediction
    fp_array = np.vstack(fingerprints)

    # Step 3: Normalize and Predict on the entire batch
    # if model_method == "rf":
    #     predictions = model.predict(fp_array)
    if model_method == "xgb":
        dmatrix = xgb.DMatrix(fp_array, feature_names=XGB_FEATURE_NAMES)
        predictions = model.predict(dmatrix)
    else:
        raise ValueError("Unsupported model method")

    # Step 4: Combine results with original SMILES and any errors
    results_map = {smiles: float(pred) for smiles, pred in zip(valid_smiles, predictions)}
    results_map.update(errors)
    final_results = [results_map.get(s, None) for s in smiles_list]  # Ensure order matches input

    # Return results in the same order as the input
    return final_results