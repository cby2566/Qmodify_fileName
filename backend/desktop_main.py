"""
桌面应用模式入口 - 独立于开发模式
提供静态文件服务 + 自动打开浏览器 + 动态端口
"""
import os
import sys
import socket
import webbrowser
import threading
import time
from pathlib import Path
from contextlib import asynccontextmanager

# ============ 数据目录配置 ============
# 桌面模式使用用户数据目录，避免和开发模式冲突
def get_app_data_dir() -> Path:
    """获取应用数据目录（用户可写）"""
    if sys.platform == "win32":
        app_data = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    else:
        app_data = Path.home() / ".local" / "share"

    app_dir = app_data / "FileRenamer"
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir


# 设置环境变量，让其他模块使用用户数据目录
os.environ["FILERENAMER_DATA_DIR"] = str(get_app_data_dir())

# 现在导入 FastAPI 和路由（会使用环境变量中的数据目录）
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from services import log_service
from routers import files, regex, rename, favorites, logs, export, settings, desktop
from routers import open as open_router


# ============ 生命周期管理 ============
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时初始化数据库"""
    log_service.init_db()
    yield


# ============ 动态端口查找 ============
def find_available_port(start_port=8099, max_attempts=20):
    """查找可用端口"""
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("127.0.0.1", port))
                return port
        except OSError:
            continue
    # 如果都失败，使用 0（系统自动分配）
    return 0


# ============ 延迟打开浏览器 ============
def open_browser_delayed(url: str, delay: float = 2.0):
    """延迟打开浏览器，等待后端完全启动"""

    def _open():
        time.sleep(delay)
        webbrowser.open(url)

    threading.Thread(target=_open, daemon=True).start()


# ============ 创建 FastAPI 应用 ============
def create_app() -> FastAPI:
    """创建 FastAPI 应用（桌面模式）"""
    app = FastAPI(
        title="File Renamer - Desktop",
        description="Batch File Renamer Desktop Application",
        version="1.0.0",
        lifespan=lifespan,
    )

    # CORS 配置（桌面模式不需要，但保持兼容）
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 注册 API 路由（添加 /api 前缀以匹配前端请求）
    app.include_router(files.router, prefix="/api")
    app.include_router(regex.router, prefix="/api")
    app.include_router(rename.router, prefix="/api")
    app.include_router(favorites.router, prefix="/api")
    app.include_router(logs.router, prefix="/api")
    app.include_router(export.router, prefix="/api")
    app.include_router(settings.router, prefix="/api")
    app.include_router(open_router.router, prefix="/api")
    app.include_router(desktop.router, prefix="/api")

    # 健康检查
    @app.get("/health")
    def health():
        return {"status": "ok", "mode": "desktop"}

    # ============ 提供前端静态文件 ============
    # 判断是否是打包后的 exe
    if getattr(sys, "frozen", False):
        # PyInstaller 打包模式：使用 _MEIPASS
        base_path = Path(sys._MEIPASS)
    else:
        # 开发模式：相对于此文件的路径
        base_path = Path(__file__).parent.parent

    frontend_dist = base_path / "frontend" / "dist"

    if frontend_dist.exists():
        # 挂载静态文件服务（根路径提供前端）
        app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")
        print(f"[Desktop Mode] Serving frontend from: {frontend_dist}")
    else:
        print(f"[Desktop Mode] WARNING: Frontend dist not found at {frontend_dist}")
        print("[Desktop Mode] API endpoints will still be available.")

    return app


# ============ 主入口 ============
if __name__ == "__main__":
    import uvicorn

    print("=" * 50)
    print("  File Renamer - Desktop Mode")
    print("=" * 50)
    print()

    # 显示数据目录
    data_dir = get_app_data_dir()
    print(f"[Desktop Mode] Data directory: {data_dir}")

    # 查找可用端口
    port = find_available_port(8099)
    print(f"[Desktop Mode] Using port: {port}")

    # 创建应用
    app = create_app()

    # 准备打开浏览器
    url = f"http://localhost:{port}"
    open_browser_delayed(url, delay=2.5)
    print(f"[Desktop Mode] Opening browser: {url}")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 50)
    print()

    # 启动服务器
    try:
        uvicorn.run(
            app,
            host="127.0.0.1",
            port=port,
            log_level="info",
            access_log=True,
        )
    except KeyboardInterrupt:
        print("\n[Desktop Mode] Server stopped.")
        sys.exit(0)
