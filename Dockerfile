# # Use an official Python runtime as a parent image
# FROM python:3.10

# # Set the working directory in the container
# WORKDIR /app

# # Install dependencies
# COPY requirements.txt /app/
# RUN pip install --no-cache-dir -r requirements.txt

# # Copy the current directory contents into the container at /app
# COPY . /app/

# # Expose the port the app will run on
# EXPOSE 8000

# # Set environment variables (if you have any)
# ENV PYTHONUNBUFFERED 1

# # Copy the creds.json into the container
# # COPY creds.json /secrets/creds.json

# # Run the application
# CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "1", "antimalaria_backend.wsgi:application"]



# Use an official Python runtime as a parent image
FROM python:3.10

# Install required system dependencies (including curl)
RUN apt-get update && apt-get install -y curl

# Set the working directory in the container
WORKDIR /app

# Copy project files
COPY . /app/

# Create the directory for ML models
RUN mkdir -p /app/ml_models

# Download ML Models from Google Drive
RUN curl -L "https://drive.google.com/file/d/1EPUuv43bMj2_vTEHGiL1H7sI4wDxYVeP/view?usp=drive_link" -o /app/ml_models/model_ECFP_DL.h5 && \
    curl -L "https://drive.google.com/file/d/1CrW2-Nj7m8ft8vc29u_qXOYd-zqs6x8A/view?usp=drive_link" -o /app/ml_models/rf_model_ecfp.pkl && \
    curl -L "https://drive.google.com/file/d/1a7z6dwKpvjOnK_u8mX1Lb9QVeLQZLmt7/view?usp=drive_link" -o /app/ml_models/xgb_model_ecfp.json

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port the app will run on
EXPOSE 8000

# Run the application
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "1", "antimalaria_backend.wsgi:application"]
