from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from services import favorites_service

router = APIRouter(prefix="/favorites", tags=["favorites"])


class FavoriteCreate(BaseModel):
    name: str
    pattern: str
    description: str = ""


class FavoriteUpdate(BaseModel):
    name: Optional[str] = None
    pattern: Optional[str] = None
    description: Optional[str] = None


@router.get("/")
def list_all():
    return favorites_service.list_favorites()


@router.get("/{favorite_id}")
def get_one(favorite_id: str):
    item = favorites_service.get_favorite(favorite_id)
    if not item:
        raise HTTPException(status_code=404, detail="Favorite not found")
    return item


@router.post("/")
def create(req: FavoriteCreate):
    return favorites_service.create_favorite(
        name=req.name, pattern=req.pattern, description=req.description
    )


@router.put("/{favorite_id}")
def update(favorite_id: str, req: FavoriteUpdate):
    updates = {k: v for k, v in req.model_dump().items() if v is not None}
    item = favorites_service.update_favorite(favorite_id, updates)
    if not item:
        raise HTTPException(status_code=404, detail="Favorite not found")
    return item


@router.delete("/{favorite_id}")
def delete(favorite_id: str):
    if not favorites_service.delete_favorite(favorite_id):
        raise HTTPException(status_code=404, detail="Favorite not found")
    return {"deleted": True}


@router.post("/{favorite_id}/touch")
def touch(favorite_id: str):
    item = favorites_service.touch_favorite(favorite_id)
    if not item:
        raise HTTPException(status_code=404, detail="Favorite not found")
    return item
