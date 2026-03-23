from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.dependencies.database import get_db
from app.api.dependencies.auth import get_current_user
from app.models.user import User

from . import schemas, service

router = APIRouter()

@router.get("", response_model=schemas.PreferenceResponse)
def get_my_preferences(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    pref = service.get_preferences(db, current_user.id)
    if not pref:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Preferences not found")
    return pref

@router.post("", response_model=schemas.PreferenceResponse)
def create_my_preferences(
    data: schemas.PreferenceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    pref = service.get_preferences(db, current_user.id)
    if pref:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Preferences already exist")
    return service.create_preferences(db, current_user.id, data)

@router.put("", response_model=schemas.PreferenceResponse)
def update_my_preferences(
    data: schemas.PreferenceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return service.update_preferences(db, current_user.id, data)
