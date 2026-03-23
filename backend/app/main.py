from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.logging import setup_logging
from app.middleware.logging import log_requests
from app.services.csv_data_service import csv_data_loader

# Routers: auth & health are application-level; academic and interview are modules
from app.api.routes import auth, health
from app.modules.academic.router import router as academic_module_router
from app.modules.interview.router import router as interview_module_router
from app.modules.skills.router import router as skills_module_router
from app.modules.preferences.router import router as preferences_router
from app.modules.roadmap.router import router as roadmap_router
from app.modules.jobs.router import router as jobs_router

import logging

# ---------------------------------------------------------------------------
# Structured logging  (all middleware registered directly — no gateway)
# ---------------------------------------------------------------------------
setup_logging(level="INFO" if not settings.DEBUG else "DEBUG")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Rate limiter
# ---------------------------------------------------------------------------
limiter = Limiter(key_func=get_remote_address)

# ---------------------------------------------------------------------------
# Application — v1.0 (modular monolith)
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Student Academic Tracker API",
    description=(
        "REST API for managing student academic records, performance analytics, "
        "and AI-assisted interview preparation. "
        "Academic and Interview features run as isolated modules within a single "
        "FastAPI application (modular monolith, v1.0)."
    ),
    version="1.0.0",
)

# ---------------------------------------------------------------------------
# Middleware (CORS, rate limiting, request logging — all registered directly)
# ---------------------------------------------------------------------------
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.middleware("http")(log_requests)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------

@app.on_event("startup")
async def startup_event():
    """Load CSV reference data on startup."""
    logger.info("Starting Student Academic Tracker API v1.0 (modular monolith)")
    csv_data_loader.load_data()
    logger.info("CSV data loaded: %s", csv_data_loader.is_loaded)

# ---------------------------------------------------------------------------
# Routers
#
# Auth and Health are application-level concerns — registered directly.
# Academic module  → /api/{students,academic,analytics,profile}/*
# Interview module → /api/interview/*
# ---------------------------------------------------------------------------
app.include_router(auth.router,                prefix="/api/auth",      tags=["Authentication"])
app.include_router(health.router,              prefix="/api",            tags=["Health"])
app.include_router(academic_module_router,     prefix="/api",            tags=["Academic Module"])
app.include_router(interview_module_router,    prefix="/api/interview",  tags=["Interview Module"])
app.include_router(skills_module_router)
app.include_router(preferences_router,         prefix="/api/preferences", tags=["Preferences"])
app.include_router(roadmap_router,             prefix="/api/roadmap",     tags=["Roadmap"])
app.include_router(jobs_router,                prefix="/api/jobs",        tags=["Jobs"])

# ---------------------------------------------------------------------------
# Root
# ---------------------------------------------------------------------------

@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "Student Academic Tracker API",
        "version": "1.0.0",
        "docs": "/docs",
        "modules": ["academic", "interview", "skills", "preferences", "roadmap"],
    }
