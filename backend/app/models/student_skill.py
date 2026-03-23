import uuid
from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey, UniqueConstraint, Text
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class StudentSkill(Base):
    __tablename__ = "student_skills"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    skill_id = Column(UUID(as_uuid=True), ForeignKey("skill_taxonomy.id"), nullable=False)
    confidence_score = Column(Numeric(5, 2), default=0)
    level = Column(String(20))
    source = Column(ARRAY(Text))
    academic_weight = Column(Numeric(5, 2), default=0)
    project_weight = Column(Numeric(5, 2), default=0)
    behavior_weight = Column(Numeric(5, 2), default=0)
    last_computed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint('user_id', 'skill_id', name='uq_user_skill'),
    )

    # Relationships
    user = relationship("User", back_populates="student_skills")
    skill = relationship("SkillTaxonomy", back_populates="student_skills")
