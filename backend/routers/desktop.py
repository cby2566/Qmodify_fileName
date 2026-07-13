from fastapi import APIRouter
from pydantic import BaseModel

from services import desktop_service


router = APIRouter(prefix="/desktop", tags=["desktop"])


class PathSuggestionRequest(BaseModel):
    query: str = ""
    limit: int = 12


class ValidateDirectoryRequest(BaseModel):
    path: str


@router.get("/common-directories")
def common_directories():
    return {"directories": desktop_service.get_common_directories()}


@router.post("/path-suggestions")
def path_suggestions(req: PathSuggestionRequest):
    return {
        "suggestions": desktop_service.suggest_directories(
            query=req.query,
            limit=max(1, min(req.limit, 30)),
        )
    }


@router.post("/validate-directory")
def validate_directory(req: ValidateDirectoryRequest):
    return desktop_service.validate_directory(req.path)
