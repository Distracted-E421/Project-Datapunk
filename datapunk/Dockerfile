# Multi-stage build for optimized images

# Database stage
FROM postgres:latest as db
RUN apt-get update && \
    apt-get install -y postgis postgresql-postgis-scripts && \
    apt-get clean

# Backend stage
FROM python:3.12-slim as backend
WORKDIR /app/backend

# Install PostgreSQL development files needed for psycopg2
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ .

# Frontend stage
FROM node:20-alpine as frontend
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ .
RUN npm run build

# Final stage
FROM debian:latest    
# Install necessary runtime dependencies
RUN apt-get update && apt-get install -y \
    postgresql \
    python3 \
    python3-pip \
    nginx \
    && rm -rf /var/lib/apt/lists/*

# Copy artifacts from previous stages
COPY --from=db /usr/lib/postgresql/ /usr/lib/postgresql/
COPY --from=backend /usr/local/lib/python3.12/site-packages/ /usr/local/lib/python3.12/site-packages/
COPY --from=backend /usr/local/bin/ /usr/local/bin/
COPY --from=backend /app/backend /app/backend
COPY --from=frontend /app/frontend/dist /app/frontend/dist

# Copy configuration files
COPY docker-entrypoint.sh /
RUN chmod +x /docker-entrypoint.sh

# Expose ports
EXPOSE 5432 8000 80

# Set entrypoint
ENTRYPOINT ["/docker-entrypoint.sh"]
