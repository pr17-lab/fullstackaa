import uuid
from sqlalchemy import Column, String, Integer, Boolean, Text, DateTime, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class StudentProfile(Base):
    __tablename__ = "student_profiles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    department = Column(String(255), nullable=False)  # renamed from branch
    semester = Column(Integer, nullable=False)
    interests = Column(Text, nullable=True)
    cgpa_10scale = Column(Numeric(4, 2), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # New columns added in migration 0005_new_dataset_columns
    batch_year = Column(Integer, nullable=True)
    performance_status = Column(String(20), nullable=True)  # Excellent / Good / Average / At Risk
    backlog_count = Column(Integer, default=0)
    active_backlog = Column(Boolean, default=False)
    cgpa = Column(Numeric(4, 2), nullable=True)  # Anna University 10-point scale CGPA

    # Relationships
    user = relationship("User", back_populates="profile")

