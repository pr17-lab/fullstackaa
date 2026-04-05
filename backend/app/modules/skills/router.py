from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List

from app.api.dependencies.database import get_db
from app.api.dependencies.auth import get_current_user
from app.models.user import User

from . import schemas, service

router = APIRouter(prefix="/api/skills", tags=["Skills"])

@router.get("/me", response_model=List[schemas.SkillResponse])
def get_my_skills(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all mapped skills for the current user."""
    return service.get_student_skills(db, current_user.id)

@router.get("/summary", response_model=schemas.StudentSkillSummary)
def get_my_skill_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get high-level dashboard metrics for the current user's career paths."""
    return service.get_skill_summary(db, current_user.id)

@router.get("/gaps", response_model=List[schemas.SkillGapResponse])
def get_my_skill_gaps(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get skill gaps matching the current user's target jobs."""
    return service.get_student_gaps(db, current_user.id)

@router.get("/gaps/{job_role}", response_model=schemas.SkillGapResponse)
def get_my_skill_gap_for_role(
    job_role: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a single skill gap alignment for a specific job profile."""
    gaps = service.get_student_gaps(db, current_user.id)
    for g in gaps:
        if g.job_role.lower() == job_role.lower():
            return g
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, 
        detail=f"No gap analysis found for role {job_role}"
    )

@router.get("/recommendation")
def career_recommendation(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get the primary and alternative career recommendations for the user."""
    return service.get_career_recommendation(db, current_user.id)

@router.get("/taxonomy/search", response_model=List[schemas.TaxonomySearchResponse])
def search_skills_taxonomy(
    query: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search the skills taxonomy for dropdown population."""
    if not query.strip(): return []
    return service.search_taxonomy(db, query.strip())

@router.post("/manual", response_model=schemas.SkillResponse)
def add_manual_skill(
    payload: schemas.ManualSkillCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add or upweight a self-reported skill."""
    return service.add_manual_skill(
        db=db, 
        user_id=current_user.id, 
        skill_name=payload.skill_name.strip(), 
        confidence_score=payload.confidence_score
    )

@router.delete("/manual/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_manual_skill(
    skill_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove a self-reported skill source."""
    service.remove_manual_skill(db=db, user_id=current_user.id, skill_id=skill_id)
    return None
