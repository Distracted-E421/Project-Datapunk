# Common configuration anchors


x-healthcheck-defaults: &healthcheck-defaults
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s

services:
  cortex:
    build:
      context: ./datapunk-cortex
      dockerfile: Dockerfile
    image: datapunk/cortex:latest
    container_name: datapunk_cortex
    environment:
      <<: *common-variables
      REDIS_HOST: redis
      MINIO_HOST: minio
      MODEL_CACHE_SIZE: 2GB
      MAX_BATCH_SIZE: 32
    volumes:
      - cortex_models:/models
      - cortex_cache:/cache
      - cortex_logs:/var/log/datapunk/cortex
    ports:
      - "8001:8001"
    networks:
      - datapunk_network
    depends_on:
      db:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
      
  redis:
    image: redis:7-alpine
    container_name: datapunk_redis
    ports:
      - "6379:6379"
    networks:
      - datapunk_network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 3

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    image: datapunk/frontend:latest
    container_name: datapunk_frontend
    environment:
      - NODE_ENV=development
      - VITE_API_URL=http://backend:8000
      - VITE_CORTEX_URL=http://cortex:8001
    ports:
      - "3000:3000"
    volumes:
      - ./frontend:/app
      - /app/node_modules
    networks:
      - datapunk_network
    depends_on:
      - cortex
    healthcheck:
      <<: *healthcheck-defaults
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G

  datapunk-stream:
    image: datapunk/stream:latest
    container_name: datapunk_stream
    environment:
      REDIS_URL: ${REDIS_URL}
      POSTGRES_URL: ${POSTGRES_URL}
      API_KEYS: ${API_KEYS}
    volumes:
      - stream_cache:/cache
      - stream_logs:/logs
    ports:
      - "8000:8000"
    networks:
      - datapunk_network
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  datapunk-lake:
    build:
      context: ./datapunk-lake
      dockerfile: Dockerfile
    image: datapunk/lake:latest
    container_name: datapunk_lake
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-datapunk}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-changeme}
      POSTGRES_DB: ${POSTGRES_DB:-datapunk}
      # Core PostgreSQL settings
      POSTGRES_MAX_CONNECTIONS: 200
      POSTGRES_SHARED_BUFFERS: 2GB
      POSTGRES_EFFECTIVE_CACHE_SIZE: 6GB
      POSTGRES_MAINTENANCE_WORK_MEM: 512MB
      POSTGRES_WAL_BUFFERS: 16MB
      POSTGRES_DEFAULT_STATISTICS_TARGET: 100
      POSTGRES_RANDOM_PAGE_COST: 1.1
      POSTGRES_EFFECTIVE_IO_CONCURRENCY: 200
      POSTGRES_WORK_MEM: 16MB
      POSTGRES_MIN_WAL_SIZE: 1GB
      POSTGRES_MAX_WAL_SIZE: 4GB
    volumes:
      - data_volume:/var/lib/postgresql/data
      - import_staging:/data/staging
      - archive:/data/archive
      - lake_logs:/var/log/datapunk/lake
      # Mount config files from local directory
      - ./datapunk-lake/config/postgresql.conf:/etc/postgresql/postgresql.conf:ro
      - ./datapunk-lake/config/init-extensions.sql:/docker-entrypoint-initdb.d/init-extensions.sql:ro
    ports:
      - "5432:5432"
    networks:
      - datapunk_network
    healthcheck:
      <<: *healthcheck-defaults
      test: ["CMD-SHELL", "pg_isready -U postgres"]
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: '8G'
        reservations:
          cpus: '2'
          memory: '4G'
    depends_on:
      redis:
        condition: service_healthy

volumes:
  cortex_models:
  cortex_cache:
  cortex_logs:
  stream_cache:
  stream_logs:
  data_volume:
  import_staging:
  archive:
  lake_logs:

networks:
  datapunk_network:
    driver: bridge









#------------------------------------------------------------------------------
# DATAPUNK POSTGRESQL CONFIGURATION
# Compatible with PostgreSQL 16.x
#------------------------------------------------------------------------------

# Connection Settings
listen_addresses = '*'
max_connections = 200
superuser_reserved_connections = 3

#------------------------------------------------------------------------------
# MEMORY CONFIGURATION
#------------------------------------------------------------------------------
shared_buffers = '4GB'                      # 25% of RAM for dedicated DB server
huge_pages = 'try'                          # Attempt to use huge pages
effective_cache_size = '12GB'               # 75% of RAM for query planning
maintenance_work_mem = '1GB'                # For maintenance operations
work_mem = '64MB'                          # Per-sort operation memory
temp_buffers = '64MB'                      # Per-session temp table memory

#------------------------------------------------------------------------------
# WRITE AHEAD LOG
#------------------------------------------------------------------------------
wal_level = logical                        # Enable logical replication
synchronous_commit = off                   # Improved performance, slight durability trade-off
wal_writer_delay = '200ms'                # WAL write frequency
wal_buffers = '16MB'                      # WAL buffer size
checkpoint_completion_target = 0.9         # Spread checkpoint I/O
min_wal_size = '1GB'
max_wal_size = '4GB'

#------------------------------------------------------------------------------
# QUERY PLANNING
#------------------------------------------------------------------------------
random_page_cost = 1.1                    # Optimized for SSD storage
effective_io_concurrency = 200            # Higher for SSD/NVMe
default_statistics_target = 100           # Balance between planning and quality
constraint_exclusion = partition          # Optimize partitioned queries

#------------------------------------------------------------------------------
# PARALLEL QUERY
#------------------------------------------------------------------------------
max_worker_processes = 8
max_parallel_workers_per_gather = 4
max_parallel_workers = 8
max_parallel_maintenance_workers = 4

#------------------------------------------------------------------------------
# AUTOVACUUM
#------------------------------------------------------------------------------
autovacuum = on
autovacuum_max_workers = 4
autovacuum_naptime = '1min'
autovacuum_vacuum_threshold = 50
autovacuum_analyze_threshold = 50

#------------------------------------------------------------------------------
# EXTENSIONS AND PRELOADED LIBRARIES
#------------------------------------------------------------------------------
shared_preload_libraries = 'pg_stat_statements,pg_stat_monitor,pg_cron,pg_prewarm,pg_stat_kcache,pg_trgm,pgvector,timescaledb,pg_memcache,pg_tle,pgsodium,auto_explain,pg_partman,pg_qualstats,pg_prometheus'

# Extension-specific settings
pg_stat_statements.max = 10000
pg_stat_statements.track = all

# Auto explain for query analysis
auto_explain.log_min_duration = '3s'
auto_explain.log_analyze = on
auto_explain.log_buffers = on
auto_explain.log_timing = on
auto_explain.log_nested_statements = on

# Memory cache settings
memcache.default_lifetime = '1 hour'
memcache.number_of_pools = 4

# Partition management
partman.retention = '3 months'
partman.retention_keep_table = true
partman.retention_keep_index = true

# Query statistics
pg_qualstats.enabled = true
pg_qualstats.track_constants = on
pg_qualstats.max = 10000

# Prometheus metrics
prometheus.listen_address = '0.0.0.0:9187'
prometheus.retention_days = 7





FROM postgres:16

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    postgresql-server-dev-16 \
    libpq-dev \
    python3-dev \
    python3-pip \
    # Required extensions
    postgresql-16-postgis \
    postgresql-16-postgis-scripts \
    postgresql-16-cron \
    postgresql-16-partman \
    postgresql-16-hstore \
    # Additional dependencies
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install pgvector
RUN git clone --branch v0.5.1 https://github.com/pgvector/pgvector.git && \
    cd pgvector && \
    make && \
    make install

# Install TimescaleDB
RUN curl -s https://packagecloud.io/install/repositories/timescale/timescaledb/script.deb.sh | bash && \
    apt-get update && \
    apt-get install -y timescaledb-postgresql-16 && \
    rm -rf /var/lib/apt/lists/*

# Default command
CMD ["postgres", "-c", "config_file=/etc/postgresql/postgresql.conf"]





-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pgvector;
CREATE EXTENSION IF NOT EXISTS timescaledb;
CREATE EXTENSION IF NOT EXISTS pg_cron;
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
CREATE EXTENSION IF NOT EXISTS pg_partman;
CREATE EXTENSION IF NOT EXISTS hstore;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Create core schemas
CREATE SCHEMA IF NOT EXISTS user_data;
CREATE SCHEMA IF NOT EXISTS imports;
CREATE SCHEMA IF NOT EXISTS analytics;
CREATE SCHEMA IF NOT EXISTS vectors;
CREATE SCHEMA IF NOT EXISTS timeseries;
CREATE SCHEMA IF NOT EXISTS archive; 