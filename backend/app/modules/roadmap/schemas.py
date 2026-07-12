from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
from datetime import datetime

class RoadmapTaskResponse(BaseModel):
    id: UUID
    roadmap_id: UUID
    phase: str
    task_type: str
    title: str
    description: Optional[str]
    resource_url: Optional[str]
    platform: Optional[str]
    estimated_hours: int
    order_index: int
    status: str
    completed_at: Optional[datetime]
    feedback_score: Optional[int]
    skill_name: Optional[str] = None
    associated_skill_id: Optional[UUID] = None
    submission_link: Optional[str] = None
    validation_status: Optional[str] = None
    resource_source: Optional[str] = None
    learning_resource_id: Optional[UUID] = None
    upvotes: Optional[int] = 0
    downvotes: Optional[int] = 0
    depth_verified: Optional[bool] = False
    project_id: Optional[UUID] = None
    
    class Config:
        from_attributes = True

class RoadmapSummary(BaseModel):
    id: UUID
    job_role: str
    version: int
    status: str
    completion_percentage: float
    created_at: datetime
    
    class Config:
        from_attributes = True

class RoadmapResponse(RoadmapSummary):
    user_id: UUID
    is_transition: bool
    generated_by: Optional[str] = None
    total_tasks: int
    completed_tasks: int
    updated_at: datetime
    tasks: List[RoadmapTaskResponse]
    projected_completion_weeks: Optional[float] = None
    pacing_status: Optional[str] = None

class GenerateRoadmapRequest(BaseModel):
    job_role: str

class TaskCompleteRequest(BaseModel):
    feedback_score: Optional[int] = None
    submission_link: Optional[str] = None

class CustomTaskCreate(BaseModel):
    title: str
    platform: Optional[str] = None
    estimated_hours: int = 1
    resource_url: Optional[str] = None
    phase: str

class TaskStatusUpdate(BaseModel):
    status: str

class ResourceVoteRequest(BaseModel):
    vote_type: str # 'upvote' or 'downvote'

