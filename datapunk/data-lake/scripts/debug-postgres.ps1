Write-Host "=== PostgreSQL Container Logs ==="
docker logs datapunk_lake

Write-Host "`n=== PostgreSQL Configuration ==="
docker exec datapunk_lake cat /etc/postgresql/postgresql.conf

Write-Host "`n=== Installed Extensions ==="
docker exec datapunk_lake psql -U datapunk -d datapunk -c "\dx"

Write-Host "`n=== PostgreSQL Error Log ==="
docker exec datapunk_lake Get-Content /var/log/postgresql/postgresql-*.log -Tail 50