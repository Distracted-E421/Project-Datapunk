FROM postgres:latest

# Install PostGIS and other required extensions
RUN apt-get update && \
    apt-get install -y postgis postgresql-postgis-scripts && \
    apt-get clean

# Copy initialization scripts
COPY init.sql /docker-entrypoint-initdb.d/

# Create directory for PostgreSQL configuration
RUN mkdir -p /etc/postgresql && \
    chown -R postgres:postgres /etc/postgresql

# Set proper permissions
RUN chmod -R 750 /var/lib/postgresql/data

# Expose PostgreSQL default port
EXPOSE 5432