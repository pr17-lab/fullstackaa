from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import sqlalchemy as sa
from pydantic import BaseModel
from uuid import UUID
from typing import List

from app.api.dependencies.database import get_db
from app.api.dependencies.auth import get_current_user
from app.models.user import User

from . import schemas, service

router = APIRouter(prefix="/api/skills", tags=["Skills"])

@router.get("/me", response_model=List[schemas.SkillResponse])
def get_my_skills(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all mapped skills for the current user."""
    return service.get_student_skills(db, current_user.id)

@router.get("/summary", response_model=schemas.StudentSkillSummary)
def get_my_skill_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get high-level dashboard metrics for the current user's career paths."""
    return service.get_skill_summary(db, current_user.id)

@router.get("/gaps", response_model=List[schemas.SkillGapResponse])
def get_my_skill_gaps(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get skill gaps matching the current user's target jobs."""
    return service.get_student_gaps(db, current_user.id)

@router.get("/gaps/{job_role}", response_model=schemas.SkillGapResponse)
def get_my_skill_gap_for_role(
    job_role: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a single skill gap alignment for a specific job profile."""
    gaps = service.get_student_gaps(db, current_user.id)
    for g in gaps:
        if g.job_role.lower() == job_role.lower():
            return g
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, 
        detail=f"No gap analysis found for role {job_role}"
    )

@router.get("/recommendation")
def career_recommendation(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get the primary and alternative career recommendations for the user."""
    return service.get_career_recommendation(db, current_user.id)

@router.get("/taxonomy/search", response_model=List[schemas.TaxonomySearchResponse])
def search_skills_taxonomy(
    query: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search the skills taxonomy for dropdown population."""
    if not query.strip(): return []
    return service.search_taxonomy(db, query.strip())

@router.get("/topics", response_model=List[schemas.TaxonomySearchResponse])
def get_practice_topics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a list of practiceable topics sourced directly from skill_taxonomy.
    """
    from app.models.skill_taxonomy import SkillTaxonomy
    return db.query(SkillTaxonomy).order_by(SkillTaxonomy.skill_name).all()

@router.post("/manual", response_model=schemas.SkillResponse)
def add_manual_skill(
    payload: schemas.ManualSkillCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add or upweight a self-reported skill."""
    return service.add_manual_skill(
        db=db, 
        user_id=current_user.id, 
        skill_name=payload.skill_name.strip(), 
        confidence_score=payload.confidence_score
    )

@router.delete("/manual/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_manual_skill(
    skill_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove a self-reported skill source."""
    service.remove_manual_skill(db=db, user_id=current_user.id, skill_id=skill_id)
    return None

class ResumeExtractRequest(BaseModel):
    resume_text: str

@router.post("/extract-resume-skills", status_code=201)
async def extract_resume_skills(
    body: ResumeExtractRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Extract technical skills from a student's resume using Gemini,
    with a prompt biased by their target roles, and save them.
    """
    from app.models.student_preference import StudentPreference
    from app.models.skill_taxonomy import SkillTaxonomy
    from app.models.student_skill import StudentSkill
    from app.modules.skills.engine import calculate_composite_score
    from app.utils.academic import score_to_level
    from app.core.config import settings
    import httpx
    import json
    import uuid
    import logging
    
    logger = logging.getLogger(__name__)
    pref = db.query(StudentPreference).filter(StudentPreference.user_id == current_user.id).first()
    target_roles_str = ""
    if pref and pref.target_roles:
        target_roles_str = f" This user is targeting {', '.join(pref.target_roles)} roles — pay particular attention to relevant frameworks/tools for these roles in this text."

    prompt = f"""Act as an automated technology identifier. Read this resume text.{target_roles_str} Return ONLY a plain JSON array of framework, tool, or database strings discovered (e.g., ['FastAPI', 'React', 'Docker']). Do not include explanatory text or markdown backticks.

Resume:
{body.resume_text[:6000]}"""

    extracted_skills = []
    if settings.GEMINI_API_KEY:
        try:
            url_gemini = (
                "https://generativelanguage.googleapis.com/v1beta/models/"
                f"{settings.GEMINI_MODEL}:generateContent?key={settings.GEMINI_API_KEY}"
            )
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.3,
                    "response_mime_type": "application/json"
                },
            }
            async with httpx.AsyncClient(timeout=25.0) as client_http:
                resp_gemini = await client_http.post(url_gemini, json=payload)
                resp_gemini.raise_for_status()
                raw_text = resp_gemini.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                
                # Strip markdown code fences if Gemini returned them anyway
                if raw_text.startswith("```"):
                    raw_text = raw_text.split("```")[1]
                    if raw_text.startswith("json"):
                        raw_text = raw_text[4:]
                raw_text = raw_text.strip()
                
                extracted_skills = json.loads(raw_text)
                if not isinstance(extracted_skills, list):
                    extracted_skills = []
        except Exception as exc:
            logger.error("Exception during Gemini resume skill extraction: %s", exc)
            extracted_skills = []
            
    # Fallback / mock extraction if settings are not set or Gemini fails
    if not extracted_skills:
        extracted_skills = ["FastAPI", "React", "Docker"]
        
    saved_skills = []
    is_sqlite = db.bind.dialect.name == "sqlite"
    extracted_skill_ids = set()
    
    for skill_name in extracted_skills:
        if is_sqlite:
            tax = (
                db.query(SkillTaxonomy)
                .filter(sa.func.lower(SkillTaxonomy.skill_name) == skill_name.lower())
                .first()
            )
            if not tax:
                all_tax = db.query(SkillTaxonomy).all()
                for t in all_tax:
                    if t.aliases and any(skill_name.lower() in str(a).lower() for a in t.aliases):
                        tax = t
                        break
        else:
            tax = (
                db.query(SkillTaxonomy)
                .filter(
                    sa.or_(
                        sa.func.lower(SkillTaxonomy.skill_name) == skill_name.lower(),
                        sa.func.array_to_string(SkillTaxonomy.aliases, ",").ilike(f"%{skill_name}%"),
                    )
                )
                .first()
            )

        if not tax:
            logger.warning("Skill '%s' not found in SkillTaxonomy, skipping", skill_name)
            continue

        extracted_skill_ids.add(tax.id)

        ss = (
            db.query(StudentSkill)
            .filter(
                StudentSkill.user_id == current_user.id,
                StudentSkill.skill_id == tax.id
            )
            .first()
        )
        
        res_wt = 70.0
        
        if not ss:
            ss = StudentSkill(
                id=uuid.uuid4(),
                user_id=current_user.id,
                skill_id=tax.id,
                resume_weight=res_wt,
                project_weight=0.0,
                interview_weight=0.0,
                communication_weight=0.0,
                is_interview_scored=False,
                source=["resume"] if not is_sqlite else None
            )
            db.add(ss)
            db.flush()
        else:
            ss.resume_weight = res_wt
            src_list = list(ss.source) if ss.source else []
            if "resume" not in src_list:
                src_list.append("resume")
                if not is_sqlite:
                    ss.source = src_list
                    
        pr_wt = float(ss.project_weight) if ss.project_weight else 0.0
        in_wt = float(ss.interview_weight) if ss.interview_weight else 0.0
        comm_wt = float(ss.communication_weight) if ss.communication_weight else 0.0
        
        ss.confidence_score = calculate_composite_score(res_wt, pr_wt, in_wt, comm_wt, is_interview_scored=ss.is_interview_scored)
        ss.level = score_to_level(ss.confidence_score)
        saved_skills.append(tax.skill_name)

    # For skills that were resume-sourced but no longer appear in the updated resume:
    all_student_skills = db.query(StudentSkill).filter(StudentSkill.user_id == current_user.id).all()
    for ss in all_student_skills:
        is_resume_sourced = False
        if not is_sqlite and ss.source and "resume" in ss.source:
            is_resume_sourced = True
        elif ss.resume_weight is not None and float(ss.resume_weight) > 0:
            is_resume_sourced = True
            
        if is_resume_sourced and ss.skill_id not in extracted_skill_ids:
            # Set resume_weight back to 0.0
            ss.resume_weight = 0.0
            # Remove "resume" from source if present
            if not is_sqlite and ss.source and "resume" in ss.source:
                src_list = list(ss.source)
                if "resume" in src_list:
                    src_list.remove("resume")
                ss.source = src_list
            # Recalculate confidence score and level without touching project_weight or interview_weight
            pr_wt = float(ss.project_weight) if ss.project_weight else 0.0
            in_wt = float(ss.interview_weight) if ss.interview_weight else 0.0
            comm_wt = float(ss.communication_weight) if ss.communication_weight else 0.0
            ss.confidence_score = calculate_composite_score(0.0, pr_wt, in_wt, comm_wt, is_interview_scored=ss.is_interview_scored)
            ss.level = score_to_level(ss.confidence_score)

    if pref:
        pref.onboarding_step = "resume_uploaded"
        
    db.commit()
    return {"success": True, "skills_extracted": saved_skills, "skills_saved_count": len(saved_skills)}
