# Show the build context
Write-Host "=== Build Context Files ==="
Get-ChildItem -Path .\datapunk-lake -Recurse | Select-Object FullName

# Show specific file content
Write-Host "`n=== Init SQL Content ==="
Get-Content .\datapunk-lake\config\init.sql

# Show file permissions
Write-Host "`n=== File Permissions ==="
Get-Acl .\datapunk-lake\config\init.sql | Format-List 