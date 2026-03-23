import uuid
from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class JobSkillRequirement(Base):
    __tablename__ = "job_skill_requirements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_role = Column(String(255), nullable=False)
    skill_id = Column(UUID(as_uuid=True), ForeignKey("skill_taxonomy.id"), nullable=False)
    importance = Column(String(20), nullable=False)
    min_score_required = Column(Numeric(5, 2))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint('job_role', 'skill_id', name='uq_job_role_skill'),
    )

    # Relationships
    skill = relationship("SkillTaxonomy", back_populates="job_skill_requirements")
