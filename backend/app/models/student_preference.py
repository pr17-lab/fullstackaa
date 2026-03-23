import uuid
from sqlalchemy import Column, String, Boolean, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class StudentPreference(Base):
    __tablename__ = "student_preferences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    target_roles = Column(ARRAY(String))
    preferred_domains = Column(ARRAY(String))
    open_to_remote = Column(Boolean, default=True)
    career_transition = Column(Boolean, default=False)
    transition_from = Column(String(100))
    transition_to = Column(String(100))
    timeline_months = Column(Integer)
    experience_level = Column(String(20))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="student_preferences")
