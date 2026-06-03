"""
Skills service — student skill retrieval, gap analysis, career recommendations,
taxonomy search, and manual skill management.
"""

import sqlalchemy as sa
from sqlalchemy.orm import Session
from uuid import UUID
from fastapi import HTTPException, status

from app.models.student_skill import StudentSkill
from app.models.skill_taxonomy import SkillTaxonomy
from app.models.skill_gap import SkillGap
from app.utils.academic import score_to_level
from .schemas import SkillResponse, SkillGapResponse, StudentSkillSummary


# ---------------------------------------------------------------------------
# Department → primary career roles mapping
# ---------------------------------------------------------------------------

DEPARTMENT_PRIMARY_ROLES: dict[str, list[str]] = {
    "CSE": [
        "Software Engineer", "Backend Developer", "Full Stack Developer",
        "Frontend Developer", "Data Engineer", "Data Scientist",
        "Machine Learning Engineer", "DevOps Engineer", "Cloud Engineer",
        "Cybersecurity Analyst", "Blockchain Developer",
        "QA/Test Engineer", "Data Analyst", "Technical Product Manager",
    ],
    "AIML": [
        "Data Scientist", "Machine Learning Engineer", "NLP Engineer",
        "Data Engineer", "Data Analyst", "Software Engineer",
        "Backend Developer", "Full Stack Developer",
    ],
    "ECE": [
        "Embedded Systems Engineer", "Hardware/VLSI Design Engineer",
        "IoT Engineer", "Cybersecurity Analyst", "Cloud Engineer",
        "Backend Developer", "Software Engineer",
    ],
    "MECH": [
        "Data Analyst", "IoT Engineer", "Embedded Systems Engineer",
        "Software Engineer", "Backend Developer",
        "QA/Test Engineer", "Cloud Engineer",
    ],
}


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _enrich_skill_list(items: list, skill_name_map: dict[str, str]) -> list:
    """Inject skill_name and optional parent_name into each skill-reference dict."""
    enriched = []
    for item in items:
        entry = dict(item)
        sid = entry.get("skill_id")
        if sid:
            entry["skill_name"] = skill_name_map.get(str(sid))
        pid = entry.get("parent_id")
        if pid:
            entry["parent_name"] = skill_name_map.get(str(pid))
        enriched.append(entry)
    return enriched


def _make_match_label(score: float) -> str:
    if score >= 60:
        return "Excellent"
    if score >= 35:
        return "Good"
    if score >= 20:
        return "Potential"
    return "Low Match"


# ---------------------------------------------------------------------------
# Public service functions
# ---------------------------------------------------------------------------

def get_student_skills(db: Session, user_id: UUID) -> list[SkillResponse]:
    """Return all mapped skills for a student, ordered by confidence score desc."""
    if isinstance(user_id, str):
        user_id = UUID(user_id)
    rows = (
        db.query(StudentSkill, SkillTaxonomy)
        .join(SkillTaxonomy, StudentSkill.skill_id == SkillTaxonomy.id)
        .filter(StudentSkill.user_id == user_id)
        .order_by(StudentSkill.confidence_score.desc())
        .all()
    )
    return [
        SkillResponse(
            skill_id=ss.skill_id,
            skill_name=st.skill_name,
            category=st.category,
            confidence_score=float(ss.confidence_score) if ss.confidence_score else 0.0,
            level=ss.level,
            source=ss.source,
            last_computed_at=ss.last_computed_at,
        )
        for ss, st in rows
    ]


def get_student_gaps(db: Session, user_id: UUID) -> list[SkillGapResponse]:
    """Return all skill-gap records for a student, ordered by match score desc."""
    if isinstance(user_id, str):
        user_id = UUID(user_id)
    gaps = (
        db.query(SkillGap)
        .filter(SkillGap.user_id == user_id)
        .order_by(SkillGap.match_score.desc())
        .all()
    )

    skill_name_map = {str(s.id): s.skill_name for s in db.query(SkillTaxonomy).all()}

    results = []
    for g in gaps:
        score = float(g.match_score) if g.match_score else 0.0
        label = "Excellent" if score >= 60 else "Good" if score >= 35 else "Potential"
        results.append(SkillGapResponse(
            job_role=g.job_role,
            match_score=score,
            match_label=label,
            missing_skills=_enrich_skill_list(g.missing_skills or [], skill_name_map),
            weak_skills=_enrich_skill_list(g.weak_skills or [], skill_name_map),
            strong_skills=_enrich_skill_list(g.strong_skills or [], skill_name_map),
            high_potential_skills=_enrich_skill_list(g.high_potential_skills or [], skill_name_map),
            computed_at=g.computed_at,
        ))
    return results


def get_skill_summary(db: Session, user_id: UUID) -> StudentSkillSummary:
    """Return high-level skill metrics for the student."""
    skills = get_student_skills(db, user_id)
    gaps = get_student_gaps(db, user_id)
    return StudentSkillSummary(
        total_skills=len(skills),
        strong_count=sum(1 for s in skills if s.level == "strong"),
        moderate_count=sum(1 for s in skills if s.level == "moderate"),
        weak_count=sum(1 for s in skills if s.level == "weak"),
        top_skills=skills[:5],
        skill_gaps=gaps,
    )


def get_career_recommendation(db: Session, user_id: UUID) -> dict:
    """Return primary and alternative career recommendations based on gap scores."""
    if isinstance(user_id, str):
        user_id = UUID(user_id)
    from app.models.student_profile import StudentProfile
    from app.models.student_preference import StudentPreference

    profile = db.query(StudentProfile).filter(StudentProfile.user_id == user_id).first()
    prefs = db.query(StudentPreference).filter(StudentPreference.user_id == user_id).first()
    department = profile.department if profile else None

    all_gaps = (
        db.query(SkillGap)
        .filter(SkillGap.user_id == user_id)
        .order_by(SkillGap.match_score.desc())
        .all()
    )

    if not all_gaps:
        return {
            "primary": None,
            "alternatives": [],
            "is_transition": False,
            "transition_target": None,
            "out_of_domain": False,
        }

    is_transition = prefs.career_transition if prefs else False
    transition_to = prefs.transition_to if prefs else None

    def gap_to_dict(g) -> dict:
        score = float(g.match_score) if g.match_score else 0.0
        return {"job_role": g.job_role, "match_score": round(score, 2), "match_label": _make_match_label(score)}

    # Career-transition mode: user explicitly chose a target role
    if is_transition and transition_to:
        transition_gap = next((g for g in all_gaps if g.job_role == transition_to), None)
        primary = gap_to_dict(transition_gap) if transition_gap else {
            "job_role": transition_to, "match_score": 0.0, "match_label": "Low Match"
        }
        return {
            "primary": primary,
            "alternatives": [gap_to_dict(g) for g in all_gaps if g.job_role != transition_to][:2],
            "is_transition": True,
            "transition_target": transition_to,
            "out_of_domain": False,
        }

    # Normal mode: filter to department-appropriate roles
    allowed_roles = DEPARTMENT_PRIMARY_ROLES.get(department, [])
    filtered_gaps = [g for g in all_gaps if g.job_role in allowed_roles]

    out_of_domain = False
    if not filtered_gaps:
        filtered_gaps = all_gaps
        out_of_domain = True

    return {
        "primary": gap_to_dict(filtered_gaps[0]),
        "alternatives": [gap_to_dict(g) for g in filtered_gaps[1:3]],
        "is_transition": False,
        "transition_target": None,
        "out_of_domain": out_of_domain,
    }


def search_taxonomy(db: Session, query: str) -> list[SkillTaxonomy]:
    """Case-insensitive search across skill names and aliases."""
    q = f"%{query.lower()}%"
    return (
        db.query(SkillTaxonomy)
        .filter(sa.or_(
            sa.func.lower(SkillTaxonomy.skill_name).like(q),
            sa.func.array_to_string(SkillTaxonomy.aliases, ",").ilike(q),
        ))
        .limit(5)
        .all()
    )


def add_manual_skill(db: Session, user_id: UUID, skill_name: str, confidence_score: float) -> SkillResponse:
    """Add or upweight a self-reported skill for the student."""
    # Resolve taxonomy entry
    tax = db.query(SkillTaxonomy).filter(
        sa.func.lower(SkillTaxonomy.skill_name) == skill_name.lower()
    ).first()

    if not tax:
        tax = db.query(SkillTaxonomy).filter(
            sa.func.array_to_string(SkillTaxonomy.aliases, ",").ilike(f"%{skill_name}%")
        ).first()

    if not tax:
        suggestions = [s.skill_name for s in search_taxonomy(db, skill_name)]
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": "Skill not in taxonomy.", "suggestions": suggestions},
        )

    # Upsert
    ss = db.query(StudentSkill).filter(
        StudentSkill.user_id == user_id,
        StudentSkill.skill_id == tax.id,
    ).first()

    if ss:
        srcs = list(ss.source) if ss.source else []
        if "self_reported" not in srcs:
            srcs.append("self_reported")
        ss.source = srcs
        ss.confidence_score = max(float(ss.confidence_score) if ss.confidence_score else 0.0, confidence_score)
        ss.level = score_to_level(float(ss.confidence_score))
    else:
        ss = StudentSkill(
            user_id=user_id,
            skill_id=tax.id,
            confidence_score=confidence_score,
            level=score_to_level(confidence_score),
            source=["self_reported"],
        )
        db.add(ss)

    db.commit()
    db.refresh(ss)
    return SkillResponse(
        skill_id=ss.skill_id,
        skill_name=tax.skill_name,
        category=tax.category,
        confidence_score=float(ss.confidence_score),
        level=ss.level,
        source=ss.source,
        last_computed_at=ss.last_computed_at,
    )


def remove_manual_skill(db: Session, user_id: UUID, skill_id: UUID) -> None:
    """Remove the self-reported source from a skill (or delete if no other sources)."""
    ss = db.query(StudentSkill).filter(
        StudentSkill.user_id == user_id,
        StudentSkill.skill_id == skill_id,
    ).first()

    if not ss or not ss.source or "self_reported" not in ss.source:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only self-reported skills can be manually removed.",
        )

    srcs = list(ss.source)
    srcs.remove("self_reported")

    if not srcs:
        db.delete(ss)
    else:
        ss.source = srcs
        base_score = float(ss.resume_weight) if ss.resume_weight else 0.0
        ss.confidence_score = base_score
        ss.level = score_to_level(base_score)

    db.commit()


from .project_service import verify_github_complexity_async
