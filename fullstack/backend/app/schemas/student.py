from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import uuid

# Student Profile Schemas
class StudentProfileBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    branch: str = Field(..., min_length=1, max_length=100)
    semester: int = Field(..., ge=1, le=10, description="Semester number (1-10)")
    interests: Optional[str] = None

class StudentProfileCreate(StudentProfileBase):
    user_id: uuid.UUID

class StudentProfileUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    branch: Optional[str] = Field(None, min_length=1, max_length=100)
    semester: Optional[int] = Field(None, ge=1, le=10)
    interests: Optional[str] = None

class StudentProfileResponse(StudentProfileBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# List/Pagination Schemas
class StudentListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    students: list[StudentProfileResponse]
