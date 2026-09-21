from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import asyncio
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
            target_type=req.target_type,
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


class DirSizeRequest(BaseModel):
    paths: List[str]


@router.post("/dir-size")
async def dir_size(req: DirSizeRequest):
    """Calculate sizes for a batch of directories on demand.

    Kept separate from /scan so that the expensive recursive walk only runs
    when the user explicitly asks for it, for the directories they can see.

    Declared async and offloaded with to_thread: the walk is blocking IO, and
    on a single uvicorn worker running it inline would stall every other
    request (settings polling, progress checks) until the last folder is done.
    """
    results = await asyncio.to_thread(file_service.calculate_dir_sizes, req.paths)
    return {"results": results}
