FROM postgres:16

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    postgresql-server-dev-16 \
    libpq-dev \
    postgresql-contrib \
    && rm -rf /var/lib/apt/lists/*

# Install pgvector with correct include paths
RUN git clone --branch v0.5.1 https://github.com/pgvector/pgvector.git \
    && cd pgvector \
    && PG_CONFIG=/usr/lib/postgresql/16/bin/pg_config make \
    && PG_CONFIG=/usr/lib/postgresql/16/bin/pg_config make install

# Set environment variables
ENV PATH=$PATH:/usr/lib/postgresql/16/bin

# Update shared preload libraries
RUN echo "shared_preload_libraries = 'pg_stat_statements,pgvector'" >> /usr/share/postgresql/postgresql.conf.sample

EXPOSE 5432

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD pg_isready -U datapunk -d datapunk || exit 1