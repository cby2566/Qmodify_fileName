import json
import os
from pathlib import Path
from typing import Optional, Dict, Any, List

# 支持环境变量配置数据目录（桌面模式），默认为 backend/data/
_data_dir = os.environ.get("FILERENAMER_DATA_DIR")
if _data_dir:
    DATA_PATH = Path(_data_dir) / "settings.json"
else:
    DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "settings.json"

DEFAULTS: Dict[str, Any] = {
    "available_extensions": [".txt", ".zip", ".rar", ".7z"],
    "target_extensions": [".txt", ".zip", ".rar", ".7z"],
    "default_recursive": False,
    "max_scan_depth": 5,
    "log_retention_days": 30,
    "preview_debounce_ms": 300,
    "open_with": "",
}


def _normalize(data: Dict[str, Any]) -> Dict[str, Any]:
    # Ensure target ⊆ available: drop targets without a source entry.
    avail = set(data.get("available_extensions", []))
    data["target_extensions"] = [
        t for t in data.get("target_extensions", []) if t in avail
    ]
    if "available_extensions" not in data:
        data["available_extensions"] = list(DEFAULTS["available_extensions"])
    return data


def _load() -> Dict[str, Any]:
    if not DATA_PATH.exists():
        return _normalize(dict(DEFAULTS))
    try:
        data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
        merged = dict(DEFAULTS)
        merged.update(data)
        return _normalize(merged)
    except (json.JSONDecodeError, OSError):
        return _normalize(dict(DEFAULTS))


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
    _normalize(current)
    _save(current)
    return current


def reset_settings() -> Dict[str, Any]:
    _save(dict(DEFAULTS))
    return dict(DEFAULTS)
