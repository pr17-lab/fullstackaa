"""
AcademicService — Shared Service-Layer Interface (v1.0)
-------------------------------------------------------
This is the ONLY way the Interview module (or any future module) should
read academic data.  Direct cross-module SQL queries are intentionally
avoided; all access goes through this class.

Usage (inside an interview endpoint):
    from app.modules.academic.service import AcademicService

    academic_svc = AcademicService()
    profile = academic_svc.get_student_profile(db, user_id)
    terms   = academic_svc.get_academic_terms(db, user_id)
"""
from __future__ import annotations

import uuid
from typing import Optional
from decimal import Decimal

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from fastapi import HTTPException

from app.models import StudentProfile, User, AcademicTerm, Subject


class AcademicService:
    """Read-only façade over the academic data layer.

    All methods accept a SQLAlchemy Session and a user_id (UUID) and return
    ORM objects or plain Python values.  They never commit or flush.
    """

    # ------------------------------------------------------------------
    # Student / Profile
    # ------------------------------------------------------------------

    def get_student_profile(
        self, db: Session, user_id: uuid.UUID
    ) -> StudentProfile:
        """Return the StudentProfile for *user_id*.

        Raises HTTP 404 if none exists.
        """
        profile = (
            db.query(StudentProfile)
            .filter(StudentProfile.user_id == user_id)
            .first()
        )
        if not profile:
            raise HTTPException(status_code=404, detail="Student profile not found")
        return profile

    def get_student_by_student_id(
        self, db: Session, student_id: str
    ) -> StudentProfile:
        """Return the StudentProfile whose linked User has the given student_id string."""
        profile = (
            db.query(StudentProfile)
            .join(User)
            .filter(User.student_id == student_id)
            .first()
        )
        if not profile:
            raise HTTPException(
                status_code=404,
                detail=f"Student with student_id '{student_id}' not found",
            )
        return profile

    # ------------------------------------------------------------------
    # Academic Terms
    # ------------------------------------------------------------------

    def get_academic_terms(
        self,
        db: Session,
        user_id: uuid.UUID,
        *,
        completed_only: bool = True,
    ) -> list[AcademicTerm]:
        """Return academic terms for a student, optionally filtered to
        completed semesters only (i.e., semester <= profile.semester).
        """
        profile = self.get_student_profile(db, user_id)

        query = db.query(AcademicTerm).filter(
            AcademicTerm.user_id == user_id
        )
        if completed_only:
            query = query.filter(AcademicTerm.semester <= profile.semester)

        return (
            query.options(joinedload(AcademicTerm.subjects))
            .order_by(AcademicTerm.year, AcademicTerm.semester)
            .all()
        )

    # ------------------------------------------------------------------
    # Subjects / Performance
    # ------------------------------------------------------------------

    def get_subject_performance(
        self, db: Session, user_id: uuid.UUID
    ) -> list[Subject]:
        """Return all Subject rows across completed academic terms."""
        terms = self.get_academic_terms(db, user_id, completed_only=True)
        term_ids = [t.id for t in terms]
        if not term_ids:
            return []
        return db.query(Subject).filter(Subject.term_id.in_(term_ids)).all()

    def get_weak_subjects(
        self,
        db: Session,
        user_id: uuid.UUID,
        *,
        threshold_marks: float = 60.0,
    ) -> list[Subject]:
        """Return subjects where the student scored below *threshold_marks*."""
        subjects = self.get_subject_performance(db, user_id)
        return [s for s in subjects if float(s.marks) < threshold_marks]

    def get_overall_gpa(self, db: Session, user_id: uuid.UUID) -> Decimal:
        """Return the simple mean GPA across completed terms."""
        terms = self.get_academic_terms(db, user_id, completed_only=True)
        if not terms:
            return Decimal("0.00")
        avg = sum(float(t.gpa) for t in terms) / len(terms)
        return Decimal(str(round(avg, 2)))

    def get_branch(self, db: Session, user_id: uuid.UUID) -> str:
        """Convenience: return the student's branch string."""
        return self.get_student_profile(db, user_id).department
