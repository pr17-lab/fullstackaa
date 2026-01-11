from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
import uuid

# Subject Schemas
class SubjectBase(BaseModel):
    subject_name: str = Field(..., min_length=1, max_length=255)
    subject_code: str = Field(..., min_length=1, max_length=50)
    credits: int = Field(..., ge=1, le=10)
    marks: Decimal = Field(..., ge=0, le=100, decimal_places=2)
    grade: str = Field(..., pattern="^[A-F][+-]?$", description="Grade (A+, A, B+, etc.)")

class SubjectCreate(SubjectBase):
    term_id: uuid.UUID

class SubjectUpdate(BaseModel):
    subject_name: Optional[str] = Field(None, min_length=1, max_length=255)
    subject_code: Optional[str] = Field(None, min_length=1, max_length=50)
    credits: Optional[int] = Field(None, ge=1, le=10)
    marks: Optional[Decimal] = Field(None, ge=0, le=100)
    grade: Optional[str] = Field(None, pattern="^[A-F][+-]?$")

class SubjectResponse(SubjectBase):
    id: uuid.UUID
    term_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Academic Term Schemas
class AcademicTermBase(BaseModel):
    semester: int = Field(..., ge=1, le=10)
    year: int = Field(..., ge=2000, le=2100)
    gpa: Decimal = Field(..., ge=0, le=10, decimal_places=2)

class AcademicTermCreate(AcademicTermBase):
    user_id: uuid.UUID
    subjects: List[SubjectBase] = []

class AcademicTermUpdate(BaseModel):
    semester: Optional[int] = Field(None, ge=1, le=10)
    year: Optional[int] = Field(None, ge=2000, le=2100)
    gpa: Optional[Decimal] = Field(None, ge=0, le=10)

class AcademicTermResponse(AcademicTermBase):
    id: uuid.UUID
    user_id: uuid.UUID
    subjects: List[SubjectResponse] = []
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Academic Record Summary
class AcademicRecordSummary(BaseModel):
    student_id: uuid.UUID
    total_terms: int
    overall_gpa: Decimal
    total_credits: int
    terms: List[AcademicTermResponse]
