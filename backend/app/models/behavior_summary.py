import uuid
from sqlalchemy import Column, String, Integer, Numeric, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class BehaviorSummary(Base):
    __tablename__ = "behavior_summary"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    interviews_completed = Column(Integer, default=0)
    interviews_abandoned = Column(Integer, default=0)
    questions_answered = Column(Integer, default=0)
    roadmap_tasks_done = Column(Integer, default=0)
    login_streak_days = Column(Integer, default=0)
    last_active_at = Column(DateTime(timezone=True))
    consistency_score = Column(Numeric(5, 2), default=0)
    engagement_level = Column(String(20))
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="behavior_summary")
