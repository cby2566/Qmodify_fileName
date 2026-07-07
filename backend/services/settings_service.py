import json
from pathlib import Path
from typing import Optional, Dict, Any

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "settings.json"

DEFAULTS = {
    "target_extensions": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz", ".tar.gz", ".tar.bz2", ".tar.xz"],
    "default_recursive": False,
    "max_scan_depth": 5,
    "log_retention_days": 30,
    "preview_debounce_ms": 300,
    "open_with": "",
}


def _load() -> Dict[str, Any]:
    if not DATA_PATH.exists():
        return dict(DEFAULTS)
    try:
        data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
        merged = dict(DEFAULTS)
        merged.update(data)
        return merged
    except (json.JSONDecodeError, OSError):
        return dict(DEFAULTS)


def _save(data: Dict[str, Any]):
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    DATA_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def get_settings() -> Dict[str, Any]:
    return _load()


def update_settings(updates: Dict[str, Any]) -> Dict[str, Any]:
    current = _load()
    for k, v in updates.items():
        if k in DEFAULTS:
            current[k] = v
    _save(current)
    return current


def reset_settings() -> Dict[str, Any]:
    _save(dict(DEFAULTS))
    return dict(DEFAULTS)
