from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services import open_service

router = APIRouter(prefix="/open", tags=["open"])


class OpenRequest(BaseModel):
    file_path: str
    open_with: str = ""


@router.post("/")
def open_file(req: OpenRequest):
    result = open_service.open_file(req.file_path, req.open_with)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result
