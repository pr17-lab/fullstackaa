from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime
from app.models.student_preference import StudentPreference
from .schemas import PreferenceCreate, PreferenceUpdate

def get_preferences(db: Session, user_id: UUID) -> StudentPreference:
    return db.query(StudentPreference).filter(StudentPreference.user_id == user_id).first()

def create_preferences(db: Session, user_id: UUID, data: PreferenceCreate) -> StudentPreference:
    db_pref = get_preferences(db, user_id)
    if db_pref:
        return db_pref
    
    db_pref = StudentPreference(
        user_id=user_id,
        target_roles=data.target_roles,
        preferred_domains=data.preferred_domains,
        open_to_remote=data.open_to_remote,
        career_transition=data.career_transition,
        transition_from=data.transition_from,
        transition_to=data.transition_to,
        timeline_months=data.timeline_months,
        experience_level=data.experience_level
    )
    db.add(db_pref)
    db.commit()
    db.refresh(db_pref)
    return db_pref

def update_preferences(db: Session, user_id: UUID, data: PreferenceUpdate) -> StudentPreference:
    db_pref = get_preferences(db, user_id)
    if not db_pref:
        # Upsert behavior
        return create_preferences(db, user_id, PreferenceCreate(**data.model_dump()))
        
    for key, value in data.model_dump().items():
        setattr(db_pref, key, value)
    
    db.commit()
    db.refresh(db_pref)
    return db_pref
