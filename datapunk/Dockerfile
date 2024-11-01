# =====================================================================
# Multi-stage build configuration
# This approach allows us to create a minimal final image by copying only
# necessary artifacts from intermediate build stages, significantly
# reducing the final image size and potential security vulnerabilities
# =====================================================================

# =====================================================================
# Database Stage
# Creates a PostgreSQL instance with PostGIS extensions for spatial data
# We use postgres:latest as the base to ensure we have the most recent
# stable version with security updates
# =====================================================================
FROM postgres:latest as db
RUN apt-get update && \
    apt-get install -y postgis postgresql-postgis-scripts && \
    apt-get clean

# =====================================================================
# Backend Stage
# Sets up the Python environment and installs dependencies
# We use python:3.12-slim to minimize image size while maintaining
# necessary Python functionality
# =====================================================================
FROM python:3.12-slim as backend
WORKDIR /app/backend

# Install system dependencies required for Python packages
# gcc: Required for compiling Python packages
# python3-dev: Provides Python header files
# libpq-dev: Required for psycopg2 (PostgreSQL adapter for Python)
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ .

# =====================================================================
# Frontend Stage
# Builds the Node.js application and creates production assets
# Uses node:20-alpine for a minimal footprint during build
# =====================================================================
FROM node:20-alpine as frontend
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ .
RUN npm run build

# =====================================================================
# Final Stage
# Combines all components into a single, production-ready image
# Uses debian:latest as base for compatibility and stability
# =====================================================================
FROM debian:latest    

# Install runtime dependencies
# postgresql: Required for database client tools
# python3: Runs the backend application
# python3-pip: Manages Python packages
# nginx: Serves the frontend assets and handles reverse proxy
RUN apt-get update && apt-get install -y \
    postgresql \
    python3 \
    python3-pip \
    nginx \
    && rm -rf /var/lib/apt/lists/*

# =====================================================================
# Artifact Collection
# Copy necessary files from previous build stages
# This ensures we only include what's needed for production
# =====================================================================
# Copy PostgreSQL libraries from db stage
COPY --from=db /usr/lib/postgresql/ /usr/lib/postgresql/
# Copy Python packages from backend stage
COPY --from=backend /usr/local/lib/python3.12/site-packages/ /usr/local/lib/python3.12/site-packages/
COPY --from=backend /usr/local/bin/ /usr/local/bin/
COPY --from=backend /app/backend /app/backend
# Copy built frontend assets
COPY --from=frontend /app/frontend/dist /app/frontend/dist

# =====================================================================
# Final Configuration
# Set up entry point and expose necessary ports
# =====================================================================
# Copy and configure startup script
COPY docker-entrypoint.sh /
RUN chmod +x /docker-entrypoint.sh

# Expose required ports
# 5432: PostgreSQL
# 8000: Backend API
# 80: Frontend/Nginx
EXPOSE 5432 8000 80

# Configure container startup
ENTRYPOINT ["/docker-entrypoint.sh"]
