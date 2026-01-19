from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
import psutil
import os

from app.core.database import get_db
from app.schemas.common import HealthStatus, DetailedHealthStatus

router = APIRouter()

@router.get("/health", response_model=HealthStatus)
def health_check(db: Session = Depends(get_db)):
    """Basic health check endpoint."""
    try:
        # Check database connection
        db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    return HealthStatus(
        status="healthy" if db_status == "healthy" else "degraded",
        database=db_status,
        version="1.0.0"
    )

@router.get("/health/detailed", response_model=DetailedHealthStatus)
def detailed_health_check(db: Session = Depends(get_db)):
    """Detailed health check with metrics."""
    try:
        # Database metrics
        user_count = db.execute(text("SELECT COUNT(*) FROM users")).scalar()
        profile_count = db.execute(text("SELECT COUNT(*) FROM student_profiles")).scalar()
        term_count = db.execute(text("SELECT COUNT(*) FROM academic_terms")).scalar()
        subject_count = db.execute(text("SELECT COUNT(*) FROM subjects")).scalar()
        
        db_metrics = {
            "status": "healthy",
            "users_count": user_count,
            "profiles_count": profile_count,
            "academic_terms_count": term_count,
            "subjects_count": subject_count
        }
    except Exception as e:
        db_metrics = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Memory metrics
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    
    memory_metrics = {
        "rss_mb": round(memory_info.rss / 1024 / 1024, 2),
        "vms_mb": round(memory_info.vms / 1024 / 1024, 2),
        "percent": round(process.memory_percent(), 2)
    }
    
    return DetailedHealthStatus(
        status="healthy" if db_metrics.get("status") == "healthy" else "degraded",
        database=db_metrics,
        memory=memory_metrics
    )
