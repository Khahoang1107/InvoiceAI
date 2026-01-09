@echo off
REM Setup Python 3.12 Environment (One-time setup)
echo ========================================
echo  Setup Python 3.12 for InvoiceAI
echo  This script will create venv312
echo ========================================
echo.

cd /d "%~dp0"

REM Check if Python 3.12 is installed
py -3.12 --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python 3.12 not found!
    echo Please install Python 3.12 from https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [INFO] Python 3.12 found
py -3.12 --version

REM Create virtual environment
if exist "venv312" (
    echo [INFO] venv312 already exists, skipping creation
) else (
    echo [INFO] Creating Python 3.12 virtual environment...
    py -3.12 -m venv venv312
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
    echo [SUCCESS] Virtual environment created
)

REM Activate and install dependencies
echo.
echo [INFO] Activating virtual environment...
call venv312\Scripts\activate.bat

echo [INFO] Upgrading pip...
python -m pip install --upgrade pip

echo.
echo [INFO] Installing dependencies...
echo This may take a few minutes...
echo.

REM Core dependencies
pip install fastapi uvicorn sqlalchemy psycopg2-binary python-dotenv pydantic pydantic-settings pydantic[email]

REM OCR & NER
pip install pytesseract spacy pyvi scikit-learn

REM AI & Vector DB
pip install groq pinecone-client

REM Auth & Utils
pip install python-jose PyJWT bcrypt passlib pillow python-multipart requests alembic

echo.
echo [INFO] Checking if NER model exists...
if exist "models\invoice_ner" (
    echo [SUCCESS] NER model found
) else (
    echo [INFO] Training NER model...
    python train_ner_quick.py
    if errorlevel 1 (
        echo [WARNING] NER training failed, but continuing...
    ) else (
        echo [SUCCESS] NER model trained
    )
)

echo.
echo ========================================
echo  Setup Complete!
echo ========================================
echo.
echo To start the backend, run:
echo   start_py312.bat
echo.
echo Or manually:
echo   venv312\Scripts\activate
echo   python main_refactored.py
echo.
pause
