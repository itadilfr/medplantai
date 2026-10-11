@echo off
setlocal
cd /d "%~dp0backend"

echo ==========================================
echo MedPlant AI - Backend Setup
 echo Python 3.14 compatible build
 echo ==========================================

if not exist .venv\Scripts\python.exe (
    echo Creating Python virtual environment...
    py -3.14 -m venv .venv
    if errorlevel 1 (
        echo.
        echo ERROR: Could not create the virtual environment.
        echo Make sure Python 3.14 is installed and available through the "py -3.14" launcher.
        pause
        exit /b 1
    )
)

call .venv\Scripts\activate.bat
python -m pip install --upgrade pip setuptools wheel
if errorlevel 1 (
    echo.
    echo ERROR: pip upgrade failed. Check your internet connection.
    pause
    exit /b 1
)

python -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo ERROR: Backend dependencies could not be installed.
    echo If an older partial environment exists, delete backend\.venv and run this again.
    pause
    exit /b 1
)

echo.
echo Backend starting at http://127.0.0.1:8000
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
pause
