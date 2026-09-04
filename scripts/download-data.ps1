$ErrorActionPreference = "Stop"

$repositoryRoot = Split-Path -Parent $PSScriptRoot
$destination = Join-Path $repositoryRoot "data/raw"

New-Item -ItemType Directory -Force -Path $destination | Out-Null

python -m kaggle datasets download `
  -d olistbr/brazilian-ecommerce `
  -p $destination `
  --unzip

Write-Host "Dataset extracted to $destination"
