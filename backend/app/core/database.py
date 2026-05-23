from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from app.core.config import settings

# Create database engine with connection pooling
engine = create_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=settings.DB_POOL_SIZE,           # Number of connections to keep open
    max_overflow=settings.DB_MAX_OVERFLOW,     # Additional connections when needed
    pool_pre_ping=True,                        # Verify connections before use
    pool_recycle=settings.DB_POOL_RECYCLE,     # Recycle connections after N seconds
    echo=settings.DEBUG                        # Log SQL queries in debug mode
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

# Dependency for getting database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

