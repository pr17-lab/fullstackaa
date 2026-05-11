from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.pool import QueuePool
from app.core.config import settings

# Create database engine with connection pooling
# Ensure we use the asyncpg driver
async_db_url = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

engine = create_async_engine(
    async_db_url,
    poolclass=QueuePool,
    pool_size=settings.DB_POOL_SIZE,           # Number of connections to keep open
    max_overflow=settings.DB_MAX_OVERFLOW,     # Additional connections when needed
    pool_pre_ping=True,                        # Verify connections before use
    pool_recycle=settings.DB_POOL_RECYCLE,     # Recycle connections after N seconds
    echo=settings.DEBUG                        # Log SQL queries in debug mode
)

# Create session factory
SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False
)

# Base class for models
Base = declarative_base()

# Dependency for getting database session
async def get_db():
    async with SessionLocal() as db:
        try:
            yield db
        finally:
            await db.close()

