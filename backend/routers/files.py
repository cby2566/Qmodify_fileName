from fastapi import APIRouter, HTTPException
from typing import List, Optional
from models.file_models import ScanRequest, FileInfo
from services import file_service, filter_service

router = APIRouter(prefix="/files", tags=["files"])


@router.post("/scan", response_model=List[FileInfo])
def scan_directory(req: ScanRequest):
    try:
        return file_service.scan_directory(
            path=req.path,
            extensions=req.extensions,
            recursive=req.recursive,
            max_depth=req.max_depth,
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except NotADirectoryError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post("/filter")
def filter_files(payload: dict):
    """Body: {"files": [FileInfo...], "filters": {...}}"""
    files = payload.get("files", [])
    filters = payload.get("filters", {})
    file_objs = [FileInfo(**f) for f in files]
    try:
        filtered = filter_service.filter_files(file_objs, filters)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return filtered
