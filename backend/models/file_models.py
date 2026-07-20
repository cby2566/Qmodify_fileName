from pydantic import BaseModel
from typing import List, Optional


class FileInfo(BaseModel):
    filename: str
    stem: str
    extension: str
    size_bytes: int
    size_display: str
    created_time: str
    modified_time: str
    full_path: str
    parent_dir: str


class ScanRequest(BaseModel):
    path: str
    extensions: Optional[List[str]] = None
    recursive: bool = False
    max_depth: int = 5
