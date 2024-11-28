# PostgreSQL Debugging Script
# Provides comprehensive diagnostics for PostgreSQL container
# See: sys-arch.mmd Infrastructure->StorageLayer->PG

# NOTE: Requires active PostgreSQL container named 'datapunk_lake'
# TODO: Add error handling for container not running
# TODO: Add configuration validation checks
# FIXME: Implement log rotation handling
# TODO: Add metrics collection for monitoring integration

# Display container logs for operational issues
Write-Host "=== PostgreSQL Container Logs ==="
docker logs datapunk_lake

# Verify current PostgreSQL configuration
# NOTE: Critical for performance debugging
Write-Host "`n=== PostgreSQL Configuration ==="
docker exec datapunk_lake cat /etc/postgresql/postgresql.conf

# List installed extensions for feature verification
# NOTE: Required for vector store and time series functionality
Write-Host "`n=== Installed Extensions ==="
docker exec datapunk_lake psql -U datapunk -d datapunk -c "\dx"

# Check recent error logs for troubleshooting
# TODO: Add pattern matching for critical errors
Write-Host "`n=== PostgreSQL Error Log ==="
docker exec datapunk_lake Get-Content /var/log/postgresql/postgresql-*.log -Tail 50