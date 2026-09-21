from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services import open_service

router = APIRouter(prefix="/open", tags=["open"])


class OpenRequest(BaseModel):
    file_path: str
    open_with: str = ""
    # Informational: the service resolves the real type from disk anyway.
    is_dir: bool = False


@router.post("/")
def open_file(req: OpenRequest):
    result = open_service.open_file(req.file_path, req.open_with, req.is_dir)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result
