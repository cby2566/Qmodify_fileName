@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"

echo ============================================
echo    File Renamer - Build Desktop App
echo ============================================
echo.

REM Check Python
set "PYTHON_CMD="
call :detect_python python
if not defined PYTHON_CMD call :detect_python py -3
if not defined PYTHON_CMD (
    echo [ERROR] Python 3.10+ was not found.
    pause
    exit /b 1
)

REM Check Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js was not found. Install Node.js 18+ first.
    pause
    exit /b 1
)

echo [3/4] Preparing build environment...
set "VENV_PY=backend\venv\Scripts\python.exe"
if not exist "%VENV_PY%" (
    echo Creating virtual environment for packaging...
    %PYTHON_CMD% -m venv backend\venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
)

echo Installing Python dependencies...
"%VENV_PY%" -m pip install -r backend\requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)

echo [4/4] Building frontend and packaging...
cd /d "%~dp0frontend"
call npm run build
if errorlevel 1 (
    echo [ERROR] Failed to build frontend.
    pause
    exit /b 1
)
cd /d "%~dp0"

echo Checking PyInstaller...
"%VENV_PY%" -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo Installing PyInstaller...
    "%VENV_PY%" -m pip install pyinstaller
    if errorlevel 1 (
        echo [ERROR] Failed to install PyInstaller.
        pause
        exit /b 1
    )
)

echo Running PyInstaller...
"%VENV_PY%" -m PyInstaller packaging\file_renamer.spec --clean --noconfirm
if errorlevel 1 (
    echo [ERROR] PyInstaller failed.
    pause
    exit /b 1
)

echo.
echo ============================================
echo    Build Complete!
echo    Output: dist\FileRenamer\
echo ============================================
echo.
echo You can now:
echo   1. Test the app: run dist\FileRenamer\FileRenamer.exe
echo   2. Package as ZIP: compress dist\FileRenamer\ folder
echo.

pause
exit /b 0

:detect_python
%* -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
if not errorlevel 1 set "PYTHON_CMD=%*"
exit /b 0
