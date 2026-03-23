import uuid
from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.core.database import Base

class JobCache(Base):
    __tablename__ = "job_cache"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    query_key = Column(String(255), unique=True, nullable=False)
    job_title = Column(String(255))
    source = Column(String(50))
    raw_results = Column(JSONB)
    job_count = Column(Integer)
    fetched_at = Column(DateTime(timezone=True))
    expires_at = Column(DateTime(timezone=True))
