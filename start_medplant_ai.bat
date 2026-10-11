@echo off
setlocal
cd /d "%~dp0"

echo =============================================
echo        MedPlant AI V9 - One Click Launcher
echo =============================================
echo.

echo [1/4] Checking Python...
py -3.14 --version
if errorlevel 1 (
    echo ERROR: Python 3.14 was not found with the py launcher.
    pause
    exit /b 1
)

echo.
echo [2/4] Preparing backend...
if not exist backend\.venv\Scripts\python.exe (
    py -3.14 -m venv backend\.venv
    if errorlevel 1 (
        echo ERROR: Could not create backend virtual environment.
        pause
        exit /b 1
    )
)
call backend\.venv\Scripts\activate.bat
python -m pip install --upgrade pip setuptools wheel
if errorlevel 1 (
    echo ERROR: pip upgrade failed. Check your internet connection.
    pause
    exit /b 1
)
python -m pip install -r backend\requirements.txt
if errorlevel 1 (
    echo ERROR: Backend dependency installation failed.
    pause
    exit /b 1
)

echo.
echo [3/4] Preparing frontend...
where npm >nul 2>nul
if errorlevel 1 (
    echo ERROR: npm was not found. Install Node.js first.
    pause
    exit /b 1
)
cd /d "%~dp0frontend"
if not exist node_modules (
    npm install
    if errorlevel 1 (
        echo ERROR: Frontend npm install failed.
        pause
        exit /b 1
    )
)
cd /d "%~dp0"

echo.
echo [4/4] Launching MedPlant AI...
start "MedPlant AI Backend" cmd /k "cd /d "%~dp0backend" && call .venv\Scripts\activate.bat && python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"
start "MedPlant AI Frontend" cmd /k "cd /d "%~dp0frontend" && npm run dev"

echo Waiting for the frontend to start...
timeout /t 7 /nobreak >nul
start "" http://localhost:5173/

echo.
echo MedPlant AI should now be open in your browser.
echo Keep the two black terminal windows running while you use the app.
pause
