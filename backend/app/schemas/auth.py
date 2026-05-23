"""
Pydantic schemas for the Authentication module (login, registration, user responses).
"""

from uuid import UUID
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


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
# Self-service update schemas
# ---------------------------------------------------------------------------

class UpdateProfileRequest(BaseModel):
    """Payload for PATCH /auth/me — student updates their own profile."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    semester: Optional[int] = Field(None, ge=1, le=8)


class ChangePasswordRequest(BaseModel):
    """Payload for PUT /auth/change-password."""
    current_password: str
    new_password: str = Field(..., min_length=8)


# ---------------------------------------------------------------------------
# Registration payload schemas
# ---------------------------------------------------------------------------

class StudentRegistration(BaseModel):
    full_name: str
    email: EmailStr
    student_id: str | None = None
    password: str
    department: str
    batch_year: int
    current_semester: int
