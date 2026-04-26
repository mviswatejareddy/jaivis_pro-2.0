param(
  [string]$OutputZip = ""
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

if ([string]::IsNullOrWhiteSpace($OutputZip)) {
  $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
  $OutputZip = Join-Path (Split-Path -Parent $projectRoot) "jarvis_pro_complete_$timestamp.zip"
}

if (Test-Path $OutputZip) {
  Remove-Item $OutputZip -Force
}

Compress-Archive -Path "$projectRoot\*" -DestinationPath $OutputZip -Force
Write-Host "Exported complete project to: $OutputZip" -ForegroundColor Green
