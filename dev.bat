@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"

echo ============================================
echo    File Renamer - Quick Start (no install)
echo ============================================
echo.

if not exist "backend\venv\Scripts\python.exe" (
    echo [ERROR] backend\venv not found. Run start.bat once to set it up.
    pause
    exit /b 1
)
if not exist "frontend\node_modules" (
    echo [ERROR] frontend\node_modules not found. Run start.bat once to set it up.
    pause
    exit /b 1
)

echo [1/2] Starting backend ...
start "File Renamer - Backend" cmd /k "cd /d ""%~dp0backend"" && venv\Scripts\python.exe -m uvicorn main:app --reload --port 8099"

timeout /t 3 /nobreak >nul

echo [2/2] Starting frontend ...
start "File Renamer - Frontend" cmd /k "cd /d ""%~dp0frontend"" && npm run dev"

echo.
echo ============================================
echo    Services are starting...
echo    Backend:  http://localhost:8099
echo    Frontend: http://localhost:5173
echo ============================================
echo.
echo Press any key to close this window. Services will keep running.
pause >nul
exit /b 0
