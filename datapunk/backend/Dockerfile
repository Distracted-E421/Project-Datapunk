# =================================================================
# BASE IMAGE SELECTION
# =================================================================
# Using python:3.11-slim as base image for:
# - Minimal footprint while maintaining essential functionality
# - Official Python support and security updates
# - Slim variant excludes unnecessary packages
# 
# Consider upgrading to 3.12 for:
# - Improved performance
# - Latest security patches
# - New language features
# =================================================================
FROM python:3.11-slim

# =================================================================
# SYSTEM DEPENDENCIES
# =================================================================
# Installing minimal required system packages:
# - gcc: Required for compiling Python C extensions
# - python3-dev: Provides Python header files for building packages
# - libpq-dev: PostgreSQL client library for psycopg2
#
# Best practices implemented:
# - Combined RUN commands to reduce layers
# - Cleanup after installation to reduce image size
# - No-install-recommends to minimize unnecessary packages
# =================================================================
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    libpq-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# =================================================================
# WORKING DIRECTORY
# =================================================================
# Set /app as working directory for:
# - Consistent file locations
# - Isolation from system directories
# - Clear separation of application code
# =================================================================
WORKDIR /app

# =================================================================
# DEPENDENCY MANAGEMENT
# =================================================================
# Copy requirements first to leverage Docker cache
# This layer will only rebuild if requirements.txt changes
#
# TODO: Consider implementing:
# - Multi-stage builds for development vs production
# - Poetry or Pipenv for better dependency management
# - Requirements splitting (base.txt, dev.txt, prod.txt)
# =================================================================
COPY requirements.txt .

# =================================================================
# PYTHON PACKAGE INSTALLATION
# =================================================================
# Install Cython first as it's required by some dependencies
# Using --no-cache-dir to keep container size minimal
#
# Best practices:
# - Separate Cython installation for better dependency resolution
# - Installing wheel and setuptools for better package compatibility
# - Using pip's no-cache option to reduce image size
# =================================================================
RUN pip install --no-cache-dir Cython wheel setuptools

# =================================================================
# APPLICATION DEPENDENCIES
# =================================================================
# Install all required packages from requirements.txt
# Using --no-cache-dir to minimize image size
#
# TODO: Consider:
# - Adding pip-tools for dependency management
# - Implementing

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]