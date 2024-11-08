FROM postgres:16

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    postgresql-server-dev-16 \
    libpq-dev \
    postgresql-contrib \
    && rm -rf /var/lib/apt/lists/*

# Install pgvector with correct paths and registration
WORKDIR /tmp/pgvector
RUN git clone --branch v0.5.1 https://github.com/pgvector/pgvector.git . && \
    PG_CONFIG=/usr/lib/postgresql/16/bin/pg_config make && \
    PG_CONFIG=/usr/lib/postgresql/16/bin/pg_config make install && \
    mkdir -p /usr/share/postgresql/16/extension && \
    cp vector.control /usr/share/postgresql/16/extension/ && \
    cp sql/vector--*.sql /usr/share/postgresql/16/extension/

# Create extension initialization script
RUN echo "CREATE EXTENSION IF NOT EXISTS pg_stat_statements; CREATE EXTENSION IF NOT EXISTS vector;" > /docker-entrypoint-initdb.d/init-extensions.sql

# Set environment variables
ENV PATH=$PATH:/usr/lib/postgresql/16/bin

# Update shared preload libraries
RUN echo "shared_preload_libraries = 'pg_stat_statements,vector'" >> /usr/share/postgresql/postgresql.conf.sample

EXPOSE 5432

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD pg_isready -U datapunk -d datapunk || exit 1