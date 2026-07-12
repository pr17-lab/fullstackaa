"""
API routes for project complexity ingestion and verification.
"""

from typing import List, Optional
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, status, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, field_validator

from app.api.dependencies.database import get_db
from app.api.dependencies.auth import get_current_user
from app.models.user import User
from app.modules.skills.service import verify_github_complexity_async

router = APIRouter(prefix="/api/skills/project", tags=["Projects"])


class ProjectVerifyRequest(BaseModel):
    repo_url: str

    @field_validator("repo_url")
    @classmethod
    def validate_repo_url(cls, v: str) -> str:
        if "github.com" not in v.lower():
            raise ValueError("repo_url must contain github.com")
        return v


class ProjectResponse(BaseModel):
    id: UUID
    title: str
    repo_url: Optional[str] = None
    tech_stack: Optional[List[str]] = None
    extracted_skills: Optional[List[str]] = None
    depth_verified: bool
    calculated_complexity: Optional[int] = None
    analyzed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


@router.post("/verify", status_code=status.HTTP_202_ACCEPTED)
async def verify_project(
    payload: ProjectVerifyRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Queue an asynchronous analysis of a GitHub repository for technical complexity
    and skill extraction.
    """
    background_tasks.add_task(
        verify_github_complexity_async,
        payload.repo_url,
        current_user.id,
        db
    )
    return {
        "status": "processing",
        "message": "Repository analysis queued."
    }


@router.get("", response_model=List[ProjectResponse])
def get_my_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all projects for the current user.
    """
    from app.models.student_project import StudentProject
    return db.query(StudentProject).filter(StudentProject.user_id == current_user.id).order_by(StudentProject.created_at.desc()).all()
