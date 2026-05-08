import uuid
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class SkillResource(Base):
    __tablename__ = "skill_resources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    skill_id = Column(UUID(as_uuid=True), ForeignKey("skill_taxonomy.id", ondelete="CASCADE"), nullable=False)
    phase = Column(String(20), nullable=False) # 'learn' or 'practice'
    platform = Column(String(100), nullable=False)
    resource_url = Column(String(500), nullable=False)
    estimated_hours = Column(Integer, nullable=False, default=10)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    skill = relationship("SkillTaxonomy")
