"""
Academic module routes.
Provides the authenticated student with the ability to update
their own subject marks (which auto-recalculates grade and term GPA).
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel, Field
import uuid

from app.core.database import get_db
from app.api.dependencies.auth import get_current_user
from app.models.user import User
from app.models.subject import Subject
from app.models.academic_term import AcademicTerm
from app.models.student_profile import StudentProfile
from app.utils.academic import calculate_grade, calculate_grade_points

router = APIRouter()


# ─── Background Tasks ────────────────────────────────────────────────────────

def _run_skill_extraction(user_id: str) -> None:
    """Recomputes skills and gaps after subject marks are updated."""
    from app.core.database import SessionLocal
    from app.modules.skills.engine import compute_skills_for_student, compute_gaps_for_student

    db = SessionLocal()
    try:
        compute_skills_for_student(db, user_id)
        compute_gaps_for_student(db, user_id)
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning("Skill extraction failed for %s: %s", user_id, e)
    finally:
        db.close()


# ─── Schemas ────────────────────────────────────────────────────────────────

class SubjectUpdateRequest(BaseModel):
    """Only marks (and optionally subject_name) can be changed by the student."""
    marks: Optional[float] = Field(None, ge=0, le=100, description="Marks obtained (0-100)")
    subject_name: Optional[str] = Field(None, min_length=1, max_length=255)


class SubjectUpdateResponse(BaseModel):
    id: str
    subject_name: str
    subject_code: str
    credits: int
    marks: float
    grade: str
    pass_fail: str
    term_id: str
    term_gpa: float  # recalculated GPA for the term

    class Config:
        from_attributes = True


# ─── Helper: recalculate term GPA ────────────────────────────────────────────

def _recalculate_term_gpa(db: Session, term: AcademicTerm) -> float:
    """Recompute weighted GPA for a term and persist it."""
    total_credits = 0
    total_points = 0.0
    for subj in term.subjects:
        if subj.marks is not None and subj.credits:
            grade = calculate_grade(float(subj.marks))
            gp = calculate_grade_points(grade)
            total_credits += subj.credits
            total_points += gp * subj.credits
    new_gpa = round(total_points / total_credits, 2) if total_credits > 0 else 0.0
    term.gpa = new_gpa
    db.commit()
    return new_gpa


# ─── Endpoints ───────────────────────────────────────────────────────────────

@router.patch("/subjects/{subject_id}", response_model=SubjectUpdateResponse)
async def update_subject(
    subject_id: uuid.UUID,
    payload: SubjectUpdateRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update a subject's marks (and optionally name) for the authenticated student.
    - Verifies the subject belongs to the current user's term.
    - Auto-recalculates grade, pass/fail, and the term's GPA.
    """
    # Fetch subject
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    # Ownership check: term must belong to this user
    term = db.query(AcademicTerm).filter(AcademicTerm.id == subject.term_id).first()
    if not term or str(term.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorised to edit this subject",
        )

    # Apply updates
    if payload.subject_name is not None:
        subject.subject_name = payload.subject_name.strip()

    if payload.marks is not None:
        subject.marks = round(payload.marks, 2)
        grade = calculate_grade(float(subject.marks))
        subject.grade = grade
        subject.pass_fail = "Pass" if float(subject.marks) >= 40 else "F"

    db.commit()
    db.refresh(subject)

    # Recalculate GPA for the term
    new_gpa = _recalculate_term_gpa(db, term)

    # Also update CGPA on the student profile
    profile = db.query(StudentProfile).filter(
        StudentProfile.user_id == current_user.id
    ).first()
    if profile:
        all_terms = db.query(AcademicTerm).filter(
            AcademicTerm.user_id == current_user.id,
            AcademicTerm.gpa.isnot(None),
        ).all()
        if all_terms:
            cgpa = round(sum(float(t.gpa) for t in all_terms) / len(all_terms), 2)
            profile.cgpa = cgpa
            profile.cgpa_10scale = cgpa
            if cgpa >= 8.5:
                profile.performance_status = "Excellent"
            elif cgpa >= 6.5:
                profile.performance_status = "Good"
            elif cgpa >= 5.0:
                profile.performance_status = "Average"
            else:
                profile.performance_status = "At Risk"
            db.commit()

    # Trigger async re-computation of skills and gaps based on the new marks
    background_tasks.add_task(_run_skill_extraction, str(current_user.id))

    return SubjectUpdateResponse(
        id=str(subject.id),
        subject_name=subject.subject_name,
        subject_code=subject.subject_code,
        credits=subject.credits,
        marks=float(subject.marks),
        grade=subject.grade or "",
        pass_fail=subject.pass_fail or "",
        term_id=str(subject.term_id),
        term_gpa=new_gpa,
    )
