# Run from root with: .\datapunk\docs\MVP\graphs\config\scripts\generate-deployment-view.ps1

$rootDir = Split-Path (Split-Path (Split-Path (Split-Path (Split-Path $PSScriptRoot))))
$configPath = Join-Path (Split-Path $PSScriptRoot) "mermaid-theme.json"
$inputPath = Join-Path $rootDir "docs/MVP/graphs/mmd/detailed-views/deployment-view.mmd"
$outputDir = Join-Path $rootDir "docs/MVP/graphs/output/"

# Create output directory if it doesn't exist
if (!(Test-Path $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir -Force
}

$outputPath = Join-Path $outputDir "deployment-view.svg"

Write-Host "Processing: deployment-view.mmd"
mmdc "-i" $inputPath "-o" $outputPath "-c" $configPath 