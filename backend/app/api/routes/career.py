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


@router.get("/recommendations/{job_role}/breakdown")
async def get_career_recommendation_breakdown(
    job_role: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed match score breakdown and next tier recommendation for a specific job role.
    """
    from fastapi import HTTPException, status
    from sqlalchemy.sql import text
    import uuid
    from app.models.student_profile import StudentProfile
    from app.models.student_skill import StudentSkill
    from app.models.skill_taxonomy import SkillTaxonomy
    
    # 1. Fetch requirements for the job_role case-insensitively
    res = db.execute(
        text("SELECT job_role, skill_id, importance, min_score_required FROM job_skill_requirements WHERE LOWER(job_role) = :role"),
        {"role": job_role.lower()}
    )
    rows = res.fetchall()
    if not rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No requirements found for job role '{job_role}'"
        )
        
    actual_role_name = rows[0][0]
    reqs = []
    for row in rows:
        reqs.append({
            "skill_id": str(row[1]),
            "importance": row[2],
            "min_score_required": float(row[3])
        })
        
    user_uuid = current_user.id
    if isinstance(user_uuid, str):
        user_uuid = uuid.UUID(user_uuid)
        
    # 2. Fetch student profile (department)
    prof = db.query(StudentProfile).filter(StudentProfile.user_id == user_uuid).first()
    student_dept = prof.department if prof else None
    
    # 3. Fetch user skills
    skills = db.query(StudentSkill).filter(StudentSkill.user_id == user_uuid).all()
    stud_skills = {str(s.skill_id): {
        "score": float(s.confidence_score) if s.confidence_score else 0.0,
        "resume_weight": float(s.resume_weight) if s.resume_weight else 0.0
    } for s in skills}
    
    # 4. Fetch skill taxonomy names mapping
    skill_tax = db.query(SkillTaxonomy).all()
    id_to_name = {str(s.id): s.skill_name for s in skill_tax}
    
    # 5. Call score and breakdown engine helper
    from app.modules.skills.engine import calculate_role_score_and_breakdown
    result = calculate_role_score_and_breakdown(
        db=db,
        user_id=user_uuid,
        role=actual_role_name,
        reqs=reqs,
        stud_skills=stud_skills,
        student_dept=student_dept,
        id_to_name=id_to_name
    )
    
    match_score = result["match_score"]
    
    # 6. Map match score to category: Excellent Match, Good Match, Potential Match, Low Match
    if match_score >= 60.0:
        category = "Excellent Match"
    elif match_score >= 35.0:
        category = "Good Match"
    elif match_score >= 20.0:
        category = "Potential Match"
    else:
        category = "Low Match"
        
    # 7. Compute distance to next tier
    if match_score >= 60.0:
        distance = None
    else:
        if match_score >= 35.0:
            next_category = "Excellent Match"
            points_needed = round(60.0 - match_score, 2)
        elif match_score >= 20.0:
            next_category = "Good Match"
            points_needed = round(35.0 - match_score, 2)
        else:
            next_category = "Potential Match"
            points_needed = round(20.0 - match_score, 2)
            
        # Filter and sort missing/weak leverage skills
        leverage_skills = []
        for item in result["breakdown"]:
            if item["status"] in ("weak", "missing"):
                leverage_skills.append(item)
                
        leverage_skills.sort(key=lambda x: (-(x["weight"] * (1.0 - x["credit_pct"])), x["skill"]))
        highest_leverage = [item["skill"] for item in leverage_skills[:3]]
        
        distance = {
            "next_category": next_category,
            "points_needed": points_needed,
            "highest_leverage_skills": highest_leverage
        }
        
    return {
        "job_role": actual_role_name,
        "match_score": match_score,
        "category": category,
        "breakdown": result["breakdown"],
        "distance_to_next_tier": distance
    }

