"""
Pydantic schemas for the Authentication module (login, registration, user responses).
"""

from uuid import UUID
from pydantic import BaseModel, EmailStr


# ---------------------------------------------------------------------------
# Token / auth response
# ---------------------------------------------------------------------------

class Token(BaseModel):
    access_token: str
    token_type: str


class UserResponse(BaseModel):
    id: UUID
    email: str
    student_id: str | None = None
    name: str | None = None
    branch: str | None = None
    semester: int | None = None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Registration payload schemas
# ---------------------------------------------------------------------------

class SubjectRecord(BaseModel):
    subject_name: str
    subject_code: str
    credits: int
    marks_obtained: int | None = None
    total_marks: int = 100


class SemesterRecord(BaseModel):
    semester: int
    subjects: list[SubjectRecord]


class StudentRegistration(BaseModel):
    full_name: str
    email: EmailStr
    student_id: str
    password: str
    department: str
    batch_year: int
    current_semester: int
    academic_records: list[SemesterRecord]
