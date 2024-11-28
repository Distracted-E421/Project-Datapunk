# Docker Environment Reset Script
# Performs complete cleanup and rebuild of Docker environment
# See: sys-arch.mmd Infrastructure->Docker->Management

# NOTE: This script requires administrative privileges
# TODO: Add error handling for volume removal failures
# TODO: Add selective container reset capability
# TODO: Add environment-specific configurations
# FIXME: Improve volume pattern matching

# Stop all running containers and remove volumes
# NOTE: Force removal to handle stuck containers
Write-Host "Stopping all containers..."
docker-compose down -v

# Remove project-specific volumes to ensure clean state
# NOTE: Uses pattern matching to target only project volumes
Write-Host "Removing all related volumes..."
docker volume rm $(docker volume ls -q | Select-String "datapunk")

# Clean up unused Docker resources
# NOTE: Force cleanup without confirmation for automation
Write-Host "Pruning system..."
docker system prune -f

# Rebuild and start services with fresh state
# TODO: Add health check verification
Write-Host "Rebuilding and starting services..."
docker-compose up --build