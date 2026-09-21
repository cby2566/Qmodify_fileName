from pathlib import Path
from typing import List, Optional
import datetime
from models.file_models import FileInfo

# Directories that are almost never meant to be renamed in bulk.
SKIPPED_DIR_NAMES = {
    ".git", ".svn", ".hg",
    "node_modules", "__pycache__", ".venv", "venv",
    "$recycle.bin", "system volume information",
    ".idea", ".vscode", ".cache", ".pytest_cache",
}

# Directory size is not measured during scan (recursive stat is too slow);
# it is surfaced as a placeholder instead.
DIR_SIZE_PLACEHOLDER = "—"


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


def _should_skip_dir(name: str) -> bool:
    """Skip system / dependency directories that must not be renamed."""
    if name.startswith("."):
        return True
    return name.lower() in SKIPPED_DIR_NAMES


def scan_directory(
    path: str,
    extensions: Optional[List[str]] = None,
    recursive: bool = False,
    max_depth: int = 5,
    target_type: str = "file",
) -> List[FileInfo]:
    """Recursively or non-recursively scan a directory for entries.

    ``target_type`` selects what is collected:
      - ``file``: files only (default, backward compatible)
      - ``dir`` : directories only
      - ``all`` : files and directories
    Extension filtering only applies to files; directories always pass.
    """
    root = Path(path)
    if not root.exists():
        raise FileNotFoundError(f"Directory not found: {path}")
    if not root.is_dir():
        raise NotADirectoryError(f"Not a directory: {path}")

    if extensions:
        ext_set = {e.lower() if e.startswith(".") else f".{e.lower()}" for e in extensions}
    else:
        ext_set = None

    want_files = target_type in ("file", "all")
    want_dirs = target_type in ("dir", "all")

    results: List[FileInfo] = []

    def _entry_info(entry: Path, is_dir: bool) -> FileInfo:
        if is_dir:
            stat = entry.stat()
            return FileInfo(
                filename=entry.name,
                stem=entry.name,
                extension="",
                size_bytes=0,
                size_display=DIR_SIZE_PLACEHOLDER,
                created_time=datetime.datetime.fromtimestamp(stat.st_ctime).isoformat(),
                modified_time=datetime.datetime.fromtimestamp(stat.st_mtime).isoformat(),
                full_path=str(entry.resolve()),
                parent_dir=str(entry.parent.resolve()),
                is_dir=True,
            )
        stat = entry.stat()
        return FileInfo(
            filename=entry.name,
            stem=entry.stem,
            extension=entry.suffix,
            size_bytes=stat.st_size,
            size_display=_human_size(stat.st_size),
            created_time=datetime.datetime.fromtimestamp(stat.st_ctime).isoformat(),
            modified_time=datetime.datetime.fromtimestamp(stat.st_mtime).isoformat(),
            full_path=str(entry.resolve()),
            parent_dir=str(entry.parent.resolve()),
            is_dir=False,
        )

    def _walk(current: Path, depth: int):
        try:
            entries = list(current.iterdir())
        except PermissionError:
            return
        for entry in entries:
            try:
                if entry.is_dir():
                    if want_dirs and not _should_skip_dir(entry.name):
                        results.append(_entry_info(entry, True))
                    if recursive and depth < max_depth:
                        _walk(entry, depth + 1)
                elif want_files and entry.is_file():
                    if ext_set is None or _match_extension(entry.name, ext_set):
                        results.append(_entry_info(entry, False))
            except (PermissionError, OSError):
                continue

    _walk(root, 0)
    results.sort(key=lambda f: f.full_path)
    return results
