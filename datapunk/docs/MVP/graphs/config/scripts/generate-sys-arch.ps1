# Run from root with: .\datapunk\docs\MVP\graphs\config\scripts\generate-sys-arch.ps1

$rootDir = Split-Path (Split-Path (Split-Path (Split-Path (Split-Path $PSScriptRoot))))
$configPath = Join-Path (Split-Path $PSScriptRoot) "mermaid-theme.json"
$inputPath = Join-Path $rootDir "docs/MVP/graphs/mmd/overview/sys-arch.mmd"
$outputDir = Join-Path $rootDir "docs/MVP/graphs/output/svg/overview"

# Create output directory if it doesn't exist
if (!(Test-Path $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir -Force
}

$outputPath = Join-Path $outputDir "sys-arch.svg"

Write-Host "Processing: sys-arch.mmd from $inputPath"
Write-Host "Output to: $outputPath"
Write-Host "Using config: $configPath"

mmdc "-i" $inputPath "-o" $outputPath "-c" $configPath