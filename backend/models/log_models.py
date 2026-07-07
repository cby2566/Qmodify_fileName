from pydantic import BaseModel
from typing import List, Optional, Literal


class LogEntry(BaseModel):
    id: Optional[int] = None
    batch_id: str
    original_path: str
    new_path: str
    status: Literal["success", "failed", "rollback"]
    message: Optional[str] = None
    created_at: str


class OperationBatch(BaseModel):
    batch_id: str
    directory: str
    total: int
    succeeded: int
    failed: int
    created_at: str
    operations: List[LogEntry]


class LogQueryRequest(BaseModel):
    page: int = 1
    page_size: int = 20
    batch_id: Optional[str] = None
    status: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
