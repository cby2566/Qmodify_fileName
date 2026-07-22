#!/usr/bin/env python3
"""
打包桌面应用的 Python 脚本（跨平台兼容）
"""
import subprocess
import sys
import shutil
from pathlib import Path

def run_command(cmd, description=""):
    """运行命令并打印输出"""
    if description:
        print(f"\n{'='*60}")
        print(f"  {description}")
        print(f"{'='*60}\n")

    print(f"Running: {' '.join(cmd)}\n")
    result = subprocess.run(cmd, capture_output=False)
    if result.returncode != 0:
        print(f"\n[ERROR] Command failed with exit code {result.returncode}")
        sys.exit(result.returncode)
    return result.returncode == 0

def main():
    project_root = Path(__file__).parent
    os.chdir(project_root)

    print("="*60)
    print("  File Renamer - Build Desktop App")
    print("="*60)
    print()

    # Step 1: Check Node.js
    print("[1/5] Checking Node.js...")
    if not shutil.which("node"):
        print("[ERROR] Node.js not found. Please install Node.js 18+")
        sys.exit(1)

    # Step 2: Build frontend
    print("[2/5] Building frontend...")
    if not run_command(["npm", "run", "build"], "Building Frontend"):
        sys.exit(1)
    os.chdir(project_root)

    # Step 3: Check/Create virtual environment
    print("[3/5] Preparing Python virtual environment...")
    venv_py = project_root / "backend" / "venv" / "Scripts" / "python.exe"
    if not venv_py.exists():
        print("Creating virtual environment...")
        subprocess.run([sys.executable, "-m", "venv", "backend/venv"], check=True)

    # Step 4: Install dependencies
    print("[4/5] Installing dependencies...")
    pip_cmd = str(venv_py).replace("python.exe", "pip.exe")
    run_command([pip_cmd, "install", "-r", "backend/requirements.txt"], "Installing Python Dependencies")

    # Install PyInstaller
    run_command([pip_cmd, "install", "pyinstaller"], "Installing PyInstaller")

    # Step 5: Run PyInstaller
    print("[5/5] Packaging with PyInstaller...")
    pyinstaller_cmd = str(venv_py).replace("python.exe", "pyinstaller.exe")
    spec_file = project_root / "packaging" / "file_renamer.spec"

    if not run_command(
        [pyinstaller_cmd, str(spec_file), "--clean", "--noconfirm"],
        "Running PyInstaller"
    ):
        sys.exit(1)

    # Success
    print("\n" + "="*60)
    print("  Build Complete!")
    print("  Output: dist\\FileRenamer\\")
    print("="*60)
    print("\nYou can now:")
    print("  1. Test the app: dist\\FileRenamer\\FileRenamer.exe")
    print("  2. Package as ZIP: compress dist\\FileRenamer\\ folder")
    print()

if __name__ == "__main__":
    import os
    main()
