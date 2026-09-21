import os
import subprocess
import sys
from pathlib import Path


def _launch_default(target: Path) -> None:
    """Hand the path to the OS default handler (Explorer / Finder / xdg-open)."""
    if sys.platform == "win32":
        os.startfile(str(target))
    elif sys.platform == "darwin":
        subprocess.Popen(["open", str(target)])
    else:
        subprocess.Popen(["xdg-open", str(target)])


def _launch_with(program: str, target: Path) -> None:
    """Run a user-specified program against a path.

    The path is passed as a list argument so that programs whose own path
    contains spaces (``C:\\Program Files\\...``) are still launched correctly.
    """
    program = program.strip().strip('"')
    subprocess.Popen([program, str(target)])


def open_file(file_path: str, open_with: str = "", is_dir: bool = False) -> dict:
    """Open a file or directory, optionally through a user-chosen program.

    When ``open_with`` is empty the OS default handler is used, which for a
    directory means the system file manager.
    """
    p = Path(file_path)
    if not p.exists():
        return {"success": False, "error": f"Path not found: {file_path}"}
    try:
        if open_with and open_with.strip():
            _launch_with(open_with, p)
        else:
            _launch_default(p)
        return {"success": True, "opened_as": "dir" if p.is_dir() else "file"}
    except Exception as e:
        return {"success": False, "error": str(e)}

