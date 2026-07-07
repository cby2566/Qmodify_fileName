from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
from models.rule_models import RenameRule
from services import rename_service, log_service
import datetime

router = APIRouter(prefix="/rename", tags=["rename"])


class PreviewRequest(BaseModel):
    files: List[str]
    rules: List[RenameRule]
    regex_pattern: Optional[str] = None


class ExecuteRequest(BaseModel):
    operations: List[dict]
    directory: str = ""


@router.post("/preview")
def preview(req: PreviewRequest):
    try:
        rules = [rule.model_dump(exclude_none=True) for rule in req.rules]
        return rename_service.generate_preview(
            files=req.files,
            rules=rules,
            regex_pattern=req.regex_pattern,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/execute")
def execute(req: ExecuteRequest):
    batch_id, results = rename_service.execute_rename(req.operations)
    log_service.log_batch(batch_id, results, directory=req.directory)
    succeeded = sum(1 for r in results if r["status"] == "success")
    failed = sum(1 for r in results if r["status"] != "success")
    return {
        "batch_id": batch_id,
        "total": len(results),
        "succeeded": succeeded,
        "failed": failed,
        "results": results,
    }


@router.get("/history")
def history():
    """Get operation batch history."""
    batches = log_service.get_all_batches()
    return {"batches": batches}


@router.get("/batch/{batch_id}")
def get_batch(batch_id: str):
    """Get details of a specific operation batch."""
    batch = log_service.get_batch(batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    return batch


@router.post("/undo/{batch_id}")
def undo(batch_id: str):
    """Undo a rename batch by reversing the operations."""
    batch = log_service.get_batch(batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    results = []
    for op in reversed(batch.get("operations", [])):
        from pathlib import Path
        src = Path(op["new_path"])
        dst = Path(op["original_path"])
        if src.exists() and not dst.exists():
            try:
                src.rename(dst)
                results.append({"status": "success", "original_path": op["original_path"], "new_path": op["new_path"]})
            except Exception as e:
                results.append({"status": "failed", "error": str(e), "original_path": op["original_path"], "new_path": op["new_path"]})
        else:
            results.append({"status": "skipped", "reason": "file_missing_or_target_exists", "original_path": op["original_path"], "new_path": op["new_path"]})
    
    # Log the undo operation
    log_service.log_batch(f"undo_{batch_id}", results, directory=batch.get("directory", ""))
    
    succeeded = sum(1 for r in results if r["status"] == "success")
    failed = sum(1 for r in results if r["status"] == "failed")
    return {"batch_id": batch_id, "succeeded": succeeded, "failed": failed, "results": results}
