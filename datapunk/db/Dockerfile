FROM postgres:latest

# /*
# Install PostGIS, pgvector, and other required extensions:
# - Update the package list
# - Install the required packages: postgis, postgresql-postgis-scripts, build-essential, git, postgresql-server-dev-all
# - Change directory to /tmp
# - Clone the pgvector repository
# - Change directory to pgvector
# - Build and install pgvector
# - Copy pgvector control file to PostgreSQL extension directory
# - Copy pgvector SQL files to PostgreSQL extension directory
# - Remove unnecessary packages
# - Remove automatically installed packages that are no longer needed
# - Clean up the package cache
# - Remove temporary files and package lists
# */

RUN apt-get update && \
    apt-get install -y \
    postgis \
    postgresql-postgis-scripts \
    build-essential \
    git \
    postgresql-server-dev-all && \
    cd /tmp && \
    git clone --branch v0.5.1 https://github.com/pgvector/pgvector.git && \
    cd pgvector && \
    make && \
    make install && \
    cp /tmp/pgvector/pgvector.control /usr/share/postgresql/17/extension/ && \
    cp /tmp/pgvector/sql/vector--*.sql /usr/share/postgresql/17/extension/ && \
    apt-get remove -y build-essential git postgresql-server-dev-all && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/pgvector

# Copy initialization scripts
COPY init.sql /docker-entrypoint-initdb.d/

# Create directory for PostgreSQL configuration
RUN mkdir -p /etc/postgresql && \
    chown -R postgres:postgres /etc/postgresql

# Set proper permissions
RUN chmod -R 750 /var/lib/postgresql/data

# Expose PostgreSQL default port
EXPOSE 5432