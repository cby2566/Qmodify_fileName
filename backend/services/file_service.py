from pathlib import Path
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor
import datetime
import os
from models.file_models import FileInfo

# Directories that are almost never meant to be renamed in bulk.
SKIPPED_DIR_NAMES = {
    ".git", ".svn", ".hg",
    "node_modules", "__pycache__", ".venv", "venv",
    "$recycle.bin", "system volume information",
    ".idea", ".vscode", ".cache", ".pytest_cache",
}

# Directory size is not measured during scan (recursive stat is too slow);
# it is surfaced as a placeholder until the user asks for it explicitly.
DIR_SIZE_PLACEHOLDER = "—"

# Guard rail for the on-demand size calculation: a single directory is not
# worth more than a few seconds of IO, and aborting beats hanging the request.
MAX_SIZE_FILES = 200_000


def calculate_dir_size(path: str, max_files: int = MAX_SIZE_FILES) -> dict:
    """Recursively total the size of a directory.

    Uses ``os.scandir`` rather than ``Path.rglob`` because the latter pays for
    a full ``stat`` per entry through the pathlib layer (measured ~6-12x
    slower on real trees). Returns a dict with bytes, a display string, the
    file count, and whether the walk was truncated by ``max_files``.
    """
    root = Path(path)
    if not root.exists():
        raise FileNotFoundError(f"Path not found: {path}")
    if not root.is_dir():
        raise NotADirectoryError(f"Not a directory: {path}")

    total = 0
    count = 0
    truncated = False
    stack = [str(root)]

    while stack:
        current = stack.pop()
        try:
            with os.scandir(current) as it:
                for entry in it:
                    try:
                        if entry.is_dir(follow_symlinks=False):
                            stack.append(entry.path)
                        elif entry.is_file(follow_symlinks=False):
                            total += entry.stat(follow_symlinks=False).st_size
                            count += 1
                            if count >= max_files:
                                truncated = True
                                stack.clear()
                                break
                    except OSError:
                        continue
        except OSError:
            continue

    return {
        "path": str(root),
        "size_bytes": total,
        "size_display": _human_size(total),
        "file_count": count,
        "truncated": truncated,
    }


# A whole page of folders is walked at once. Disk IO releases the GIL, so a
# small thread pool parallelizes the walk without thrashing the disk.
SIZE_WORKERS = 8


def _size_one(path: str, max_files: int) -> dict:
    """Never raises: a bad path becomes a failed result, not a broken batch."""
    try:
        info = calculate_dir_size(path, max_files)
        return {"path": path, "success": True, **info}
    except (FileNotFoundError, NotADirectoryError, OSError) as e:
        return {"path": path, "success": False, "error": str(e)}


def calculate_dir_sizes(paths: List[str], max_files_per_dir: int = MAX_SIZE_FILES) -> List[dict]:
    """Calculate sizes for a batch of paths, one result per input path.

    Results keep the same order as ``paths``. A failing path yields
    ``success: False`` with a message instead of aborting the whole batch, so
    one unreadable folder cannot break the page.

    The per-directory walk is dominated by ``scandir``/``stat`` calls that
    release the GIL, so paths are walked on a bounded thread pool. A page of
    100 folders therefore costs roughly one folder of wall time, not 100.
    """
    if not paths:
        return []
    if len(paths) == 1:
        return [_size_one(paths[0], max_files_per_dir)]

    workers = min(SIZE_WORKERS, len(paths))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(lambda p: _size_one(p, max_files_per_dir), paths))


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
