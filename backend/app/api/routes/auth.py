"""
Authentication API routes for login and user management.
"""

from datetime import timedelta
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.core.config import settings
from app.core.security import verify_password, create_access_token
from app.models.user import User
from app.models.student_profile import StudentProfile
from app.api.dependencies.database import get_db
from app.api.dependencies.auth import get_current_user
from pydantic import BaseModel


router = APIRouter(tags=["Authentication"])

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Schemas
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
    
    model_config = {
        "from_attributes": True
    }

@router.post("/login", response_model=Token)
@limiter.limit("5/minute")
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Login endpoint - authenticate user and return JWT token.
    
    Username should be student_id (e.g., "S00001").
    Password will be verified against hashed password in database.
    
    Rate limited to 5 requests per minute per IP address.
    """
    # Find user by student_id
    user = db.query(User).filter(User.student_id == form_data.username).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect student ID or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if account is locked
    if user.is_locked():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account is locked due to too many failed login attempts. Please try again later.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify password
    if not user.password_hash or not verify_password(form_data.password, user.password_hash):
        # Record failed login attempt
        user.record_failed_login()
        db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect student ID or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Reset failed attempts on successful login
    user.reset_failed_attempts()
    db.commit()
    
    # Create access token (still use email as subject for backwards compatibility with tokens)
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "user_id":str(user.id), "student_id": user.student_id},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current authenticated user with profile information."""
    # Load student profile to get name, branch, and semester
    profile = db.query(StudentProfile).filter(
        StudentProfile.user_id == current_user.id
    ).first()
    
    return {
        "id": current_user.id,
        "email": current_user.email,
        "student_id": current_user.student_id,
        "name": profile.name if profile else None,
        "branch": profile.branch if profile else None,
        "semester": profile.semester if profile else None
    }
