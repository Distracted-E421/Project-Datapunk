# Build Stage
FROM postgres:16 AS datapunk-lake-builder

# Version control with defaults
ARG PG_MAJOR=16
ARG PGVECTOR_VERSION=0.5.1
ARG TIMESCALEDB_VERSION=2
ARG POSTGIS_VERSION=3

# Validate required build arguments
RUN if [ -z "$PG_MAJOR" ]; then echo "PG_MAJOR is required" && exit 1; fi && \
    if [ -z "$PGVECTOR_VERSION" ]; then echo "PGVECTOR_VERSION is required" && exit 1; fi && \
    if [ -z "$TIMESCALEDB_VERSION" ]; then echo "TIMESCALEDB_VERSION is required" && exit 1; fi && \
    if [ -z "$POSTGIS_VERSION" ]; then echo "POSTGIS_VERSION is required" && exit 1; fi

# Set PostgreSQL version for builds
ENV PG_MAJOR=${PG_MAJOR}
ENV PATH="/usr/lib/postgresql/${PG_MAJOR}/bin:${PATH}"
ENV PKG_CONFIG_PATH="/usr/lib/postgresql/${PG_MAJOR}/lib/pkgconfig:${PKG_CONFIG_PATH}"

# Install build dependencies in a single layer
RUN apt-get update \
    && apt-get install -y \
        build-essential \
        git \
        postgresql-server-dev-${PG_MAJOR} \
        postgresql-contrib-${PG_MAJOR} \
        postgresql-${PG_MAJOR}-postgis-${POSTGIS_VERSION} \
        postgresql-${PG_MAJOR}-postgis-${POSTGIS_VERSION}-scripts \
        postgresql-${PG_MAJOR}-cron \
        libpq-dev \
        pkg-config \
        wget \
        lsb-release \
        gnupg \
    && wget --quiet -O - https://packagecloud.io/timescale/timescaledb/gpgkey | apt-key add - \
    && echo "deb https://packagecloud.io/timescale/timescaledb/debian/ $(lsb_release -c -s) main" > /etc/apt/sources.list.d/timescaledb.list \
    && apt-get update \
    && apt-get install -y timescaledb-${TIMESCALEDB_VERSION}-postgresql-${PG_MAJOR}

# Build extensions in separate layers for better caching
WORKDIR /tmp/build

# Build pgvector
RUN git clone --branch v${PGVECTOR_VERSION} https://github.com/pgvector/pgvector.git \
    && cd pgvector \
    && make clean \
    && make USE_PGXS=1 \
    && make install

# Build pg_partman
RUN git clone https://github.com/pgpartman/pg_partman.git \
    && cd pg_partman \
    && make USE_PGXS=1 \
    && make install

# Runtime Stage
FROM postgres:16 AS datapunk-lake

# Copy built extensions
COPY --from=datapunk-lake-builder /usr/share/postgresql/16/extension/ /usr/share/postgresql/16/extension/
COPY --from=datapunk-lake-builder /usr/lib/postgresql/16/lib/ /usr/lib/postgresql/16/lib/

# Install runtime dependencies
RUN apt-get update \
    && apt-get install -y \
        postgresql-contrib \
        postgresql-16-postgis-3 \
        postgresql-16-postgis-3-scripts \
        postgresql-16-cron \
        timescaledb-2-postgresql-16 \
        wget \
        lsb-release \
        gnupg \
    && rm -rf /var/lib/apt/lists/*

# Create required directories with proper permissions
RUN mkdir -p /var/lib/postgresql/data \
    && mkdir -p /var/lib/postgresql/archive \
    && chown -R postgres:postgres /var/lib/postgresql

# Copy configuration files (with explicit paths)
COPY config/postgresql.conf /etc/postgresql/postgresql.conf
COPY config/init.sql /docker-entrypoint-initdb.d/init.sql
COPY scripts/healthcheck.sh /usr/local/bin/healthcheck.sh
RUN chmod +x /usr/local/bin/healthcheck.sh

# Set environment variables from build args
ENV POSTGRES_USER=${POSTGRES_USER:-datapunk} \
    POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-changeme} \
    POSTGRES_DB=${POSTGRES_DB:-datapunk} \
    PGDATA=/var/lib/postgresql/data \
    POSTGRES_INITDB_ARGS="--data-checksums"

# Expose PostgreSQL port
EXPOSE 5432

# Enhanced healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD /usr/local/bin/healthcheck.sh

# Start PostgreSQL with custom configuration
CMD ["postgres", "-c", "config_file=/etc/postgresql/postgresql.conf"]