# Use an official Python runtime as a parent image
FROM python:3.10

# Install required system dependencies (including wget and curl)
RUN apt-get update && apt-get install -y wget curl && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy project files
COPY . /app/

# Create the directory for ML models
RUN mkdir -p /app/ml_models

# Function to download large Google Drive files
RUN FILE_ID="1EPUuv43bMj2_vTEHGiL1H7sI4wDxYVeP" && \
    DEST_PATH="/app/ml_models/model_ECFP_DL.h5" && \
    CONFIRM=$(wget --quiet --save-cookies /tmp/cookies.txt --keep-session-cookies \ 
        "https://drive.google.com/uc?export=download&id=${FILE_ID}" -O- | \ 
        sed -rn 's/.*confirm=([0-9A-Za-z_]+).*/\1/p') && \ 
    wget --load-cookies /tmp/cookies.txt \ 
        "https://drive.google.com/uc?export=download&confirm=${CONFIRM}&id=${FILE_ID}" \ 
        -O "${DEST_PATH}" && \ 
    rm -rf /tmp/cookies.txt && \
    FILE_ID="1CrW2-Nj7m8ft8vc29u_qXOYd-zqs6x8A" && \
    DEST_PATH="/app/ml_models/rf_model_ecfp.pkl" && \
    CONFIRM=$(wget --quiet --save-cookies /tmp/cookies.txt --keep-session-cookies \ 
        "https://drive.google.com/uc?export=download&id=${FILE_ID}" -O- | \ 
        sed -rn 's/.*confirm=([0-9A-Za-z_]+).*/\1/p') && \ 
    wget --load-cookies /tmp/cookies.txt \ 
        "https://drive.google.com/uc?export=download&confirm=${CONFIRM}&id=${FILE_ID}" \ 
        -O "${DEST_PATH}" && \ 
    rm -rf /tmp/cookies.txt && \
    FILE_ID="1a7z6dwKpvjOnK_u8mX1Lb9QVeLQZLmt7" && \
    DEST_PATH="/app/ml_models/xgb_model_ecfp.json" && \
    CONFIRM=$(wget --quiet --save-cookies /tmp/cookies.txt --keep-session-cookies \ 
        "https://drive.google.com/uc?export=download&id=${FILE_ID}" -O- | \ 
        sed -rn 's/.*confirm=([0-9A-Za-z_]+).*/\1/p') && \ 
    wget --load-cookies /tmp/cookies.txt \ 
        "https://drive.google.com/uc?export=download&confirm=${CONFIRM}&id=${FILE_ID}" \ 
        -O "${DEST_PATH}" && \ 
    rm -rf /tmp/cookies.txt

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port the app will run on
EXPOSE 8000

# Run the application
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "1", "-k", "gevent", "antimalaria_backend.wsgi:application"]
