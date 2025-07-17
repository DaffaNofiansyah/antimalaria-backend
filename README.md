# Django API for Compound Prediction

This project is a Django REST API that provides functionality for user authentication, compound data retrieval, IC50 prediction, and Google authentication.

## Features
- **User Authentication**
  - Registration
  - Login (JWT Authentication)
  - Google OAuth Login
- **Compound Data Management**
  - Retrieve a list of compounds
  - Retrieve detailed compound information
- **Prediction Management**
  - Submit SMILES strings for IC50 prediction
  - Retrieve a list of user-specific predictions
  - View detailed prediction data

## Tech Stack
- **Backend**: Django, Django REST Framework
- **Authentication**: Simple JWT, Google OAuth
- **Database**: PostgreSQL
- **External APIs**: PubChem for compound data

## Prasyarat

Sebelum memulai, pastikan Anda sudah menginstal hal-hal berikut:

- Python ^3.9
- pip (Python package installer)
- PostgreSQL (jika menggunakan PostgreSQL sebagai database)

## Instalasi

Ikuti langkah-langkah berikut untuk meng-clone dan men-setup proyek.

### 1. Clone repository

Clone repository proyek ke mesin lokal Anda menggunakan Git:

```bash
git clone https://github.com/DaffaNofiansyah/antimalaria-backend.git
cd antimalaria-backend
```

### 2. Membuat virtual environment

```bash
python -m venv venv
.\venv\Scripts\activate
```

### 3. Instal dependensi

```bash
pip install -r requirements.txt
```

File requirements.txt mencakup paket-paket berikut:

Django==5.1.4
djangorestframework
psycopg2 (untuk PostgreSQL)
django-environ (untuk mengelola env)
djangorestframework-simplejwt (untuk JWT authentication)

### 4. Konfigurasi database dan .env

Pastikan database PostgreSQL sudah disiapkan sebelumnya. Buat file .env di root proyek dan tambahkan variabel lingkungan yang diperlukan (seperti pengaturan database):

```bash
DB_NAME=(nama_database)
DB_USER=(user_database)
DB_PASSWORD=(password_database)
DB_HOST=localhost
DB_PORT=5432
```

### 6. Terapkan migrasi database

Jalankan migrasi untuk menyiapkan skema database:

```bash
python manage.py migrate
```

### 7. Menjalankan server pengembangan

```bash
python manage.py runserver
```


# API Documentation

## Overview
This API provides authentication, compound prediction, and user management features. It supports user registration, login, token-based authentication, compound data retrieval, and IC50 prediction.

## Base URL
```
https://antimalaria-backend-production.up.railway.app/
```

## Authentication
This API uses JWT authentication.
- Obtain tokens via `/login/`
- Refresh tokens via `/refresh-token/`
---

## Endpoints

### 1. Register a User
**Endpoint:**
```
POST /register/
```
**Request Body:**
```json
{
  "username": "your_username",
  "email": "your_email@example.com",
  "password": "your_password",
  "password2": "your_password"
}
```
**Response:**
```json
{
  "message": "User registered successfully"
}
```

---

### 2. Login
**Endpoint:**
```
POST /login/
```
**Request Body:**
```json
{
  "username": "your_username",
  "password": "your_password"
}
```
**Response:**
```json
{
  "refresh": "your_refresh_token",
  "access": "your_access_token",
  "username": "your_username",
  "email": "your_email"
}
```

---

### 3. Refresh Token
**Endpoint:**
```
POST /refresh-token/
```
**Request Body:**
```json
{
  "refresh": "your_refresh_token"
}
```
**Response:**
```json
{
  "access": "new_access_token"
}
```

---

### 4. Get List of Compounds Library (Not Created from Predictions)
**Endpoint:**
```
GET /compounds/base/
```
**Response:**
```json
[
  {
    "id": 1,
    "iupac_name": "ethene",
    "smiles": "C=C",
    "cid": 6325,
    "ic50": 4.262408256530762,
    "category": "Inactive",
    "molecular_formula": "C2H4",
    "molecular_weight": "28.05",
    "synonyms": "ETHYLENE, Ethene, Acetene, Elayl, Olefiant gas, 74-85-1, Athylen, Etileno, Bicarburretted hydrogen, Liquid ethylene, Ethylene, pure, Caswell No. 436, Aethylen, ...",
    "inchi": "InChI=1S/C2H4/c1-2/h1-2H2",
    "inchikey": "VGGSQFUCUMXWEO-UHFFFAOYSA-N",
    "structure_image": "https://pubchem.ncbi.nlm.nih.gov/image/imgsrv.fcgi?cid=6325&t=l",
    "description": "Ethene is an alkene and a gas molecular entity. It has a role as a refrigerant and a plant hormone."
  },
  {
    "id": 2,
    "iupac_name": "ethene",
    "smiles": "C=C",
    "cid": 6325,
    "ic50": 4.262408256530762,
    "category": "Inactive",
    "molecular_formula": "C2H4",
    "molecular_weight": "28.05",
    "synonyms": "ETHYLENE, Ethene, Acetene, Elayl, Olefiant gas, 74-85-1, Athylen, Etileno, Bicarburretted hydrogen, Liquid ethylene, Ethylene, pure, Caswell No. 436, Aethylen, ...",
    "inchi": "InChI=1S/C2H4/c1-2/h1-2H2",
    "inchikey": "VGGSQFUCUMXWEO-UHFFFAOYSA-N",
    "structure_image": "https://pubchem.ncbi.nlm.nih.gov/image/imgsrv.fcgi?cid=6325&t=l",
    "description": "Ethene is an alkene and a gas molecular entity. It has a role as a refrigerant and a plant hormone."
  }
]
```

### 5. Get List of User Predicted Compounds
**Endpoint:**
```
GET /compounds/
```
**Headers:**
```
Authorization: Bearer your_access_token
```
**Response:**
```json
[
  {
    "id": 1,
    "iupac_name": "ethene",
    "smiles": "C=C",
    "cid": 6325,
    "ic50": 4.262408256530762,
    "category": "Inactive",
    "molecular_formula": "C2H4",
    "molecular_weight": "28.05",
    "synonyms": "ETHYLENE, Ethene, Acetene, Elayl, Olefiant gas, 74-85-1, Athylen, Etileno, Bicarburretted hydrogen, Liquid ethylene, Ethylene, pure, Caswell No. 436, Aethylen, ...",
    "inchi": "InChI=1S/C2H4/c1-2/h1-2H2",
    "inchikey": "VGGSQFUCUMXWEO-UHFFFAOYSA-N",
    "structure_image": "https://pubchem.ncbi.nlm.nih.gov/image/imgsrv.fcgi?cid=6325&t=l",
    "description": "Ethene is an alkene and a gas molecular entity. It has a role as a refrigerant and a plant hormone."
  },
  {
    "id": 2,
    "iupac_name": "ethene",
    "smiles": "C=C",
    "cid": 6325,
    "ic50": 4.262408256530762,
    "category": "Inactive",
    "molecular_formula": "C2H4",
    "molecular_weight": "28.05",
    "synonyms": "ETHYLENE, Ethene, Acetene, Elayl, Olefiant gas, 74-85-1, Athylen, Etileno, Bicarburretted hydrogen, Liquid ethylene, Ethylene, pure, Caswell No. 436, Aethylen, ...",
    "inchi": "InChI=1S/C2H4/c1-2/h1-2H2",
    "inchikey": "VGGSQFUCUMXWEO-UHFFFAOYSA-N",
    "structure_image": "https://pubchem.ncbi.nlm.nih.gov/image/imgsrv.fcgi?cid=6325&t=l",
    "description": "Ethene is an alkene and a gas molecular entity. It has a role as a refrigerant and a plant hormone."
  }
]
```

---

### 6. Get List of User Predictions
**Endpoint:**
```
GET /predictions/
```
**Headers:**
```
Authorization: Bearer your_access_token
```
**Response:**
```json
[
  {
    "id": 1,
    "user": "your_username",
    "model": "model_name",
    "jenis_malaria": "default",
    "created_at": "timestamps"
  },

  {
    "id": 2,
    "user": "your_username",
    "model": "model_name",
    "jenis_malaria": "default",
    "created_at": "timestamps"
  }
]
```

---

### 7. Get Prediction Compounds 
**Endpoint:**
```
GET /predictions/<int:prediction_id>/
```
**Headers:**
```
Authorization: Bearer your_access_token
```
**Response:**
```json
[
  {
    "id": 1,
    "iupac_name": "ethene",
    "smiles": "C=C",
    "cid": 6325,
    "ic50": 4.262408256530762,
    "category": "Inactive",
    "molecular_formula": "C2H4",
    "molecular_weight": "28.05",
    "synonyms": "ETHYLENE, Ethene, Acetene, Elayl, Olefiant gas, 74-85-1, Athylen, Etileno, Bicarburretted hydrogen, Liquid ethylene, Ethylene, pure, Caswell No. 436, Aethylen, ...",
    "inchi": "InChI=1S/C2H4/c1-2/h1-2H2",
    "inchikey": "VGGSQFUCUMXWEO-UHFFFAOYSA-N",
    "structure_image": "https://pubchem.ncbi.nlm.nih.gov/image/imgsrv.fcgi?cid=6325&t=l",
    "description": "Ethene is an alkene and a gas molecular entity. It has a role as a refrigerant and a plant hormone."
  },
  {
    "id": 2,
    "iupac_name": "ethene",
    "smiles": "C=C",
    "cid": 6325,
    "ic50": 4.262408256530762,
    "category": "Inactive",
    "molecular_formula": "C2H4",
    "molecular_weight": "28.05",
    "synonyms": "ETHYLENE, Ethene, Acetene, Elayl, Olefiant gas, 74-85-1, Athylen, Etileno, Bicarburretted hydrogen, Liquid ethylene, Ethylene, pure, Caswell No. 436, Aethylen, ...",
    "inchi": "InChI=1S/C2H4/c1-2/h1-2H2",
    "inchikey": "VGGSQFUCUMXWEO-UHFFFAOYSA-N",
    "structure_image": "https://pubchem.ncbi.nlm.nih.gov/image/imgsrv.fcgi?cid=6325&t=l",
    "description": "Ethene is an alkene and a gas molecular entity. It has a role as a refrigerant and a plant hormone."
  }
]
```

---

### 8. Get Compound Details
**Endpoint:**
```
GET /compounds/<int:compound_id>/
```
**Headers:**
```
Authorization: Bearer your_access_token
```
**Response:**
```json
{
  "id": 1,
  "iupac_name": "ethene",
  "smiles": "C=C",
  "cid": 6325,
  "ic50": 4.262408256530762,
  "category": "Inactive",
  "molecular_formula": "C2H4",
  "molecular_weight": "28.05",
  "synonyms": "ETHYLENE, Ethene, Acetene, Elayl, Olefiant gas, 74-85-1, Athylen, Etileno, Bicarburretted hydrogen, Liquid ethylene, Ethylene, pure, Caswell No. 436, Aethylen, ...",
  "inchi": "InChI=1S/C2H4/c1-2/h1-2H2",
  "inchikey": "VGGSQFUCUMXWEO-UHFFFAOYSA-N",
  "structure_image": "https://pubchem.ncbi.nlm.nih.gov/image/imgsrv.fcgi?cid=6325&t=l",
  "description": "Ethene is an alkene and a gas molecular entity. It has a role as a refrigerant and a plant hormone.",
  "prediction": 1
}
```

### 9. Get Delete Prediction
**Endpoint:**
```
DELETE /predictions/<int:prediction_id>/delete
```
**Headers:**
```
Authorization: Bearer your_access_token
```

### 10. Get Delete Compound
**Endpoint:**
```
DELETE /compounds/<int:compound_id>/delete
```
**Headers:**
```
Authorization: Bearer your_access_token
```

---

### 11. Predict IC50 for a Compound

**🔹 ECFP Models**
- **Deep Learning, ECFP**  
  `model_ECFP_DL.h5` → `model_descriptor = ecfp`, `model_method = dl`  
- **Random Forest, ECFP**  
  `rf_model_ecfp.pkl` → `model_descriptor = ecfp`, `model_method = rf`  
- **XGBoost, ECFP**  
  `xgb_model_ecfp.json` → `model_descriptor = ecfp`, `model_method = xgb`  

**🔹 MACCS Models**
- **Deep Learning, MACCS**  
  `model_MACCS_DL.h5` → `model_descriptor = maccs`, `model_method = dl`  
- **Random Forest, MACCS**  
  `rf_model_maccs.pkl` → `model_descriptor = maccs`, `model_method = rf`  
- **XGBoost, MACCS**  
  `xgb_model_maccs.json` → `model_descriptor = maccs`, `model_method = xgb`  

**🔹 PubchemFP Models**
- **Deep Learning, Mordred**
  `model_PubchemFp_DL.h5` → `model_descriptor = pubchemfp`, `model_method = dl`  
- **Random Forest, Mordred**  
  `rf_model_pubchemfp.pkl` → `model_descriptor = pubchemfp`, `model_method = rf`  
- **XGBoost, Mordred**  
  `xgb_model_pubchemfp.json` → `model_descriptor = pubchemfp`, `model_method = xgb` 

**Endpoint:**
```
POST /predict/
```
**Headers:**
```
Authorization: Bearer your_access_token
```
**Request Body:**
```json
{
  "smiles": "C=C, CHO, H2O, ..",
  "model_descriptor": "model_descriptor",
  "model_method": "model_method"
}
OR
{
  "file": ".csv/.json",
  "model_descriptor": "model_descriptor",
  "model_method": "model_method"
}
```
**Response:**
```json
[
  {
    "id": 1,
    "iupac_name": "ethene",
    "smiles": "C=C",
    "cid": 6325,
    "ic50": 4.262408256530762,
    "category": "Inactive",
    "molecular_formula": "C2H4",
    "molecular_weight": "28.05",
    "synonyms": "ETHYLENE, Ethene, Acetene, Elayl, Olefiant gas, 74-85-1, Athylen, Etileno, Bicarburretted hydrogen, Liquid ethylene, Ethylene, pure, Caswell No. 436, Aethylen, ...",
    "inchi": "InChI=1S/C2H4/c1-2/h1-2H2",
    "inchikey": "VGGSQFUCUMXWEO-UHFFFAOYSA-N",
    "structure_image": "https://pubchem.ncbi.nlm.nih.gov/image/imgsrv.fcgi?cid=6325&t=l",
    "description": "Ethene is an alkene and a gas molecular entity. It has a role as a refrigerant and a plant hormone."
  },
  {
    "id": 1,
    "iupac_name": "ethene",
    "smiles": "C=C",
    "cid": 6325,
    "ic50": 4.262408256530762,
    "category": "Inactive",
    "molecular_formula": "C2H4",
    "molecular_weight": "28.05",
    "synonyms": "ETHYLENE, Ethene, Acetene, Elayl, Olefiant gas, 74-85-1, Athylen, Etileno, Bicarburretted hydrogen, Liquid ethylene, Ethylene, pure, Caswell No. 436, Aethylen, ...",
    "inchi": "InChI=1S/C2H4/c1-2/h1-2H2",
    "inchikey": "VGGSQFUCUMXWEO-UHFFFAOYSA-N",
    "structure_image": "https://pubchem.ncbi.nlm.nih.gov/image/imgsrv.fcgi?cid=6325&t=l",
    "description": "Ethene is an alkene and a gas molecular entity. It has a role as a refrigerant and a plant hormone."
  },
]
```