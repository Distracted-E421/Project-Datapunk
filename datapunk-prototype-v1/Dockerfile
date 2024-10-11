# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Add a non-root user
RUN useradd -m e421

# Copy requirements and install
COPY requirements.txt /app
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code into the container
COPY . /app

# Set the user to use when running the container
USER e421
# Define environment variables
ENV PYTHONUNBUFFERED 1

# Set the default command to run
CMD rm -rf /app/data/* && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
