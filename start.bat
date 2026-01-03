@echo off
REM Quick Start Script for InvoiceAI
REM ==================================

echo.
echo ========================================
echo   InvoiceAI - Quick Start
echo ========================================
echo.

REM Check if Docker is available
docker --version >nul 2>&1
if %errorlevel% == 0 (
    echo Docker detected! Starting with Docker...
    echo.
    docker-compose up -d
    echo.
    echo Application started successfully!
    echo.
    echo Frontend: http://localhost:3000
    echo Backend:  http://localhost:8000
    echo API Docs: http://localhost:8000/docs
    echo.
    goto :end
)

REM Manual start
echo Docker not found. Starting manually...
echo.

echo Starting Backend...
start "InvoiceAI Backend" cmd /k "cd /d %~dp0backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000"

timeout /t 3 /nobreak >nul

echo Starting Frontend Dev Server...
start "InvoiceAI Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

timeout /t 2 /nobreak >nul

echo.
echo ========================================
echo   Application Starting...
echo ========================================
echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:5173
echo API Docs: http://localhost:8000/docs
echo.
echo Two terminal windows have been opened.
echo Close them to stop the application.
echo.

:end
pause
