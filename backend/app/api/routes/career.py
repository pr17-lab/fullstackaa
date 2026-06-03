"""
API routes for Career Recommendations dashboard.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies.database import get_db
from app.api.dependencies.auth import get_current_user
from app.models.user import User
from app.modules.skills import service

router = APIRouter(prefix="/api/skills", tags=["Career Recommendations"])


@router.get("/recommendations")
async def get_career_recommendations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get career recommendations and grouped match tiers for the authenticated student.
    """
    import uuid
    user_uuid = current_user.id
    if isinstance(user_uuid, str):
        user_uuid = uuid.UUID(user_uuid)

    # 1. Fetch fully enriched and sorted student gaps from skills service
    gaps = service.get_student_gaps(db, user_uuid)

    # 2. Fetch primary and alternative career recommendations
    recommendations = service.get_career_recommendation(db, user_uuid)

    # 3. Group gaps into four match tiers based on score
    excellent = [g for g in gaps if g.match_score >= 60.0]
    good = [g for g in gaps if 35.0 <= g.match_score < 60.0]
    potential = [g for g in gaps if 20.0 <= g.match_score < 35.0]
    low = [g for g in gaps if g.match_score < 20.0]

    # Return structured career dashboard response
    return {
        "recommendations": recommendations,
        "tiers": {
            "excellent": excellent,
            "good": good,
            "potential": potential,
            "low": low
        }
    }
