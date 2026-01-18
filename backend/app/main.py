from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.routes import auth, profile, academic, students, analytics
from app.services.csv_data_service import csv_data_loader
from app.core.logging import setup_logging
import logging

# Initialize structured logging
setup_logging(level="INFO" if not settings.DEBUG else "DEBUG")
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Student Academic Tracker API",
    description="REST API for managing student academic records and performance analytics",
    version="1.0.0"
)

@app.on_event("startup")
async def startup_event():
    """Load CSV data when application starts."""
    logger.info("Loading CSV data...")
    csv_data_loader.load_data()
    logger.info(f"CSV data loaded: {csv_data_loader.is_loaded}")


# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(students.router, prefix="/api", tags=["Students"])
app.include_router(profile.router, prefix="/api/profile", tags=["Profile"])
app.include_router(academic.router, prefix="/api/academic", tags=["Academic Records"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])


@app.get("/")
async def root():
    return {
        "message": "Student Academic Tracker API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
