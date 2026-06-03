import uuid
from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class SkillGap(Base):
    __tablename__ = "skill_gaps"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    job_role = Column(String(255), nullable=False)
    match_score = Column(Numeric(5, 2))
    missing_skills = Column(JSONB)
    weak_skills = Column(JSONB)
    strong_skills = Column(JSONB)
    high_potential_skills = Column(JSONB, default=list)
    computed_at = Column(DateTime(timezone=True))

    __table_args__ = (
        UniqueConstraint('user_id', 'job_role', name='uq_user_gap_job_role'),
    )

    # Relationships
    user = relationship("User", back_populates="skill_gaps")
