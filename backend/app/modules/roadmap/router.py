from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List

from app.api.dependencies.database import get_db
from app.api.dependencies.auth import get_current_user
from app.models.user import User
from app.models.roadmap import RoadmapTask
from app.modules.skills.service import verify_github_complexity_async

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
async def complete_roadmap_task(
    task_id: UUID,
    req: schemas.TaskCompleteRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark a task as completed and optionally leave feedback or trigger validation for apply tasks"""
    task = db.query(RoadmapTask).filter(RoadmapTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.phase == "apply":
        if task.associated_skill_id:
            incomplete_siblings = []
            siblings = (
                db.query(RoadmapTask)
                .filter(
                    RoadmapTask.roadmap_id == task.roadmap_id,
                    RoadmapTask.associated_skill_id == task.associated_skill_id,
                    RoadmapTask.phase.in_(["learn", "practice"]),
                    RoadmapTask.status != "completed"
                )
                .all()
            )
            has_attempts = False
            best_score = 0.0
            for sib in siblings:
                if sib.phase == "practice":
                    from app.models.interview import InterviewSession
                    completed_interview_exists = False
                    sessions = (
                        db.query(InterviewSession)
                        .filter(
                            InterviewSession.user_id == current_user.id,
                            InterviewSession.associated_skill_id == task.associated_skill_id,
                            InterviewSession.status == "completed"
                        )
                        .all()
                    )
                    for s in sessions:
                        if s.questions and all(q.ai_score is not None for q in s.questions):
                            scores = [int(q.ai_score) for q in s.questions]
                            avg = sum(scores) / len(scores) if scores else 0.0
                            has_attempts = True
                            if avg > best_score:
                                best_score = avg
                            if avg >= 7.0:
                                completed_interview_exists = True
                                break
                    if completed_interview_exists:
                        sib.status = "completed"
                        sib.validation_status = "verified"
                        from datetime import datetime
                        sib.completed_at = datetime.utcnow()
                        db.commit()
                        continue
                incomplete_siblings.append(sib)

            if incomplete_siblings:
                from app.models.skill_taxonomy import SkillTaxonomy
                skill_name = "the skill"
                skill_tax = db.query(SkillTaxonomy).filter(SkillTaxonomy.id == task.associated_skill_id).first()
                if skill_tax:
                    skill_name = skill_tax.skill_name
                
                if has_attempts and best_score < 7.0:
                    detail_msg = f"You scored {round(best_score, 1)}/10 on this practice interview. Score 7+ to unlock the next step, or retry when ready."
                else:
                    detail_msg = f"Complete the Learn/Practice steps for {skill_name} before starting this Apply task."
                
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=detail_msg
                )

    if task.task_type == "apply" or task.phase == "apply" or task.task_type == "project":
        if not req.submission_link:
            raise HTTPException(
                status_code=400,
                detail="Submission link is required for 'apply' tasks."
            )
        if "github.com" not in req.submission_link.lower():
            raise HTTPException(
                status_code=400,
                detail="repo_url must contain github.com"
            )
        
        # Save submission link and mark validation_status = 'pending'
        task.submission_link = req.submission_link
        task.validation_status = "pending"
        db.commit()

        background_tasks.add_task(
            verify_github_complexity_async,
            req.submission_link,
            current_user.id,
            db,
            task.id
        )
        return {
            "status": "pending",
            "message": "Project submission queued for asynchronous GitHub verification and ingestion."
        }
    else:
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

@router.post("/tasks/{task_id}/vote")
def vote_roadmap_task_resource(
    task_id: UUID,
    req: schemas.ResourceVoteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upvote or downvote the learning resource of a roadmap task"""
    task = db.query(RoadmapTask).filter(RoadmapTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Roadmap task not found")
    if not task.resource_url:
        raise HTTPException(status_code=400, detail="This task does not have an associated resource URL to vote on")

    from app.models.learning_resource import LearningResource

    # 1. If it has a learning_resource_id: update it directly
    if task.learning_resource_id:
        lr = db.query(LearningResource).filter(LearningResource.id == task.learning_resource_id).first()
        if lr:
            if req.vote_type == "upvote":
                lr.upvotes += 1
            elif req.vote_type == "downvote":
                lr.downvotes += 1
            db.commit()
            return {"status": "success", "message": "Vote recorded for curated resource.", "upvotes": lr.upvotes, "downvotes": lr.downvotes}

    # 2. Otherwise (AI-suggested resource):
    # Check if a learning resource with this URL already exists for the skill
    lr = db.query(LearningResource).filter(
        LearningResource.skill_id == task.skill_id,
        LearningResource.resource_url == task.resource_url
    ).first()

    if not lr:
        # Create a new learning resource entry
        lr = LearningResource(
            skill_id=task.skill_id,
            title=task.title,
            resource_url=task.resource_url,
            platform=task.platform or "Unverified Site",
            phase=task.phase,
            upvotes=1 if req.vote_type == "upvote" else 0,
            downvotes=1 if req.vote_type == "downvote" else 0
        )
        db.add(lr)
        db.flush() # get ID
    else:
        if req.vote_type == "upvote":
            lr.upvotes += 1
        elif req.vote_type == "downvote":
            lr.downvotes += 1

    # Link the task to this learning resource
    task.learning_resource_id = lr.id
    task.resource_source = "curated" # promotes it to curated/verified status!
    db.commit()

    return {"status": "success", "message": "AI resource promoted to curated database.", "upvotes": lr.upvotes, "downvotes": lr.downvotes}

