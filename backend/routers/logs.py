from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from services import log_service

router = APIRouter(prefix="/logs", tags=["logs"])


@router.get("/")
def list_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    batch_id: Optional[str] = None,
    status: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
):
    filters = {k: v for k, v in {
        "batch_id": batch_id,
        "status": status,
        "date_from": date_from,
        "date_to": date_to,
    }.items() if v is not None}
    rows, total = log_service.get_logs(page=page, page_size=page_size, filters=filters)
    return {"total": total, "page": page, "page_size": page_size, "items": rows}


@router.get("/batch/{batch_id}")
def get_batch(batch_id: str):
    batch = log_service.get_batch(batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    return batch


@router.delete("/")
def clear(older_than_days: Optional[int] = None):
    count = log_service.clear_logs(older_than_days=older_than_days)
    return {"deleted": count}
