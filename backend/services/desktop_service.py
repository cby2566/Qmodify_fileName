import platform
from pathlib import Path
from typing import List, Optional


def get_common_directories() -> List[dict]:
    """Return useful local directory shortcuts for the path input."""
    home = Path.home()
    candidates = [
        ("用户目录", home),
        ("桌面", home / "Desktop"),
        ("下载", home / "Downloads"),
        ("文档", home / "Documents"),
        ("图片", home / "Pictures"),
        ("音乐", home / "Music"),
        ("视频", home / "Videos"),
    ]

    shortcuts = [
        {"label": label, "path": str(path), "kind": "shortcut"}
        for label, path in candidates
        if path.exists() and path.is_dir()
    ]

    if platform.system() == "Windows":
        shortcuts.extend(
            {"label": f"{drive} 盘", "path": drive, "kind": "drive"}
            for drive in _windows_drives()
        )

    return shortcuts


def validate_directory(path: str) -> dict:
    target = _resolve_user_path(path)
    if not target:
        return {"exists": False, "is_directory": False, "message": "请输入目录路径"}

    p = Path(target)
    if not p.exists():
        return {"exists": False, "is_directory": False, "message": "目录不存在"}
    if not p.is_dir():
        return {"exists": True, "is_directory": False, "message": "路径不是目录"}
    return {
        "exists": True,
        "is_directory": True,
        "message": "目录可用",
        "path": str(p.resolve()),
    }


def suggest_directories(query: str = "", limit: int = 12) -> List[dict]:
    query = _resolve_user_path(query)
    suggestions = []

    if not query:
        return [
            {"value": item["path"], "label": item["label"], "kind": item["kind"]}
            for item in get_common_directories()[:limit]
        ]

    lower_query = query.lower()
    for item in get_common_directories():
        if item["path"].lower().startswith(lower_query) or item["label"].lower().startswith(lower_query):
            suggestions.append({"value": item["path"], "label": item["label"], "kind": item["kind"]})

    base, prefix = _suggestion_base_and_prefix(query)
    if base and base.exists() and base.is_dir():
        try:
            entries = sorted(
                (entry for entry in base.iterdir() if entry.is_dir() and entry.name.lower().startswith(prefix.lower())),
                key=lambda entry: entry.name.lower(),
            )
        except (PermissionError, OSError):
            entries = []

        for entry in entries:
            suggestions.append({
                "value": str(entry.resolve()),
                "label": entry.name,
                "kind": "directory",
            })

    deduped = []
    seen = set()
    for item in suggestions:
        key = item["value"].lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
        if len(deduped) >= limit:
            break
    return deduped


def _resolve_user_path(path: Optional[str]) -> str:
    if not path:
        return ""
    return str(Path(str(path).strip().strip('"')).expanduser())


def _suggestion_base_and_prefix(query: str) -> tuple[Optional[Path], str]:
    normalized = query.replace("/", "\\") if platform.system() == "Windows" else query

    if platform.system() == "Windows":
        if len(normalized) == 1 and normalized.isalpha():
            return None, normalized
        if len(normalized) == 2 and normalized[1] == ":":
            return Path(f"{normalized}\\"), ""

    if normalized.endswith(("\\", "/")):
        return Path(normalized), ""

    path = Path(normalized)
    if path.is_absolute() or path.drive:
        return path.parent, path.name

    return Path.home(), normalized


def _windows_drives() -> List[str]:
    if platform.system() != "Windows":
        return []
    try:
        import ctypes

        bitmask = ctypes.windll.kernel32.GetLogicalDrives()
        drives = []
        for index, letter in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
            if bitmask & (1 << index):
                drives.append(f"{letter}:\\")
        return drives
    except Exception:
        return [f"{letter}:\\" for letter in "CDEFGHIJKLMNOPQRSTUVWXYZ" if Path(f"{letter}:\\").exists()]
