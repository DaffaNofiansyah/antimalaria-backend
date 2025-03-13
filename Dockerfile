# Use an official Python runtime as a parent image
FROM python:3.10

# Set the working directory in the container
WORKDIR /app

# Install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . /app/

# Expose the port the app will run on
EXPOSE 8000

# Set environment variables (if you have any)
ENV PYTHONUNBUFFERED 1

# Copy the creds.json into the container
# COPY creds.json /secrets/creds.json

# Run the application
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "1", "antimalaria_backend.wsgi:application"]
