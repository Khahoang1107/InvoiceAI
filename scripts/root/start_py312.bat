@echo off
echo ================================
echo Starting InvoiceAI with Python 3.12
echo ================================

cd /d %~dp0
call venv312\Scripts\activate.bat
cd backend
python --version
echo.
echo Starting server...
python main.py
