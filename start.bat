@echo off
chcp 65001 >nul
echo ============================================
echo    文件批量重命名工具 - 启动脚本
echo ============================================
echo.

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python，请先安装 Python 3.10+
    pause
    exit /b 1
)

REM 检查 Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Node.js，请先安装 Node.js 18+
    pause
    exit /b 1
)

REM 创建虚拟环境并安装后端依赖
if not exist "backend\venv" (
    echo [1/4] 创建 Python 虚拟环境...
    python -m venv backend\venv
)

echo [2/4] 安装后端依赖...
call backend\venv\Scripts\activate.bat
pip install -r backend\requirements.txt
call backend\venv\Scripts\deactivate.bat

REM 安装前端依赖
if not exist "frontend\node_modules" (
    echo [3/4] 安装前端依赖...
    cd frontend
    npm install
    cd ..
) else (
    echo [3/4] 前端依赖已存在，跳过安装
)

REM 启动服务
echo [4/4] 启动服务...
echo.

start "文件重命名工具 - 后端" cmd /k "cd backend && venv\Scripts\activate && python -m uvicorn main:app --reload --port 8000"
timeout /t 3 /nobreak >nul
start "文件重命名工具 - 前端" cmd /k "cd frontend && npm run dev"

echo.
echo ============================================
echo    服务启动中...
echo    后端: http://localhost:8000
echo    前端: http://localhost:5173
echo ============================================
echo.
echo 按任意键退出此窗口（服务将继续运行）
pause >nul
