# Purpose: Debug script for Lake service container build process
# This script provides visibility into the build context and configuration
# for troubleshooting Docker build issues and permissions

# Show the build context
Write-Host "=== Build Context Files ==="
Get-ChildItem -Path .\datapunk-lake -Recurse | Select-Object FullName

# Show specific file content
# NOTE: init.sql is critical for database initialization
Write-Host "`n=== Init SQL Content ==="
Get-Content .\datapunk-lake\config\init.sql

# Show file permissions
# IMPORTANT: Ensures proper access rights for container execution
Write-Host "`n=== File Permissions ==="
Get-Acl .\datapunk-lake\config\init.sql | Format-List 

# TODO: Add validation checks for required files
# TODO: Add configuration validation
# TODO: Add error handling for missing files/directories 