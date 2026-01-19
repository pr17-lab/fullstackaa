from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.api.routes import auth, profile, academic, students, analytics, health
from app.services.csv_data_service import csv_data_loader
from app.core.logging import setup_logging
from app.middleware.logging import log_requests
import logging

# Initialize structured logging
setup_logging(level="INFO" if not settings.DEBUG else "DEBUG")
logger = logging.getLogger(__name__)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Student Academic Tracker API",
    description="REST API for managing student academic records and performance analytics",
    version="1.0.0"
)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.on_event("startup")
async def startup_event():
    """Load CSV data when application starts."""
    logger.info("Loading CSV data...")
    csv_data_loader.load_data()
    logger.info(f"CSV data loaded: {csv_data_loader.is_loaded}")


# Add request logging middleware
app.middleware("http")(log_requests)

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
app.include_router(health.router, prefix="/api", tags=["Health"])


@app.get("/")
async def root():
    return {
        "message": "Student Academic Tracker API",
        "version": "1.0.0",
        "docs": "/docs"
    }


