import uuid
from sqlalchemy import Column, String, Integer, Numeric, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class Subject(Base):
    __tablename__ = "subjects"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    term_id = Column(UUID(as_uuid=True), ForeignKey("academic_terms.id"), nullable=False)
    subject_name = Column(String(255), nullable=False)
    subject_code = Column(String(50), nullable=False)
    credits = Column(Integer, nullable=False)
    marks = Column(Numeric(5, 2), nullable=False)
    grade = Column(String(2), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    term = relationship("AcademicTerm", back_populates="subjects")
