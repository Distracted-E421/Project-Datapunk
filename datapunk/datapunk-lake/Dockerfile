FROM postgres:16

# Add PostgreSQL's repository key and repository
RUN apt-get update \
    && apt-get install -y curl ca-certificates gnupg \
    && curl https://www.postgresql.org/media/keys/ACCC4CF8.asc | gpg --dearmor | tee /etc/apt/trusted.gpg.d/apt.postgresql.org.gpg >/dev/null \
    && echo "deb http://apt.postgresql.org/pub/repos/apt/ bookworm-pgdg main" > /etc/apt/sources.list.d/pgdg.list

# Install build dependencies and extensions
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    postgresql-server-dev-16 \
    libpq-dev \
    postgresql-16-postgis-3 \
    postgresql-16-postgis-3-scripts \
    postgresql-16-cron \
    postgresql-16-partman \
    postgresql-contrib \
    && rm -rf /var/lib/apt/lists/*

# Install pgvector with correct include paths
RUN git clone --branch v0.5.1 https://github.com/pgvector/pgvector.git \
    && cd pgvector \
    && PG_CONFIG=/usr/lib/postgresql/16/bin/pg_config make \
    && PG_CONFIG=/usr/lib/postgresql/16/bin/pg_config make install

# Install TimescaleDB
RUN echo "deb https://packagecloud.io/timescale/timescaledb/debian/ bookworm main" > /etc/apt/sources.list.d/timescaledb.list \
    && curl -L https://packagecloud.io/timescale/timescaledb/gpgkey | apt-key add - \
    && apt-get update \
    && apt-get install -y timescaledb-2-postgresql-16 \
    && rm -rf /var/lib/apt/lists/*

# Copy configuration files
COPY config/postgresql.conf /etc/postgresql/postgresql.conf
COPY config/init-extensions.sql /docker-entrypoint-initdb.d/

# Set environment variables (referencing README.md lines 242-264)
ENV POSTGRES_USER=datapunk \
    POSTGRES_PASSWORD=changeme \
    POSTGRES_DB=datapunk \
    POSTGRES_INITDB_ARGS="--data-checksums" \
    PATH=$PATH:/usr/lib/postgresql/16/bin

# Update shared preload libraries
RUN echo "shared_preload_libraries = 'pg_stat_statements,pg_stat_monitor,pg_cron,timescaledb,pgvector'" >> /usr/share/postgresql/postgresql.conf.sample

EXPOSE 5432

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD pg_isready -U datapunk -d datapunk || exit 1

CMD ["postgres", "-c", "config_file=/etc/postgresql/postgresql.conf"]