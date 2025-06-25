import os
import numpy as np
import pickle
import xgboost as xgb
from rdkit import Chem, DataStructs
from rdkit.Chem import AllChem, MACCSkeys
import deepchem as dc
from functools import lru_cache
import time
import logging # Use logging instead of print for production apps
from concurrent.futures import ThreadPoolExecutor

# --- Configuration ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DIR = os.path.join(BASE_DIR, "ml_models")
XGB_FEATURE_NAMES = [f"bit{i}" for i in range(2048)]
LOGGER = logging.getLogger(__name__)

# --- Pre-loaded Models & Featurizers ---
MODELS = {}
PUBCHEM_FEATURIZER = dc.feat.PubChemFingerprint()

def load_all_models():
    """
    Finds and loads all supported model files from the MODEL_DIR.
    This function should be called ONCE when the app worker starts.
    """
    LOGGER.info("--- Loading all ML models into memory... ---")
    for filename in os.listdir(MODEL_DIR):
        model_path = os.path.join(MODEL_DIR, filename)
        try:
            if filename.endswith(".pkl"):
                with open(model_path, "rb") as f:
                    model = pickle.load(f)
            elif filename.endswith(".json"):
                model = xgb.Booster()
                model.load_model(model_path)
            else:
                continue # Skip unsupported files

            MODELS[filename] = model
            LOGGER.info(f"  [+] Loaded model: {filename}")
        except Exception as e:
            LOGGER.error(f"  [!] Failed to load model {filename}: {e}")
    LOGGER.info("--- Model loading complete. ---")


# --- Featurization Functions (with Caching) ---

# A map to simplify calling the correct featurizer
FEATURIZER_MAP = {
    "ecfp": lambda smiles: smiles_to_ecfp(smiles),
    "maccs": lambda smiles: smiles_to_maccs(smiles),
    "pubchemfp": lambda smiles: smiles_to_pubchemfp(smiles)
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

@lru_cache(maxsize=2048)
def smiles_to_maccs(smiles):
    """Convert SMILES to MACCS keys fingerprint with caching."""
    mol = Chem.MolFromSmiles(smiles)
    if not mol: return None
    fp = MACCSkeys.GenMACCSKeys(mol)
    array = np.zeros((166,), dtype=np.float32) # MACCS has 166 bits (1-166)
    # The first bit (index 0) is unused, so we convert the 167-bit vector
    DataStructs.ConvertToNumpyArray(fp, array)
    return array

@lru_cache(maxsize=2048)
def smiles_to_pubchemfp(smiles):
    """Convert SMILES to PubChem fingerprint with caching."""
    fingerprints = PUBCHEM_FEATURIZER.featurize(smiles)
    # Check if featurization was successful before accessing the array
    return fingerprints[0] if fingerprints.size > 0 else None

# --- Prediction Logic ---

def predict_batch_ic50(smiles_list, model_name, model_method, model_descriptor):
    """
    Predict IC50 for a batch of SMILES using a pre-loaded model.
    """

    overall_start_time = time.perf_counter()

    model = MODELS.get(model_name)
    if model is None:
        raise ValueError(f"Model '{model_name}' not found or failed to load.")

    # Step 1: Featurize all SMILES in a batch
    feat_start_time = time.perf_counter()
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
        feat_end_time = time.perf_counter()
        LOGGER.info(f"[TIMING] Featurization loop for {len(smiles_list)} items: {(feat_end_time - feat_start_time) * 1000:.4f} ms")
    
    if not fingerprints:
        return errors # Return only errors if no valid SMILES were found

    # Step 2: Stack fingerprints into a single NumPy array for batch prediction
    stack_start_time = time.perf_counter()
    fp_array = np.vstack(fingerprints)
    stack_end_time = time.perf_counter()
    LOGGER.info(f"[TIMING] NumPy stacking of {len(fingerprints)} fingerprints: {(stack_end_time - stack_start_time) * 1000:.4f} ms")

    # Step 3: Normalize and Predict on the entire batch
    pred_start_time = time.perf_counter()
    if model_method == "rf":
        predictions = model.predict(fp_array)
    elif model_method == "xgb":
        dmatrix = xgb.DMatrix(fp_array, feature_names=XGB_FEATURE_NAMES)
        predictions = model.predict(dmatrix)
    else:
        raise ValueError("Unsupported model method")
    pred_end_time = time.perf_counter()
    LOGGER.info(f"[TIMING] Model prediction on batch of size {fp_array.shape[0]}: {(pred_end_time - pred_start_time) * 1000:.4f} ms")

    # Step 4: Combine results with original SMILES and any errors
    format_start_time = time.perf_counter()
    results_map = {smiles: float(pred) for smiles, pred in zip(valid_smiles, predictions)}
    results_map.update(errors)
    final_results = [results_map.get(s, None) for s in smiles_list]  # Ensure order matches input
    format_end_time = time.perf_counter()
    LOGGER.info(f"[TIMING] Result formatting: {(format_end_time - format_start_time) * 1000:.4f} ms")
    
    overall_end_time = time.perf_counter()
    LOGGER.info(f"[TIMING] Total 'predict_batch_ic50' execution: {(overall_end_time - overall_start_time) * 1000:.4f} ms")

    # Return results in the same order as the input
    return final_results