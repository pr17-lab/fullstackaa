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

from sqlalchemy.orm import Session
from sqlalchemy import func, select
from fastapi import HTTPException

from app.models import StudentProfile, User


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
        profile = db.query(StudentProfile).filter(StudentProfile.user_id == user_id).first()
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



    def get_branch(self, db: Session, user_id: uuid.UUID) -> str:
        """Convenience: return the student's branch string."""
        profile = self.get_student_profile(db, user_id)
        return profile.department
