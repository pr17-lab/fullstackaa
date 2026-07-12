import uuid
import json
from sqlalchemy import Column, String, Boolean, Integer, DateTime, ForeignKey, TypeDecorator
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class SQLiteCompatibleARRAY(TypeDecorator):
    impl = ARRAY
    cache_ok = True

    def __init__(self, item_type, *args, **kwargs):
        super().__init__(item_type, *args, **kwargs)
        self.item_type = item_type

    def load_dialect_impl(self, dialect):
        if dialect.name == 'sqlite':
            return dialect.type_descriptor(String)
        else:
            return dialect.type_descriptor(ARRAY(self.item_type))

    def process_bind_param(self, value, dialect):
        if dialect.name == 'sqlite':
            if value is not None:
                return json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if dialect.name == 'sqlite':
            if value is not None:
                try:
                    return json.loads(value)
                except Exception:
                    return []
            return []
        return value

class StudentPreference(Base):
    __tablename__ = "student_preferences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    target_roles = Column(SQLiteCompatibleARRAY(String))
    preferred_domains = Column(SQLiteCompatibleARRAY(String))
    open_to_remote = Column(Boolean, default=True)
    career_transition = Column(Boolean, default=False)
    transition_from = Column(String(100))
    transition_to = Column(String(100))
    timeline_months = Column(Integer)
    experience_level = Column(String(20))
    available_hours_per_week = Column(Integer, nullable=True)
    onboarding_step = Column(String(50), default="preferred_role_set", server_default="'preferred_role_set'", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="student_preferences")
