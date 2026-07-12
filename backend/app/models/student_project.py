import uuid
from sqlalchemy import Column, String, Text, DateTime, Date, ForeignKey, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func
from app.core.database import Base

class StudentProject(Base):
    __tablename__ = "student_projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    tech_stack = Column(ARRAY(Text))
    domain = Column(String(100))
    complexity = Column(String(20))
    project_url = Column(String(500))
    completed_at = Column(Date)
    
    # GitHub Integration Fields
    repo_url = Column(String(255), nullable=True)
    extracted_skills = Column(JSONB, nullable=True)
    calculated_complexity = Column(Integer, nullable=True)
    analyzed_at = Column(DateTime(timezone=True), nullable=True)
    depth_verified = Column(Boolean, default=False, server_default="false", nullable=False)
    depth_verified_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="student_projects")

    @validates("repo_url")
    def validate_repo_url(self, key, value):
        if value is not None:
            if "github.com" not in value.lower():
                raise ValueError("Repository URL must be a github.com link")
        return value
