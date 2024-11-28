# Docker Environment Diagnostic Script
# Provides comprehensive monitoring of Docker environment state
# See: sys-arch.mmd Infrastructure->Docker->Monitoring

# NOTE: Requires active Docker daemon and compose setup
# TODO: Add container health status checks
# TODO: Add resource utilization metrics
# FIXME: Implement network connectivity validation
# TODO: Add volume usage statistics

# Display active and stopped containers for environment verification
# NOTE: Critical for service mesh debugging
Write-Host "=== Docker Container Status ==="
docker ps -a

# Check network configuration for service mesh connectivity
# NOTE: Required for inter-service communication
Write-Host "`n=== Docker Networks ==="
docker network ls

# Verify volume state for data persistence
# NOTE: Important for PostgreSQL and Redis storage
Write-Host "`n=== Docker Volumes ==="
docker volume ls

# Monitor Lake service logs for operational issues
# TODO: Add pattern matching for critical errors
Write-Host "`n=== Service Logs ==="
docker-compose logs datapunk-lake