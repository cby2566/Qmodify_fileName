# -*- mode: python ; coding: utf-8 -*-

"""
File Renamer - PyInstaller 单文件配置
打包为单个 .exe 文件（推荐用于分发）
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

# 前端构建产物
if frontend_dist.exists():
    datas.append((str(frontend_dist), "frontend/dist"))
else:
    print("[PyInstaller] WARNING: Frontend dist not found.")
    print("[PyInstaller] Run 'npm run build' first.")

# 后端数据模板
data_dir = backend_dir / "data"
if data_dir.exists():
    for json_file in data_dir.glob("*.json"):
        datas.append((str(json_file), "backend/data"))

# ============ 入口脚本 ============
entry_script = str(backend_dir / "desktop_main.py")

# ============ 分析 ============
a = Analysis(
    [entry_script],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[
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
        "sqlite3",
        "json",
        "webbrowser",
        "socket",
        "platform",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tkinter",
        "matplotlib",
        "scipy",
        "pandas",
        "PIL",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="FileRenamer",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # 关闭 UPX 避免杀毒软件误报
    console=True,  # 显示控制台窗口
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="FileRenamer",
)
