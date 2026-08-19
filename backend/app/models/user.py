import uuid
from datetime import datetime, timedelta
from sqlalchemy import Column, String, Boolean, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy import Enum as SQLAlchemyEnum
import enum
from app.core.database import Base

class UserRole(str, enum.Enum):
    student = "student"
    admin = "admin"
    faculty = "faculty"

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(String(50), unique=True, nullable=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    role = Column(SQLAlchemyEnum(UserRole), default=UserRole.student, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Security fields for account lockout
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    profile = relationship("StudentProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    interview_sessions = relationship("InterviewSession", back_populates="user", cascade="all, delete-orphan")
    
    # V2 Career Intelligence Relationships
    student_projects = relationship("StudentProject", back_populates="user", cascade="all, delete-orphan")
    student_preferences = relationship("StudentPreference", back_populates="user", uselist=False, cascade="all, delete-orphan")
    student_skills = relationship("StudentSkill", back_populates="user", cascade="all, delete-orphan")
    skill_gaps = relationship("SkillGap", back_populates="user", cascade="all, delete-orphan")
    roadmaps = relationship("Roadmap", back_populates="user", cascade="all, delete-orphan")
    behavior_summary = relationship("BehaviorSummary", back_populates="user", uselist=False, cascade="all, delete-orphan")
    
    def is_locked(self) -> bool:
        """Check if account is currently locked."""
        if self.locked_until:
            from datetime import timezone
            now = datetime.now(timezone.utc)
            locked_until_tz = self.locked_until
            if locked_until_tz.tzinfo is None:
                locked_until_tz = locked_until_tz.replace(tzinfo=timezone.utc)
            return locked_until_tz > now
        return False
    
    def record_failed_login(self) -> None:
        """Increment failed attempts and lock account if threshold exceeded."""
        self.failed_login_attempts += 1
        
        # Lock account after 5 failed attempts for 30 minutes
        if self.failed_login_attempts >= 5:
            from datetime import timezone
            self.locked_until = datetime.now(timezone.utc) + timedelta(minutes=30)
    
    def reset_failed_attempts(self) -> None:
        """Reset failed login attempts after successful login."""
        self.failed_login_attempts = 0
        self.locked_until = None

