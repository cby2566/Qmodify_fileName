from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
from services import export_service

router = APIRouter(prefix="/export", tags=["export"])


class ExportRequest(BaseModel):
    data: List[dict]
    fields: Optional[List[str]] = None


@router.post("/csv")
def export_csv(req: ExportRequest):
    try:
        path = export_service.export_to_csv(req.data, req.fields)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return FileResponse(
        path, media_type="text/csv", filename="export.csv"
    )


@router.post("/txt")
def export_txt(req: ExportRequest):
    try:
        path = export_service.export_to_txt(req.data, req.fields)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return FileResponse(
        path, media_type="text/plain", filename="export.txt"
    )
