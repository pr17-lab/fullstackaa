from typing import List, Optional
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

class SkillResponse(BaseModel):
    skill_id: UUID
    skill_name: str
    category: str
    confidence_score: float
    level: str
    source: List[str]
    last_computed_at: Optional[datetime]

    class Config:
        from_attributes = True

class SkillGapResponse(BaseModel):
    job_role: str
    match_score: float
    match_label: str
    missing_skills: List[dict]
    weak_skills: List[dict]
    strong_skills: List[dict]
    high_potential_skills: List[dict] = []
    computed_at: Optional[datetime]
    requirements_last_reviewed: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class StudentSkillSummary(BaseModel):
    total_skills: int
    strong_count: int
    moderate_count: int
    weak_count: int
    top_skills: List[SkillResponse]
    skill_gaps: List[SkillGapResponse]

class ManualSkillCreate(BaseModel):
    skill_name: str
    confidence_score: float

class TaxonomySearchResponse(BaseModel):
    id: UUID
    skill_name: str
    category: str
