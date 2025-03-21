# import os
# import numpy as np
# import tensorflow as tf
# from rdkit import Chem, DataStructs
# from rdkit.Chem import AllChem

# # Correct the model path
# BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# MODEL_PATH = os.path.join(BASE_DIR, "ml_models", "model_ECFP_DL.h5")

# # Load TensorFlow model
# model = tf.keras.models.load_model(MODEL_PATH, compile=False)

# def smiles_to_ecfp6(smiles, radius=3, n_bits=2048):
#     """Converts a SMILES string to an ECFP6 fingerprint vector."""
#     mol = Chem.MolFromSmiles(smiles)
#     if mol is None:
#         return None  # Invalid SMILES
    
#     fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius, nBits=n_bits)
    
#     array = np.zeros((1, n_bits))
#     DataStructs.ConvertToNumpyArray(fp, array[0])
    
#     return array.astype(np.float32)  # Ensure float32 for TensorFlow

# def predict_ic50(smiles):
#     """Predicts IC50 from a SMILES string using a pre-trained model."""
#     fingerprint = smiles_to_ecfp6(smiles)
    
#     if fingerprint is None:
#         return None  # Invalid SMILES

#     prediction = model.predict(fingerprint)
    
#     return float(prediction[0][0])  # Convert to Python float


# import os
# import numpy as np
# import tensorflow as tf
# import pickle
# import xgboost as xgb
# from rdkit import Chem, DataStructs
# from rdkit.Chem import AllChem

# # Define Base Model Path
# BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# MODEL_DIR = os.path.join(BASE_DIR, "ml_models")

# # Global cache to store loaded models
# MODEL_CACHE = {}

# def load_model(model_name):
#     """Load model from disk and cache it."""
#     if model_name in MODEL_CACHE:
#         return MODEL_CACHE[model_name]  # Return cached model

#     model_path = os.path.join(MODEL_DIR, model_name)
    
#     if model_name.endswith(".h5"):  # Deep Learning
#         model = tf.keras.models.load_model(model_path, compile=False)
#     elif model_name.endswith(".pkl"):  # Random Forest
#         with open(model_path, "rb") as f:
#             model = pickle.load(f)
#     elif model_name.endswith(".json"):  # XGBoost
#         model = xgb.Booster()
#         model.load_model(model_path)
#     else:
#         raise ValueError("Unsupported model format")

#     MODEL_CACHE[model_name] = model  # Store in cache
#     return model

# def smiles_to_ecfp6(smiles, radius=3, n_bits=2048):
#     mol = Chem.MolFromSmiles(smiles)
#     if mol is None:
#         raise ValueError("Invalid SMILES input!")  # Explicit error
    
#     fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius, nBits=n_bits)
    
#     array = np.zeros((1, n_bits))
#     DataStructs.ConvertToNumpyArray(fp, array[0])
    
#     return array.astype(np.float32)  # Ensure float32 for TensorFlow

# def predict_ic50(smiles, model_name):
#     """Predict IC50 based on a given SMILES and model name."""
#     try:
#         fingerprint = smiles_to_ecfp6(smiles)
#     except ValueError as e:
#         return {"error": str(e)}

#     model = load_model(model_name)

#     if model_name.endswith(".h5"):  # TensorFlow
#         prediction = model.predict(fingerprint)
#         return float(prediction[0][0])
#     elif model_name.endswith(".pkl"):  # Random Forest
#         return float(model.predict(fingerprint)[0])
#     elif model_name.endswith(".json"):  # XGBoost
#         feature_names = [f"bit{i}" for i in range(fingerprint.shape[1])]
#         dmatrix = xgb.DMatrix(fingerprint, feature_names=feature_names)
#         return float(model.predict(dmatrix)[0])
#     else:
#         raise ValueError("Unsupported model format")


import os
import numpy as np
import tensorflow as tf
import pickle
import xgboost as xgb
import weakref
from rdkit import Chem, DataStructs
from rdkit.Chem import AllChem
from functools import lru_cache

# Define Base Model Path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DIR = os.path.join(BASE_DIR, "ml_models")

# Global dictionary for cached models
MODEL_CACHE = weakref.WeakValueDictionary()

# Precompute feature names for XGBoost (2048 bits)
XGB_FEATURE_NAMES = [f"bit{i}" for i in range(2048)]

def load_model(model_name):
    """Load model from disk and cache it if not already loaded."""
    if model_name in MODEL_CACHE:
        return MODEL_CACHE[model_name]  # Return cached model

    model_path = os.path.join(MODEL_DIR, model_name)
    
    if model_name.endswith(".h5"):  # TensorFlow
        model = tf.keras.models.load_model(model_path, compile=False)
    elif model_name.endswith(".pkl"):  # Random Forest
        with open(model_path, "rb") as f:
            model = pickle.load(f)
    elif model_name.endswith(".json"):  # XGBoost
        model = xgb.Booster()
        model.load_model(model_path)
    else:
        raise ValueError("Unsupported model format")

    MODEL_CACHE[model_name] = model  # Store in cache with weak reference
    return model

@lru_cache(maxsize=1000)
def smiles_to_ecfp6(smiles, radius=3, n_bits=2048):
    """Convert a SMILES string to an ECFP6 fingerprint vector with caching."""
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None  # Invalid SMILES
    
    fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius, nBits=n_bits)
    
    array = np.zeros((1, n_bits), dtype=np.float32)
    DataStructs.ConvertToNumpyArray(fp, array[0])
    
    return array  # Already float32

def predict_ic50(smiles, model_name):
    """Predict IC50 based on a given SMILES and model name."""
    fingerprint = smiles_to_ecfp6(smiles)
    
    if fingerprint is None:
        return {"error": "Invalid SMILES input!"}

    model = load_model(model_name)

    if model_name.endswith(".h5"):  # TensorFlow Model
        prediction = model.predict(fingerprint, verbose=0)  # Suppress verbose output
        return float(prediction[0][0])
    elif model_name.endswith(".pkl"):  # Random Forest
        return float(model.predict(fingerprint)[0])
    elif model_name.endswith(".json"):  # XGBoost
        dmatrix = xgb.DMatrix(fingerprint, feature_names=XGB_FEATURE_NAMES)
        return float(model.predict(dmatrix)[0])
    
    return {"error": "Unsupported model format"}
