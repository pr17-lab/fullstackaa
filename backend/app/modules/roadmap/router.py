from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List

from app.api.dependencies.database import get_db
from app.api.dependencies.auth import get_current_user
from app.models.user import User

from . import schemas, service

router = APIRouter()

@router.get("", response_model=List[schemas.RoadmapSummary])
def list_roadmaps(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all roadmaps summary list for current user"""
    return service.get_roadmaps(db, current_user.id)

@router.post("/generate", response_model=schemas.RoadmapResponse)
async def generate_my_roadmap(
    req: schemas.GenerateRoadmapRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate a dynamic roadmap matching current skills gap"""
    return await service.generate_roadmap(db, current_user.id, req.job_role)

@router.get("/{roadmap_id}", response_model=schemas.RoadmapResponse)
def get_roadmap_details(
    roadmap_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get entire roadmap details with all sorted tasks"""
    return service.get_roadmap(db, current_user.id, roadmap_id)

@router.post("/tasks/{task_id}/complete")
def complete_roadmap_task(
    task_id: UUID,
    req: schemas.TaskCompleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark a task as completed and optionally leave feedback"""
    # Return raw dict/response or just trigger service.
    # Service returns full list currently but we can just bypass standard return or fetch the single task:
    service.complete_task(db, current_user.id, task_id, req.feedback_score)
    return {"status": "success", "message": "Task completed successfully"}

@router.post("/tasks/{task_id}/skip")
def skip_roadmap_task(
    task_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Skip a task without completing it"""
    service.skip_task(db, current_user.id, task_id)
    return {"status": "success", "message": "Task skipped successfully"}

@router.post("/{roadmap_id}/tasks/custom", response_model=schemas.RoadmapTaskResponse)
def add_custom_roadmap_task(
    roadmap_id: UUID,
    req: schemas.CustomTaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a custom task to the roadmap"""
    return service.add_custom_task(
        db, current_user.id, roadmap_id, 
        req.title, req.platform, req.estimated_hours, req.resource_url, req.phase
    )

@router.patch("/tasks/{task_id}/status", response_model=schemas.RoadmapTaskResponse)
def update_roadmap_task_status(
    task_id: UUID,
    req: schemas.TaskStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update task status (e.g., from dragging in Kanban)"""
    return service.update_task_status(db, current_user.id, task_id, req.status)

@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_custom_roadmap_task(
    task_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a custom task from the roadmap"""
    service.delete_custom_task(db, current_user.id, task_id)
    return None

@router.delete("/{roadmap_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_roadmap(
    roadmap_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a roadmap and all its tasks"""
    service.delete_roadmap(db, current_user.id, roadmap_id)
    return None
