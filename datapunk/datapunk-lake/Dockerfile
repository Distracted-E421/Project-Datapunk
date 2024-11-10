FROM postgres:16 AS datapunk-lake-builder

# Install build dependencies and TimescaleDB repo
RUN apt-get update \
    && apt-get install -y \
        build-essential \
        git \
        postgresql-server-dev-16 \
        postgresql-contrib-16 \
        libpq-dev \
        pkg-config \
        postgresql-16-postgis-3 \
        postgresql-16-postgis-3-scripts \
        postgresql-16-cron \
        wget \
        lsb-release \
        gnupg \
    && wget --quiet -O - https://packagecloud.io/timescale/timescaledb/gpgkey | apt-key add - \
    && echo "deb https://packagecloud.io/timescale/timescaledb/debian/ $(lsb_release -c -s) main" > /etc/apt/sources.list.d/timescaledb.list \
    && apt-get update \
    && apt-get install -y timescaledb-2-postgresql-16 \
    && rm -rf /var/lib/apt/lists/*

# Set PostgreSQL version for builds
ENV PG_MAJOR=16
ENV PATH="/usr/lib/postgresql/${PG_MAJOR}/bin:${PATH}"
ENV PKG_CONFIG_PATH="/usr/lib/postgresql/${PG_MAJOR}/lib/pkgconfig:${PKG_CONFIG_PATH}"

# Build pgvector
WORKDIR /tmp
RUN git clone --branch v0.5.1 https://github.com/pgvector/pgvector.git \
    && cd pgvector \
    && make clean \
    && make USE_PGXS=1 \
    && make install

# Build pg_partman
RUN git clone https://github.com/pgpartman/pg_partman.git \
    && cd pg_partman \
    && make USE_PGXS=1 \
    && make install

FROM postgres:16 AS datapunk-lake

# Copy built extensions from build stage
COPY --from=datapunk-lake-builder /usr/share/postgresql/16/extension/ /usr/share/postgresql/16/extension/
COPY --from=datapunk-lake-builder /usr/lib/postgresql/16/lib/ /usr/lib/postgresql/16/lib/

# Install runtime dependencies including TimescaleDB
RUN apt-get update \
    && apt-get install -y \
        postgresql-contrib \
        postgresql-16-postgis-3 \
        postgresql-16-postgis-3-scripts \
        postgresql-16-cron \
        wget \
        lsb-release \
        gnupg \
    && wget --quiet -O - https://packagecloud.io/timescale/timescaledb/gpgkey | apt-key add - \
    && echo "deb https://packagecloud.io/timescale/timescaledb/debian/ $(lsb_release -c -s) main" > /etc/apt/sources.list.d/timescaledb.list \
    && apt-get update \
    && apt-get install -y timescaledb-2-postgresql-16 \
    && rm -rf /var/lib/apt/lists/*

# Copy configuration files
COPY ./config/postgresql.conf /etc/postgresql/postgresql.conf
COPY ./config/init-extensions.sql /docker-entrypoint-initdb.d/

ENV POSTGRES_USER=datapunk \
    POSTGRES_PASSWORD=changeme \
    POSTGRES_DB=datapunk

EXPOSE 5432

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD pg_isready -U datapunk -d datapunk && psql -U datapunk -d datapunk -c "SELECT * FROM pg_extension WHERE extname = 'vector';" || exit 1

CMD ["postgres", "-c", "config_file=/etc/postgresql/postgresql.conf"]