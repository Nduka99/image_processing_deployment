# Use an official Python runtime as a parent image
# python:3.11-slim represents a very lightweight base image ideal for AWS Free Tier
FROM python:3.11-slim

# Set environment variables
# Prevents Python from writing pyc files to disc
ENV PYTHONDONTWRITEBYTECODE 1
# Prevents Python from buffering stdout and stderr
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Copy the dependencies file to the working directory
COPY requirements.txt .

# Install any dependencies
# Using --no-cache-dir to keep the image size small
RUN pip install --no-cache-dir -r requirements.txt

# Copy the API, Model, and Frontend directories into the container
COPY ./api /app/api
COPY ./model /app/model
COPY ./frontend /app/frontend

# Expose the port the app runs on
EXPOSE 8000

# Command to run the FastApi application
# Using uvicorn as the ASGI server
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
