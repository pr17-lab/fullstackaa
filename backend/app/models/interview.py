"""
Interview ORM Models (Phase 2, hardened)
-----------------------------------------
Maps to the `interview_sessions` and `interview_questions` tables
created in 0001_baseline, extended by 0002_interview_hardening.

Improvements over Phase 2 initial:
  - CheckConstraint on session.status — database rejects arbitrary strings.
  - Composite Index (user_id, created_at) for ordered list_sessions() queries.
  - Individual indexes on interview_questions.session_id.
  - SessionStatus constants used throughout the service layer.
"""
import uuid
from sqlalchemy import (
    Column, String, Text, DateTime, ForeignKey,
    Index, CheckConstraint, SmallInteger
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


# ---------------------------------------------------------------------------
# Status constants — single source of truth for the lifecycle
# ---------------------------------------------------------------------------
class SessionStatus:
    ACTIVE    = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"

    ALL = {ACTIVE, COMPLETED, ABANDONED}


class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    branch     = Column(String(100), nullable=False)
    topic      = Column(String(100), nullable=True)
    status     = Column(String(20),  nullable=False, default=SessionStatus.ACTIVE)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        # Composite index for ordered per-user queries (list_sessions)
        Index("ix_interview_sessions_user_id_created_at", "user_id", "created_at"),
        # DB-level enforcement of allowed status values
        CheckConstraint(
            "status IN ('active', 'completed', 'abandoned')",
            name="ck_interview_sessions_status",
        ),
    )

    # Back-reference to the owning User
    user = relationship("User", back_populates="interview_sessions")

    questions = relationship(
        "InterviewQuestion",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="InterviewQuestion.created_at",
        lazy="select",
    )


class InterviewQuestion(Base):
    __tablename__ = "interview_questions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("interview_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    topic       = Column(String(100), nullable=False)
    question    = Column(Text,        nullable=False)
    difficulty  = Column(String(20),  nullable=False, default="medium")
    source      = Column(String(50),  nullable=True)
    follow_up    = Column(Text,        nullable=True)
    user_answer  = Column(Text,        nullable=True)
    ai_score     = Column(SmallInteger, nullable=True)
    ai_verdict   = Column(String(20),  nullable=True)
    ai_feedback  = Column(Text,        nullable=True)
    model_answer = Column(Text,        nullable=True)
    mistakes     = Column(JSONB,       nullable=True, default=list)
    improvement  = Column(Text,        nullable=True)
    evaluated_at = Column(DateTime(timezone=True), nullable=True)
    created_at   = Column(DateTime(timezone=True), server_default=func.now())

    session = relationship("InterviewSession", back_populates="questions")
