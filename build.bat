@echo off
REM Build and Deploy Script for InvoiceAI
REM ======================================

echo.
echo ========================================
echo   InvoiceAI - Build and Deploy
echo ========================================
echo.

REM Check if in correct directory
if not exist "frontend\package.json" (
    echo Error: package.json not found in frontend directory
    echo Please run this script from the project root
    pause
    exit /b 1
)

echo [1/4] Installing frontend dependencies...
cd frontend
call npm install
if errorlevel 1 (
    echo Error: npm install failed
    pause
    exit /b 1
)

echo.
echo [2/4] Building frontend...
call npm run build
if errorlevel 1 (
    echo Error: npm build failed
    pause
    exit /b 1
)

cd ..

echo.
echo [3/4] Checking backend...
if not exist "backend\main.py" (
    echo Error: main.py not found in backend directory
    pause
    exit /b 1
)

echo Backend files found ✓

echo.
echo [4/4] Checking Python dependencies...
cd backend
python -c "import fastapi" 2>nul
if errorlevel 1 (
    echo Installing backend dependencies...
    pip install -r requirements.txt
)
cd ..

echo.
echo ========================================
echo   Build Completed Successfully! ✓
echo ========================================
echo.
echo Build output: frontend\dist\
echo.
echo To start the application:
echo   Backend:  cd backend ^&^& uvicorn main:app --reload
echo   Frontend: Serve the dist folder or use development mode
echo.
echo To test admin API:
echo   python test_admin_api.py
echo.
pause
