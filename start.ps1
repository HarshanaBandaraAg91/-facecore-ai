<#
.SYNOPSIS
    FACECORE AI — Production Local Deployment & Startup Script (PowerShell).

.DESCRIPTION
    Verifies virtual environments, checks model weight checksums, initializes
    SQLite database, starts the FastAPI backend (port 8001) and Vite frontend
    (port 5173), and manages graceful lifecycle termination.
#>

[CmdletBinding()]
param(
    [int]$BackendPort = 8001,
    [int]$FrontendPort = 5173,
    [switch]$SkipWeightCheck
)

$ErrorActionPreference = "Stop"
$WorkspaceRoot = $PSScriptRoot

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "           FACECORE AI — PRODUCTION LOCAL DEPLOYMENT SYSTEM          " -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "Root Directory: $WorkspaceRoot"

# 1. Check Python virtual environment
$VenvPython = Join-Path $WorkspaceRoot "backend\.venv\Scripts\python.exe"
if (-not (Test-Path $VenvPython)) {
    Write-Host "[ERROR] Python virtual environment not found at $VenvPython" -ForegroundColor Red
    Write-Host "Please create the venv: python -m venv backend\.venv && backend\.venv\Scripts\pip install -r backend\requirements.txt"
    exit 1
}

# 2. Check Node & npm
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] Node.js / npm not found on PATH. Please install Node.js (v18+)." -ForegroundColor Red
    exit 1
}

# 3. Verify Model Weights Checksums
if (-not $SkipWeightCheck) {
    Write-Host "`n[STEP 1/4] Verifying model weights cryptographic integrity..." -ForegroundColor Yellow
    $VerifyScript = Join-Path $WorkspaceRoot "backend\scripts\verify_weights.py"
    & $VenvPython $VerifyScript
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Model weight verification failed. Aborting startup." -ForegroundColor Red
        exit 1
    }
}

# 4. Check for Port Conflicts
Write-Host "`n[STEP 2/4] Verifying network ports..." -ForegroundColor Yellow
function Test-PortOccupied([int]$port) {
    $conn = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    return ($null -ne $conn)
}

if (Test-PortOccupied -port $BackendPort) {
    Write-Host "[WARN] Port $BackendPort is already in use. Existing process may already be running." -ForegroundColor Yellow
}
if (Test-PortOccupied -port $FrontendPort) {
    Write-Host "[WARN] Port $FrontendPort is already in use. Vite will automatically assign next available port." -ForegroundColor Yellow
}

# 5. Launch FastAPI Backend
Write-Host "`n[STEP 3/4] Starting FastAPI backend service on http://127.0.0.1:$BackendPort ..." -ForegroundColor Yellow
$BackendProcess = Start-Process -FilePath $VenvPython `
    -ArgumentList "-m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port $BackendPort" `
    -WorkingDirectory $WorkspaceRoot `
    -PassThru

# 6. Launch Vite Frontend
Write-Host "`n[STEP 4/4] Starting Vite frontend service on http://localhost:$FrontendPort ..." -ForegroundColor Yellow
$FrontendProcess = Start-Process -FilePath "npm.cmd" `
    -ArgumentList "--prefix frontend run dev" `
    -WorkingDirectory $WorkspaceRoot `
    -PassThru

Write-Host "`n======================================================================" -ForegroundColor Green
Write-Host "             FACECORE AI IS NOW RUNNING IN LOCAL MODE                " -ForegroundColor Green
Write-Host "======================================================================" -ForegroundColor Green
Write-Host "  Frontend UI:  http://localhost:$FrontendPort" -ForegroundColor Cyan
Write-Host "  Backend API:  http://127.0.0.1:$BackendPort" -ForegroundColor Cyan
Write-Host "  API Docs:     http://127.0.0.1:$BackendPort/docs" -ForegroundColor Cyan
Write-Host "  Backend PID:  $($BackendProcess.Id) | Frontend PID: $($FrontendProcess.Id)" -ForegroundColor DarkGray
Write-Host "`nPress Ctrl+C in this console to stop all services..." -ForegroundColor Magenta

# Trap clean termination
try {
    while ($true) {
        Start-Sleep -Seconds 2
        if ($BackendProcess.HasExited) {
            Write-Host "[WARN] Backend process terminated unexpectedly." -ForegroundColor Red
            break
        }
        if ($FrontendProcess.HasExited) {
            Write-Host "[WARN] Frontend process terminated unexpectedly." -ForegroundColor Red
            break
        }
    }
} finally {
    Write-Host "`nShutting down FACECORE AI services..." -ForegroundColor Yellow
    if (-not $BackendProcess.HasExited) {
        Stop-Process -Id $BackendProcess.Id -Force -ErrorAction SilentlyContinue
    }
    if (-not $FrontendProcess.HasExited) {
        Stop-Process -Id $FrontendProcess.Id -Force -ErrorAction SilentlyContinue
    }
    Write-Host "All processes stopped cleanly." -ForegroundColor Green
}

