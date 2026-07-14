from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional
from services import settings_service

router = APIRouter(prefix="/settings", tags=["settings"])


class SettingsUpdate(BaseModel):
    available_extensions: Optional[List[str]] = None
    target_extensions: Optional[List[str]] = None
    default_recursive: Optional[bool] = None
    max_scan_depth: Optional[int] = None
    log_retention_days: Optional[int] = None
    preview_debounce_ms: Optional[int] = None
    open_with: Optional[str] = None


@router.get("/")
def get():
    return settings_service.get_settings()


@router.put("/")
def update(req: SettingsUpdate):
    updates = {k: v for k, v in req.model_dump().items() if v is not None}
    return settings_service.update_settings(updates)


@router.post("/reset")
def reset():
    return settings_service.reset_settings()
