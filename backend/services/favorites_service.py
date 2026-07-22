import json
import uuid
import datetime
import os
from pathlib import Path
from typing import List, Optional, Dict, Any

# 支持环境变量配置数据目录（桌面模式），默认为 backend/data/
_data_dir = os.environ.get("FILERENAMER_DATA_DIR")
if _data_dir:
    DATA_PATH = Path(_data_dir) / "favorites.json"
else:
    DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "favorites.json"


def _load() -> List[dict]:
    if not DATA_PATH.exists():
        return []
    try:
        return json.loads(DATA_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []


def _save(items: List[dict]):
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    DATA_PATH.write_text(
        json.dumps(items, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def list_favorites() -> List[dict]:
    return _load()


def get_favorite(favorite_id: str) -> Optional[dict]:
    for item in _load():
        if item.get("id") == favorite_id:
            return item
    return None


def create_favorite(
    name: str,
    pattern: str,
    description: str = "",
) -> dict:
    now = datetime.datetime.now().isoformat()
    item = {
        "id": uuid.uuid4().hex,
        "name": name,
        "pattern": pattern,
        "description": description,
        "created_at": now,
        "last_used_at": None,
    }
    items = _load()
    items.append(item)
    _save(items)
    return item


def update_favorite(favorite_id: str, updates: Dict[str, Any]) -> Optional[dict]:
    items = _load()
    for item in items:
        if item.get("id") == favorite_id:
            for k, v in updates.items():
                if k in ("name", "pattern", "description"):
                    item[k] = v
            _save(items)
            return item
    return None


def delete_favorite(favorite_id: str) -> bool:
    items = _load()
    new_items = [i for i in items if i.get("id") != favorite_id]
    if len(new_items) == len(items):
        return False
    _save(new_items)
    return True


def touch_favorite(favorite_id: str) -> Optional[dict]:
    """Update last_used_at timestamp."""
    items = _load()
    for item in items:
        if item.get("id") == favorite_id:
            item["last_used_at"] = datetime.datetime.now().isoformat()
            _save(items)
            return item
    return None
