import uuid
from sqlalchemy import Column, Integer, Numeric, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class AcademicTerm(Base):
    __tablename__ = "academic_terms"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    semester = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    gpa = Column(Numeric(3, 2), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Composite unique constraint
    __table_args__ = (
        UniqueConstraint('user_id', 'semester', 'year', name='uq_user_semester_year'),
    )
    
    # Relationships
    user = relationship("User", back_populates="academic_terms")
    subjects = relationship("Subject", back_populates="term", cascade="all, delete-orphan")
