@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"

echo ============================================
echo    File Renamer - Desktop Mode
echo ============================================
echo.

REM Check Python 3.10+
set "PYTHON_CMD="
call :detect_python python
if not defined PYTHON_CMD call :detect_python py -3
if not defined PYTHON_CMD (
    echo [ERROR] Python 3.10+ was not found.
    echo Install Python 3.10+ and enable "Add python.exe to PATH".
    pause
    exit /b 1
)

REM Check Node.js (needed for building frontend)
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js was not found. Install Node.js 18+ first.
    pause
    exit /b 1
)

REM Create or repair the virtual environment
set "VENV_PY=backend\venv\Scripts\python.exe"
set "RECREATE_VENV=0"
if not exist "%VENV_PY%" (
    set "RECREATE_VENV=1"
) else (
    "%VENV_PY%" -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
    if errorlevel 1 set "RECREATE_VENV=1"
)

if "%RECREATE_VENV%"=="1" (
    echo [1/3] Creating or repairing Python virtual environment...
    if exist "backend\venv" rmdir /s /q "backend\venv"
    %PYTHON_CMD% -m venv backend\venv
    if errorlevel 1 (
        echo [ERROR] Failed to create Python virtual environment.
        pause
        exit /b 1
    )
) else (
    echo [1/3] Backend virtual environment is available, skipping creation.
)

echo [2/3] Installing backend dependencies...
"%VENV_PY%" -m pip install -r backend\requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install backend dependencies.
    pause
    exit /b 1
)

REM Build frontend if dist doesn't exist
if not exist "frontend\dist\index.html" (
    echo [3/3] Building frontend...
    cd /d "%~dp0frontend"
    call npm run build
    if errorlevel 1 (
        echo [ERROR] Failed to build frontend.
        pause
        exit /b 1
    )
    cd /d "%~dp0"
) else (
    echo [3/3] Frontend build already exists, skipping build.
)

echo.
echo ============================================
echo    Starting Desktop Mode...
echo    Data directory: %%APPDATA%%\FileRenamer
echo ============================================
echo.

REM Start desktop mode (opens browser automatically)
start "File Renamer - Desktop" cmd /k "cd /d ""%~dp0backend"" && venv\Scripts\python.exe desktop_main.py"

echo.
echo Desktop mode is starting...
echo Press any key to close this window (server will keep running).
pause >nul
exit /b 0

:detect_python
%* -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
if not errorlevel 1 set "PYTHON_CMD=%*"
exit /b 0
