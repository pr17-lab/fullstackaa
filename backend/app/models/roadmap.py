import uuid
from sqlalchemy import Column, String, Integer, Boolean, Text, DateTime, SmallInteger, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class Roadmap(Base):
    __tablename__ = "roadmaps"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    job_role = Column(String(255), nullable=False)
    version = Column(Integer, default=1)
    status = Column(String(20), default='active')
    is_transition = Column(Boolean, default=False)
    generated_by = Column(String(20))
    total_tasks = Column(Integer, default=0)
    completed_tasks = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="roadmaps")
    roadmap_tasks = relationship("RoadmapTask", back_populates="roadmap", cascade="all, delete-orphan")


class RoadmapTask(Base):
    __tablename__ = "roadmap_tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    roadmap_id = Column(UUID(as_uuid=True), ForeignKey("roadmaps.id", ondelete="CASCADE"), nullable=False)
    skill_id = Column(UUID(as_uuid=True), ForeignKey("skill_taxonomy.id"), nullable=True)
    associated_skill_id = Column(UUID(as_uuid=True), ForeignKey("skill_taxonomy.id"), nullable=True)
    phase = Column(String(20), nullable=False)
    task_type = Column(String(30))
    title = Column(String(255), nullable=False)
    description = Column(Text)
    resource_url = Column(String(500))
    platform = Column(String(100))
    estimated_hours = Column(Integer)
    order_index = Column(Integer)
    status = Column(String(20), default='pending')
    completed_at = Column(DateTime(timezone=True))
    feedback_score = Column(SmallInteger)
    submission_link = Column(String(500), nullable=True)
    validation_status = Column(String(20), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint(
            "task_type IN ('learn', 'practice', 'apply', 'custom', 'course', 'exercise', 'project')",
            name="ck_roadmap_tasks_task_type"
        ),
        CheckConstraint(
            "validation_status IN ('pending', 'verified', 'failed')",
            name="ck_roadmap_tasks_validation_status"
        ),
    )

    # Relationships
    roadmap = relationship("Roadmap", back_populates="roadmap_tasks")
    skill = relationship("SkillTaxonomy", back_populates="roadmap_tasks", foreign_keys=[skill_id])
    associated_skill = relationship("SkillTaxonomy", foreign_keys=[associated_skill_id])
