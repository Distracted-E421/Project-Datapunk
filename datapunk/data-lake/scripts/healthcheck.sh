#!/bin/bash
# /scripts/healthcheck.sh

# Check if PostgreSQL is accepting connections
pg_isready -U datapunk -d datapunk || exit 1

# Verify essential extensions
psql -U datapunk -d datapunk -c "SELECT extname, extversion FROM pg_extension WHERE extname IN ('vector', 'postgis', 'timescaledb', 'pg_cron');" || exit 1

# Check disk space
df -h /var/lib/postgresql/data | awk 'NR==2 {if ($5+0 > 90) exit 1}'

# Verify schemas exist
psql -U datapunk -d datapunk -c "SELECT schema_name FROM information_schema.schemata WHERE schema_name IN ('user_data', 'imports');" || exit 1