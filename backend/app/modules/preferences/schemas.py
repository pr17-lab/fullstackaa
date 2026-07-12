from typing import List, Optional
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

class PreferenceBase(BaseModel):
    target_roles: List[str]
    preferred_domains: Optional[List[str]] = None
    open_to_remote: bool
    career_transition: bool
    transition_from: Optional[str] = None
    transition_to: Optional[str] = None
    timeline_months: int
    experience_level: Optional[str] = None
    available_hours_per_week: Optional[int] = None
    onboarding_step: Optional[str] = "preferred_role_set"

class PreferenceCreate(PreferenceBase):
    pass

class PreferenceUpdate(PreferenceBase):
    pass

class PreferenceResponse(PreferenceBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
