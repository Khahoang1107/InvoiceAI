# PowerShell script to start backend with Python 3.12
# Usage: .\start_py312.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Starting InvoiceAI Backend (Python 3.12)" -ForegroundColor Cyan
Write-Host " NER Service: ENABLED" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Change to script directory
Set-Location $PSScriptRoot

# Check if venv312 exists
if (-not (Test-Path "venv312\Scripts\python.exe")) {
    Write-Host "[ERROR] Python 3.12 virtual environment not found!" -ForegroundColor Red
    Write-Host "Please run setup_py312.bat first" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Activate virtual environment
Write-Host "[INFO] Activating Python 3.12 environment..." -ForegroundColor Yellow
& ".\venv312\Scripts\Activate.ps1"

# Verify Python version
$pythonVersion = & python --version
Write-Host "[INFO] $pythonVersion" -ForegroundColor Green

# Start server
Write-Host ""
Write-Host "[INFO] Starting FastAPI server on http://localhost:8000" -ForegroundColor Green
Write-Host "[INFO] Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

python main_refactored.py
