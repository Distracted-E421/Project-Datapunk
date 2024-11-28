# Lake Service Docker Debug Script
# Provides comprehensive container status information for the Lake service
# See: sys-arch.mmd CoreServices->LakeService->Storage

# NOTE: This script assumes docker-compose is running in the same directory
# FIXME: Add error handling for docker command failures
# TODO: Add resource usage monitoring (CPU, Memory, Network)
# TODO: Add log filtering options
# TODO: Add container health status checks

Write-Host "=== Docker Container Status ==="
docker ps -a  # Shows all containers, including stopped ones

Write-Host "`n=== Docker Networks ==="
docker network ls  # Network connectivity verification

Write-Host "`n=== Docker Volumes ==="
docker volume ls  # Data persistence verification

Write-Host "`n=== Service Logs ==="
# NOTE: Logs limited to Lake service for focused debugging
# TODO: Add timestamp filtering
# TODO: Add log level filtering
docker-compose logs datapunk-lake

# TODO: Add sections for:
# - Container resource metrics
# - Network connectivity tests
# - Volume mount verification
# - Configuration validation
# - Health check status
# - Performance metrics