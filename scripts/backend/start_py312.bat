@echo off
REM Start Backend with Python 3.12 (NER-enabled)
echo ========================================
echo  Starting InvoiceAI Backend (Python 3.12)
echo  NER Service: ENABLED
echo ========================================
echo.

cd /d "%~dp0"

REM Check if venv312 exists
if not exist "venv312\Scripts\python.exe" (
    echo [ERROR] Python 3.12 virtual environment not found!
    echo Please run setup_py312.bat first
    pause
    exit /b 1
)

REM Activate virtual environment and start server
echo [INFO] Activating Python 3.12 environment...
call venv312\Scripts\activate.bat

echo [INFO] Starting FastAPI server on http://localhost:8000
echo [INFO] Press Ctrl+C to stop the server
echo.

python main_refactored.py
