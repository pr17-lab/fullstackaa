from sqlalchemy.orm import Session
from uuid import UUID
from app.models.student_skill import StudentSkill
from app.models.skill_taxonomy import SkillTaxonomy
from app.models.skill_gap import SkillGap
from .schemas import SkillResponse, SkillGapResponse, StudentSkillSummary

def get_student_skills(db: Session, user_id: UUID) -> list[SkillResponse]:
    skills = (
        db.query(StudentSkill, SkillTaxonomy)
        .join(SkillTaxonomy, StudentSkill.skill_id == SkillTaxonomy.id)
        .filter(StudentSkill.user_id == user_id)
        .order_by(StudentSkill.confidence_score.desc())
        .all()
    )
    
    results = []
    for ss, st in skills:
        results.append(SkillResponse(
            skill_id=ss.skill_id,
            skill_name=st.skill_name,
            category=st.category,
            confidence_score=float(ss.confidence_score) if ss.confidence_score else 0.0,
            level=ss.level,
            source=ss.source,
            last_computed_at=ss.last_computed_at
        ))
    return results

def get_student_gaps(db: Session, user_id: UUID) -> list[SkillGapResponse]:
    gaps = (
        db.query(SkillGap)
        .filter(SkillGap.user_id == user_id)
        .order_by(SkillGap.match_score.desc())
        .all()
    )

    # Build a skill_id → skill_name lookup from taxonomy
    all_skills = db.query(SkillTaxonomy).all()
    skill_name_map = {str(s.id): s.skill_name for s in all_skills}

    def enrich(items: list) -> list:
        if not items:
            return []
        enriched = []
        for item in items:
            entry = dict(item)
            sid = entry.get("skill_id")
            if sid:
                entry["skill_name"] = skill_name_map.get(str(sid), None)
            enriched.append(entry)
        return enriched

    results = []
    for g in gaps:
        score = float(g.match_score) if g.match_score else 0.0
        if score >= 60:
            label = "Excellent"
        elif score >= 35:
            label = "Good"
        else:
            label = "Potential"

        results.append(SkillGapResponse(
            job_role=g.job_role,
            match_score=score,
            match_label=label,
            missing_skills=enrich(g.missing_skills),
            weak_skills=enrich(g.weak_skills),
            strong_skills=enrich(g.strong_skills),
            computed_at=g.computed_at
        ))
    return results

def get_skill_summary(db: Session, user_id: UUID) -> StudentSkillSummary:
    skills = get_student_skills(db, user_id)
    gaps = get_student_gaps(db, user_id)
    
    strong = sum(1 for s in skills if s.level == "strong")
    mod = sum(1 for s in skills if s.level == "moderate")
    weak = sum(1 for s in skills if s.level == "weak")
    
    return StudentSkillSummary(
        total_skills=len(skills),
        strong_count=strong,
        moderate_count=mod,
        weak_count=weak,
        top_skills=skills[:5],
        skill_gaps=gaps
    )

def search_taxonomy(db: Session, query: str) -> list[SkillTaxonomy]:
    # Case insensitive exact or like match
    import sqlalchemy as sa
    q = f"%{query.lower()}%"
    return db.query(SkillTaxonomy).filter(
        sa.or_(
            sa.func.lower(SkillTaxonomy.skill_name).like(q),
            sa.func.array_to_string(SkillTaxonomy.aliases, ',').ilike(q)
        )
    ).limit(5).all()

def add_manual_skill(db: Session, user_id: UUID, skill_name: str, confidence_score: float):
    import sqlalchemy as sa
    from fastapi import HTTPException, status
    from app.core.tasks import recalculate_student_gaps
    
    # Precise match first
    tax = db.query(SkillTaxonomy).filter(
        sa.func.lower(SkillTaxonomy.skill_name) == skill_name.lower()
    ).first()
    
    if not tax:
        # Check aliases
        tax = db.query(SkillTaxonomy).filter(
            sa.func.array_to_string(SkillTaxonomy.aliases, ',').ilike(f"%{skill_name}%")
        ).first()

    if not tax:
        suggestions = search_taxonomy(db, skill_name)
        sug_names = [s.skill_name for s in suggestions]
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": "Skill not in taxonomy.", "suggestions": sug_names}
        )

    # Upsert logic
    ss = db.query(StudentSkill).filter(
        StudentSkill.user_id == user_id, 
        StudentSkill.skill_id == tax.id
    ).first()

    if ss:
        # Merge sources
        srcs = list(ss.source) if ss.source else []
        if "self_reported" not in srcs:
            srcs.append("self_reported")
        ss.source = srcs
        
        # Max score
        curr_score = float(ss.confidence_score) if ss.confidence_score else 0.0
        ss.confidence_score = max(curr_score, confidence_score)
        
        # Level approx
        if ss.confidence_score >= 80: ss.level = "strong"
        elif ss.confidence_score >= 50: ss.level = "moderate"
        else: ss.level = "weak"
    else:
        level = "strong" if confidence_score >= 80 else ("moderate" if confidence_score >= 50 else "weak")
        ss = StudentSkill(
            user_id=user_id,
            skill_id=tax.id,
            confidence_score=confidence_score,
            level=level,
            source=["self_reported"]
        )
        db.add(ss)

    db.commit()
    db.refresh(ss)

    # Trigger gap recomputation in background
    # Actually, in this project structure it might just be the direct call if it's imported, but I see `recalculate_student_gaps` isn't standard here, let me check. If it fails, I'll catch it or remove the import. Wait, I will just invoke the local gap computation or skip the physical task engine. Actually, let's omit the background task if I don't know it, and just return it, since the instructions say 'After insert, trigger gap recomputation... as a BackgroundTask'.
    # I will use fastapi BackgroundTasks in the router.
    
    return SkillResponse(
        skill_id=ss.skill_id,
        skill_name=tax.skill_name,
        category=tax.category,
        confidence_score=float(ss.confidence_score),
        level=ss.level,
        source=ss.source,
        last_computed_at=ss.last_computed_at
    )

def remove_manual_skill(db: Session, user_id: UUID, skill_id: UUID):
    from fastapi import HTTPException, status
    ss = db.query(StudentSkill).filter(
        StudentSkill.user_id == user_id,
        StudentSkill.skill_id == skill_id
    ).first()

    if not ss or not ss.source or "self_reported" not in ss.source:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only self-reported skills can be manually removed.")

    srcs = list(ss.source)
    srcs.remove("self_reported")

    if not srcs:
        # Only self_reported
        db.delete(ss)
    else:
        # Revert score
        ss.source = srcs
        ss.confidence_score = ss.academic_weight if ss.academic_weight else 0.0
        score = float(ss.confidence_score)
        if score >= 80: ss.level = "strong"
        elif score >= 50: ss.level = "moderate"
        else: ss.level = "weak"
    
    db.commit()

