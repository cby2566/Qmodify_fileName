@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"

echo ============================================
echo    File Renamer - Stop Services
echo ============================================
echo.

set "KILLED=0"

REM --- Kill backend (port 8099) ---
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8099" ^| findstr "LISTENING"') do (
    taskkill /PID %%a /F >nul 2>&1
    if not errorlevel 1 (
        echo [OK] backend PID %%a (port 8099) stopped
        set "KILLED=1"
    )
)

REM --- Kill frontend (port 5173) ---
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5173" ^| findstr "LISTENING"') do (
    taskkill /PID %%a /F >nul 2>&1
    if not errorlevel 1 (
        echo [OK] frontend PID %%a (port 5173) stopped
        set "KILLED=1"
    )
)

REM --- Fallback: kill by window title ---
taskkill /FI "WINDOWTITLE eq File Renamer - Backend*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq File Renamer - Frontend*" /F >nul 2>&1

echo.
if "%KILLED%"=="1" (
echo ============================================
echo    Services stopped.
echo ============================================
) else (
echo ============================================
echo    No running services found.
echo ============================================
)
echo.
pause
exit /b 0
