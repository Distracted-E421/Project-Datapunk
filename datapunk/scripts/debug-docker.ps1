Write-Host "=== Docker Container Status ==="
docker ps -a

Write-Host "`n=== Docker Networks ==="
docker network ls

Write-Host "`n=== Docker Volumes ==="
docker volume ls

Write-Host "`n=== Service Logs ==="
docker-compose logs datapunk-lake