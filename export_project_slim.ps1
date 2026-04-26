param(
  [string]$OutputZip = ""
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$parentDir = Split-Path -Parent $projectRoot

if ([string]::IsNullOrWhiteSpace($OutputZip)) {
  $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
  $OutputZip = Join-Path $parentDir "jarvis_pro_slim_$timestamp.zip"
}

$tempDir = Join-Path $env:TEMP ("jarvis_pro_slim_" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $tempDir | Out-Null

try {
  $excludeDirs = @(
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    "node_modules",
    "dist",
    "build"
  )

  $robocopyExcludes = @()
  foreach ($d in $excludeDirs) {
    $robocopyExcludes += $d
  }

  $null = robocopy $projectRoot $tempDir /E /NFL /NDL /NJH /NJS /NC /NS /XD $robocopyExcludes

  if (Test-Path $OutputZip) {
    Remove-Item $OutputZip -Force
  }
  Compress-Archive -Path "$tempDir\*" -DestinationPath $OutputZip -Force
  Write-Host "Exported slim project to: $OutputZip" -ForegroundColor Green
}
finally {
  if (Test-Path $tempDir) {
    Remove-Item $tempDir -Recurse -Force
  }
}
