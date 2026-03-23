import uuid
from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class SkillTaxonomy(Base):
    __tablename__ = "skill_taxonomy"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    skill_name = Column(String(100), unique=True, nullable=False)
    category = Column(String(50), nullable=False)
    aliases = Column(ARRAY(Text))
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    student_skills = relationship("StudentSkill", back_populates="skill")
    job_skill_requirements = relationship("JobSkillRequirement", back_populates="skill")
    roadmap_tasks = relationship("RoadmapTask", back_populates="skill")
