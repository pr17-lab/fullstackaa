"""
Academic Module Router (v1.0)
-----------------------------
Aggregates all SATA (Student Academic Tracker) routes as a single FastAPI router.
Existing route files are imported and included here — no logic is duplicated.

URL prefixes are applied when this router is included in main.py:
  - Students:   /api/students/*
  - Analytics:  /api/analytics/*
  - Profile:    /api/profile/*
  - Academic:   /api/academic/*
"""
from fastapi import APIRouter

from app.api.routes import students, profile

router = APIRouter()

# Re-mount existing route modules under the academic module
router.include_router(students.router,  prefix="",           tags=["Students"])
router.include_router(profile.router,   prefix="/profile",   tags=["Profile"])
