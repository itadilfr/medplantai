@echo off
setlocal
cd /d "%~dp0frontend"

echo ==========================================
echo MedPlant AI - Frontend Setup
 echo ==========================================

if not exist node_modules (
    echo Installing frontend packages...
    npm install
    if errorlevel 1 (
        echo.
        echo ERROR: npm install failed.
        echo Check that Node.js and npm are installed and that you have internet access.
        pause
        exit /b 1
    )
)

echo.
echo Frontend starting at http://localhost:5173
npm run dev
pause
