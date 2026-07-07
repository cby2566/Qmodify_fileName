from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
from models.file_models import FileInfo
from services import regex_service

router = APIRouter(prefix="/regex", tags=["regex"])


class ExtractRequest(BaseModel):
    files: List[str]  # List of file paths
    pattern: str


class GroupRequest(BaseModel):
    files: List[str]  # List of file paths
    pattern: str
    field: str


class ValidateRequest(BaseModel):
    pattern: str


@router.post("/validate")
def validate(req: ValidateRequest):
    is_valid, err = regex_service.validate_pattern(req.pattern)
    return {"valid": is_valid, "error": err}


@router.post("/extract")
def extract(req: ExtractRequest):
    try:
        return regex_service.extract_fields(req.files, req.pattern)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/group")
def group(req: GroupRequest):
    try:
        extracted = regex_service.extract_fields(req.files, req.pattern)
        return regex_service.group_by_field(extracted, req.field)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
