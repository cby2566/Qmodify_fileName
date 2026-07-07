from pydantic import BaseModel
from typing import List


class Settings(BaseModel):
    target_extensions: List[str] = [".txt", ".jpg", ".png", ".pdf", ".docx"]
    default_recursive: bool = False
    max_scan_depth: int = 5
    log_retention_days: int = 30
    preview_debounce_ms: int = 300
