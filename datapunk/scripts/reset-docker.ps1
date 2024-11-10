# scripts/reset-docker.ps1

Write-Host "Stopping all containers..."
docker-compose down -v

Write-Host "Removing all related volumes..."
docker volume rm $(docker volume ls -q | Select-String "datapunk")

Write-Host "Pruning system..."
docker system prune -f

Write-Host "Rebuilding and starting services..."
docker-compose up --build