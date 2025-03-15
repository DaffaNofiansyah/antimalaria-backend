# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Install required system dependencies (including wget and curl)
RUN apt-get update && apt-get install -y wget curl && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy project files
COPY . /app/

# Create the directory for ML models
RUN mkdir -p /app/ml_models

RUN pip install --no-cache-dir -r requirements.txt

# Function to download large Google Drive files
RUN mkdir -p /app/ml_models && \
    gdown --id 1EPUuv43bMj2_vTEHGiL1H7sI4wDxYVeP -O /app/ml_models/model_ECFP_DL.h5 && \
    gdown --id 1CrW2-Nj7m8ft8vc29u_qXOYd-zqs6x8A -O /app/ml_models/rf_model_ecfp.pkl && \
    gdown --id 1a7z6dwKpvjOnK_u8mX1Lb9QVeLQZLmt7 -O /app/ml_models/xgb_model_ecfp.json

# Install dependencies

# Expose the port the app will run on
EXPOSE 8080

# Run the application
# CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "1", "-k", "gevent", "antimalaria_backend.wsgi:application"]
# CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--workers", "2", "--timeout", "120", "--keep-alive", "10", "antimalaria_backend.asgi:application"]
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "--workers", "2", "--timeout", "120", "--keep-alive", "10", "antimalaria_backend.asgi:application", "--lifespan", "on"]