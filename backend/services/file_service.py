from pathlib import Path
from typing import List, Optional
import datetime
from models.file_models import FileInfo


def _human_size(size_bytes: int) -> str:
    """Convert bytes to a human-readable string (B/KB/MB/GB/TB)."""
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(size_bytes)
    for unit in units:
        if size < 1024 or unit == "TB":
            if unit == "B":
                return f"{int(size)} {unit}"
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} PB"


def _match_extension(filename: str, ext_set: set) -> bool:
    """Match against compound extensions like .tar.gz as well as simple ones."""
    lower = filename.lower()
    return any(lower.endswith(ext) for ext in ext_set)


def scan_directory(
    path: str,
    extensions: Optional[List[str]] = None,
    recursive: bool = False,
    max_depth: int = 5,
) -> List[FileInfo]:
    """Recursively or non-recursively scan a directory for files."""
    root = Path(path)
    if not root.exists():
        raise FileNotFoundError(f"Directory not found: {path}")
    if not root.is_dir():
        raise NotADirectoryError(f"Not a directory: {path}")

    if extensions:
        ext_set = {e.lower() if e.startswith(".") else f".{e.lower()}" for e in extensions}
    else:
        ext_set = None

    results: List[FileInfo] = []

    def _walk(current: Path, depth: int):
        try:
            entries = list(current.iterdir())
        except PermissionError:
            return
        for entry in entries:
            try:
                if entry.is_file():
                    if ext_set is None or _match_extension(entry.name, ext_set):
                        stat = entry.stat()
                        results.append(FileInfo(
                            filename=entry.name,
                            stem=entry.stem,
                            extension=entry.suffix,
                            size_bytes=stat.st_size,
                            size_display=_human_size(stat.st_size),
                            created_time=datetime.datetime.fromtimestamp(
                                stat.st_ctime
                            ).isoformat(),
                            modified_time=datetime.datetime.fromtimestamp(
                                stat.st_mtime
                            ).isoformat(),
                            full_path=str(entry.resolve()),
                            parent_dir=str(entry.parent.resolve()),
                        ))
                elif recursive and depth < max_depth and entry.is_dir():
                    _walk(entry, depth + 1)
            except (PermissionError, OSError):
                continue

    _walk(root, 0)
    results.sort(key=lambda f: f.full_path)
    return results