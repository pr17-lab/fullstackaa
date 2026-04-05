"""
Authentication API routes: login, registration, and current-user lookup.
"""

import math
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings
from app.core.security import verify_password, create_access_token, get_password_hash
from app.models.user import User
from app.models.student_profile import StudentProfile
from app.api.dependencies.database import get_db
from app.api.dependencies.auth import get_current_user
from app.schemas.auth import Token, UserResponse, StudentRegistration
from app.utils.academic import calculate_grade, calculate_grade_points

router = APIRouter(tags=["Authentication"])
limiter = Limiter(key_func=get_remote_address)


# ---------------------------------------------------------------------------
# Background task: compute skills + gaps after registration
# ---------------------------------------------------------------------------

def _run_skill_extraction(user_id: str) -> None:
    """Called as a BackgroundTask after successful student registration."""
    from app.api.dependencies.database import SessionLocal
    from app.modules.skills.engine import compute_skills_for_student, compute_gaps_for_student

    db = SessionLocal()
    try:
        compute_skills_for_student(db, user_id)
        compute_gaps_for_student(db, user_id)
    except Exception as e:
        # Non-fatal — skills can be recomputed later
        import logging
        logging.getLogger(__name__).warning("Skill extraction failed for %s: %s", user_id, e)
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Subject-template helper (no logic change — thin pass-through)
# ---------------------------------------------------------------------------

from .subject_templates import SUBJECT_TEMPLATES  # noqa: E402


@router.get("/subject-templates")
async def get_subject_templates_api(department: str, semester: int):
    """Return an array of subjects for a given department and semester."""
    if department not in SUBJECT_TEMPLATES:
        return []
    return SUBJECT_TEMPLATES[department].get(semester, [])


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

@router.post("/register")
async def register_student(
    payload: StudentRegistration,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    from app.models.academic_term import AcademicTerm
    from app.models.subject import Subject

    # --- Validation ---
    if len(payload.password) < 8 or not any(c.isdigit() for c in payload.password):
        raise HTTPException(
            status_code=422,
            detail="Password must be at least 8 characters and contain a number",
        )
    if payload.department not in ["CSE", "ECE", "AIML", "MECH", "AI&ML"]:
        raise HTTPException(status_code=422, detail="Invalid department")
    if not 1 <= payload.current_semester <= 8:
        raise HTTPException(status_code=422, detail="Semester must be between 1 and 8")

    # --- Uniqueness checks ---
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=422, detail="An account with this email already exists")

    safe_student_id = payload.student_id.strip().upper()
    if db.query(User).filter(User.student_id == safe_student_id).first():
        raise HTTPException(
            status_code=422,
            detail="This Student ID is already taken. Try adding your batch year e.g. S2024001",
        )

    # --- Create user ---
    new_user = User(
        email=payload.email,
        student_id=safe_student_id,
        password_hash=get_password_hash(payload.password),
        is_active=True,
    )
    db.add(new_user)
    db.flush()

    new_profile = StudentProfile(
        user_id=new_user.id,
        name=payload.full_name,
        department=payload.department,
        batch_year=payload.batch_year,
        semester=payload.current_semester,
        performance_status="Average",
        backlog_count=0,
        active_backlog=False,
    )
    db.add(new_profile)
    db.flush()

    # --- Academic records ---
    total_gpa_sum = 0.0
    valid_semesters = 0
    total_sems_recorded = 0

    for record in payload.academic_records:
        sem_year = payload.batch_year + math.floor((record.semester - 1) / 2)
        term = AcademicTerm(
            user_id=new_user.id,
            semester=record.semester,
            year=sem_year,
            gpa=0.0,
        )
        db.add(term)
        db.flush()

        sem_credits = 0
        sem_points = 0
        has_grades = False

        for sub in record.subjects:
            pf = gr = None
            if sub.marks_obtained is not None:
                if not 0 <= sub.marks_obtained <= sub.total_marks:
                    raise HTTPException(status_code=422, detail="Marks must be between 0 and total marks")
                has_grades = True
                pf = "Pass" if sub.marks_obtained >= 40 else "F"
                gr = calculate_grade(sub.marks_obtained)
                sem_credits += sub.credits
                sem_points += calculate_grade_points(gr) * sub.credits

            db.add(Subject(
                term_id=term.id,
                subject_name=sub.subject_name,
                subject_code=sub.subject_code,
                credits=sub.credits,
                marks=sub.marks_obtained,
                total_marks=sub.total_marks,
                grade=gr,
                pass_fail=pf,
            ))

        if has_grades and sem_credits > 0:
            term.gpa = round(sem_points / sem_credits, 2)
            total_gpa_sum += term.gpa
            valid_semesters += 1
        else:
            term.gpa = None

        total_sems_recorded += 1

    # --- CGPA and performance status ---
    cgpa = None
    if valid_semesters > 0:
        cgpa = round(total_gpa_sum / valid_semesters, 2)
        new_profile.cgpa = cgpa
        new_profile.cgpa_10scale = cgpa

        if cgpa >= 8.5:
            new_profile.performance_status = "Excellent"
        elif cgpa >= 6.5:
            new_profile.performance_status = "Good"
        elif cgpa >= 5.0:
            new_profile.performance_status = "Average"
        else:
            new_profile.performance_status = "At Risk"

    db.commit()
    db.refresh(new_profile)

    background_tasks.add_task(_run_skill_extraction, str(new_user.id))

    return {
        "message": "Registration successful",
        "student_id": safe_student_id,
        "user_id": str(new_user.id),
        "cgpa": float(cgpa) if cgpa else None,
        "semesters_recorded": total_sems_recorded,
    }


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

@router.post("/login", response_model=Token)
@limiter.limit("5/minute")
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """
    Authenticate with student_id + password and return a JWT bearer token.
    Rate-limited to 5 requests per minute per IP.
    """
    safe_username = form_data.username.strip().upper()
    user = db.query(User).filter(User.student_id == safe_username).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect student ID or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.is_locked():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is locked due to too many failed login attempts. Please try again later.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not (user.password_hash and verify_password(form_data.password, user.password_hash)):
        user.record_failed_login()
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect student ID or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user.reset_failed_attempts()
    db.commit()

    access_token = create_access_token(
        data={"sub": user.email, "user_id": str(user.id), "student_id": user.student_id},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {"access_token": access_token, "token_type": "bearer"}


# ---------------------------------------------------------------------------
# Current user
# ---------------------------------------------------------------------------

@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return the currently authenticated user with profile information."""
    profile = db.query(StudentProfile).filter(
        StudentProfile.user_id == current_user.id
    ).first()

    return {
        "id": current_user.id,
        "email": current_user.email,
        "student_id": current_user.student_id,
        "name": profile.name if profile else None,
        "branch": profile.department if profile else None,
        "semester": profile.semester if profile else None,
    }
