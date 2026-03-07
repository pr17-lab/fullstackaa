# Academic Module (SATA)
# Aggregates all academic-related routers and exposes AcademicService for cross-module use.
from app.modules.academic.router import router
from app.modules.academic.service import AcademicService

__all__ = ["router", "AcademicService"]
