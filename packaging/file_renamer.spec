# -*- mode: python ; coding: utf-8 -*-

"""
File Renamer - PyInstaller 配置文件
打包为单文件 exe 或文件夹
"""

import os
from pathlib import Path

# ============ 基础配置 ============
block_cipher = None
project_root = Path(".").resolve()
backend_dir = project_root / "backend"
frontend_dist = project_root / "frontend" / "dist"

# ============ 数据文件收集 ============
datas = []

# 1. 前端构建产物（必须）
if frontend_dist.exists():
    datas.append((str(frontend_dist), "frontend/dist"))
    print(f"[PyInstaller] Found frontend dist: {frontend_dist}")
else:
    print(f"[PyInstaller] WARNING: Frontend dist not found: {frontend_dist}")
    print("[PyInstaller] Please run 'npm run build' first.")

# 2. 后端数据模板（可选，用于首次运行时初始化）
data_dir = backend_dir / "data"
if data_dir.exists():
    # 只包含 JSON 模板文件，不包含日志数据库
    for json_file in data_dir.glob("*.json"):
        datas.append((str(json_file), "backend/data"))
        print(f"[PyInstaller] Found data file: {json_file.name}")

# ============ 二进制文件收集 ============
binaries = []

# ============ 隐藏导入 ============
hiddenimports = [
    # FastAPI 相关
    "fastapi",
    "uvicorn",
    "uvicorn.logging",
    "uvicorn.loops",
    "uvicorn.loops.auto",
    "uvicorn.protocols",
    "uvicorn.protocols.http",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.websockets",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.lifespan",
    "uvicorn.lifespan.on",
    "pydantic",
    "pydantic.json",
    # 其他依赖
    "sqlite3",
    "json",
    "pathlib",
    "webbrowser",
    "threading",
    "socket",
    "platform",
    "ctypes",
    "re",
    "datetime",
    "typing",
    "shutil",
    "uuid",
    "base64",
    "csv",
]

# ============ 排除不必要的模块 ============
excludes = [
    "tkinter",
    "matplotlib",
    "scipy",
    "pandas",
    "PIL",
    "PyQt5",
    "PyQt6",
    "PySide2",
    "PySide6",
]

# ============ 入口脚本 ============
entry_script = str(backend_dir / "desktop_main.py")

# ============ 分析 ============
a = Analysis(
    [entry_script],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# ============ PYZ（Python 字节码） ============
pyz = PYZ(a.pure)

# ============ EXE 可执行文件 ============
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="FileRenamer",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # UPX 压缩会触发杀毒软件误报，建议关闭
    console=True,  # 显示控制台窗口（用于调试和日志）
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # 可添加图标路径，如 "assets/icon.ico"
    version_file=None,
)

# ============ 收集所有文件到文件夹 ============
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="FileRenamer",
)
