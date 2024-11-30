# Run from root with: .\datapunk\docs\MVP\graphs\config\scripts\generate-service-mesh.ps1

$rootDir = Split-Path (Split-Path (Split-Path (Split-Path (Split-Path $PSScriptRoot))))
$configPath = Join-Path (Split-Path $PSScriptRoot) "mermaid-theme.json"
$inputPath = Join-Path $rootDir "docs/MVP/graphs/mmd/detailed-views/service-mesh.mmd"
$outputDir = Join-Path $rootDir "docs/MVP/graphs/output/svg/detailed-views"

# Create output directory if it doesn't exist
if (!(Test-Path $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir -Force
}

$outputPath = Join-Path $outputDir "service-mesh.svg"

Write-Host "Processing: service-mesh.mmd"
mmdc "-i" $inputPath "-o" $outputPath "-c" $configPath 