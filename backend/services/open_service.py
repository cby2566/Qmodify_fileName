import subprocess
import sys
from pathlib import Path


def open_file(file_path: str, open_with: str = "") -> dict:
    """Open a file with the specified program or the system default."""
    p = Path(file_path)
    if not p.exists():
        return {"success": False, "error": f"File not found: {file_path}"}
    try:
        if open_with:
            subprocess.Popen([open_with, str(p)])
        else:
            if sys.platform == "win32":
                import os
                os.startfile(str(p))
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(p)])
            else:
                subprocess.Popen(["xdg-open", str(p)])
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}
