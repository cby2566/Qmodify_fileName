from pydantic import BaseModel
from typing import List, Literal, Optional


class FileInfo(BaseModel):
    filename: str
    stem: str
    extension: str
    size_bytes: int = 0
    size_display: str = ""
    created_time: str
    modified_time: str
    full_path: str
    parent_dir: str
    # True when the entry is a directory. Directories carry an empty
    # extension and are never split into stem + suffix while renaming.
    is_dir: bool = False


class ScanRequest(BaseModel):
    path: str
    extensions: Optional[List[str]] = None
    recursive: bool = False
    max_depth: int = 5
    # "file" -> files only (default, keeps old behaviour)
    # "dir"  -> directories only
    # "all"  -> both
    target_type: Literal["file", "dir", "all"] = "file"
