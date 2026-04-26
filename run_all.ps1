param(
  [string]$BackendHost = "0.0.0.0",
  [int]$BackendPort = 8000,
  [int]$FrontendPort = 5173
)

$ErrorActionPreference = "Stop"

Write-Host "Starting Jarvis Pro backend + dashboard..." -ForegroundColor Cyan

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$dashboardRoot = Join-Path $projectRoot "dashboard"

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
  throw "Python is not installed or not in PATH."
}

if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
  throw "npm is not installed or not in PATH."
}

Write-Host "Backend: http://localhost:$BackendPort" -ForegroundColor Green
Write-Host "Frontend: http://localhost:$FrontendPort" -ForegroundColor Green

$backendCmd = "cd `"$projectRoot`"; uvicorn src.jarvis.api.server:app --host $BackendHost --port $BackendPort"
$frontendCmd = "cd `"$dashboardRoot`"; npm install; npm run dev -- --port $FrontendPort"

Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCmd
Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCmd

Write-Host "Both processes launched in separate terminals." -ForegroundColor Yellow
