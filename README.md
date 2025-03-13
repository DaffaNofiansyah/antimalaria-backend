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

- Python 3.8 atau lebih tinggi
- pip (Python package installer)
- PostgreSQL (jika menggunakan PostgreSQL sebagai database)

## Instalasi

Ikuti langkah-langkah berikut untuk meng-clone dan men-setup proyek.

### 1. Clone repository

Clone repository proyek ke mesin lokal Anda menggunakan Git:

```bash
git clone https://github.com/DaffaNofiansyah/Antimalaria-BE.git
cd Antimalaria-BE
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
http://https://malaria-757983837468.asia-east1.run.app/
```

## Authentication
This API uses JWT authentication.
- Obtain tokens via `/login/`
- Refresh tokens via `/refresh-token/`
- Google authentication via `/google-login/`

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

### 4. Google Login
**Endpoint:**
```
POST /google-login/
```
**Request Body:**
```json
{
  "id_token": "your_google_id_token"
}
```
**Response:**
```json
{
  "message": "Login successful",
  "access": "your_access_token",
  "refresh": "your_refresh_token",
  "user": {
    "email": "user@example.com",
    "name": "User Name",
  }
}
```

---

### 5. Get List of Compounds Library
**Endpoint:**
```
GET /compounds/
```
**Response:**
```json
[
  {
    "iupac_name": "Compound Name",
    "smiles": "Compound SMILES",
    "cid": "Compound CID",
    "ic50": "IC50",
    "category": "Compound Category"
  },
  {
    "iupac_name": "Compound Name",
    "smiles": "Compound SMILES",
    "cid": "Compound CID",
    "ic50": "IC50",
    "category": "Compound Category"
  }
]
```

---

### 6. Get List of Predictions
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
    "model_id": 1,
    "jenis_malaria": "default"
  },

  {
    "id": 2,
    "user": "your_username",
    "model_id": 1,
    "jenis_malaria": "default"
  }
]
```

---

### 7. Get Details of a Prediction
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
    "iupac_name": "Compound Name",
    "smiles": "Compound SMILES",
    "cid": "Compound CID",
    "ic50": "IC50",
    "category": "Compound Category"
  },
  {
    "iupac_name": "Compound Name",
    "smiles": "Compound SMILES",
    "cid": "Compound CID",
    "ic50": "IC50",
    "category": "Compound Category"
  }
]
```

---

### 8. Get Compound Details
**Endpoint:**
```
GET /predictions/<int:prediction_id>/compounds/<int:compound_id>/
```
**Headers:**
```
Authorization: Bearer your_access_token
```
**Response:**
```json
{
    "iupac_name": "Compound IUPAC Name",
    "smiles": "SMILES",
    "cid": "Compound CID",
    "ic50": "IC50",
    "category": "Category",
    "molecular_formula": "Compound Molecular Formula",
    "molecular_weight": "Compound Molecular Weight",
    "synonyms": "Compound Synonyms",
    "inchi": "Compound InChI",
    "inchikey": "Compound InChIKey",
    "structure_image": "Compound Structure Image",
    "description": "Compound Description"
}
```

---

### 9. Predict IC50 for a Compound
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
  "smiles": "CCO"
}
```
**Response:**
```json
[
  {
    "iupac_name": "Compound Name",
    "smiles": "CCO",
    "cid": "12345",
    "ic50": 7.5,
    "category": "Moderately Active"
  }
]
```