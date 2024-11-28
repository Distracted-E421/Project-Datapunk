# Lake Service PostgreSQL Debug Script
# Provides comprehensive database diagnostics for the Lake service
# See: sys-arch.mmd CoreServices->LakeService->Storage->PG

# NOTE: This script assumes the Lake container is running
# FIXME: Add error handling for container access failures
# TODO: Add performance metrics collection
# TODO: Add connection pool status
# TODO: Add query performance analysis

Write-Host "=== PostgreSQL Container Logs ==="
docker logs datapunk_lake  # General container health check

Write-Host "`n=== PostgreSQL Configuration ==="
# NOTE: Configuration validation against recommended settings
# TODO: Add configuration diff against baseline
docker exec datapunk_lake cat /etc/postgresql/postgresql.conf

Write-Host "`n=== Installed Extensions ==="
# NOTE: Verifies required extensions (pgvector, TimescaleDB, PostGIS)
# TODO: Add version validation
docker exec datapunk_lake psql -U datapunk -d datapunk -c "\dx"

Write-Host "`n=== PostgreSQL Error Log ==="
# NOTE: Last 50 lines only - increase if debugging specific issues
# TODO: Add log filtering by severity
# TODO: Add log pattern analysis
docker exec datapunk_lake Get-Content /var/log/postgresql/postgresql-*.log -Tail 50

# TODO: Add sections for:
# - Connection pool status
# - Active queries
# - Lock information
# - Table statistics
# - Index health
# - Vacuum status
# - Replication lag