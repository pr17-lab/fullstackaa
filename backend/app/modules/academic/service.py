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

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy import func, select
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

    async def get_student_profile(
        self, db: AsyncSession, user_id: uuid.UUID
    ) -> StudentProfile:
        """Return the StudentProfile for *user_id*.

        Raises HTTP 404 if none exists.
        """
        stmt = select(StudentProfile).filter(StudentProfile.user_id == user_id)
        result = await db.execute(stmt)
        profile = result.scalar_one_or_none()
        if not profile:
            raise HTTPException(status_code=404, detail="Student profile not found")
        return profile

    async def get_student_by_student_id(
        self, db: AsyncSession, student_id: str
    ) -> StudentProfile:
        """Return the StudentProfile whose linked User has the given student_id string."""
        stmt = (
            select(StudentProfile)
            .join(User)
            .filter(User.student_id == student_id)
        )
        result = await db.execute(stmt)
        profile = result.scalar_one_or_none()
        if not profile:
            raise HTTPException(
                status_code=404,
                detail=f"Student with student_id '{student_id}' not found",
            )
        return profile

    # ------------------------------------------------------------------
    # Academic Terms
    # ------------------------------------------------------------------

    async def get_academic_terms(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        *,
        completed_only: bool = True,
    ) -> list[AcademicTerm]:
        """Return academic terms for a student, optionally filtered to
        completed semesters only (i.e., semester <= profile.semester).
        """
        profile = await self.get_student_profile(db, user_id)

        stmt = select(AcademicTerm).filter(AcademicTerm.user_id == user_id)
        if completed_only:
            stmt = stmt.filter(AcademicTerm.semester <= profile.semester)

        stmt = (
            stmt.options(joinedload(AcademicTerm.subjects))
            .order_by(AcademicTerm.year, AcademicTerm.semester)
        )
        
        result = await db.execute(stmt)
        # Using unique() is necessary when using joinedload with select
        return list(result.scalars().unique().all())

    # ------------------------------------------------------------------
    # Subjects / Performance
    # ------------------------------------------------------------------

    async def get_subject_performance(
        self, db: AsyncSession, user_id: uuid.UUID
    ) -> list[Subject]:
        """Return all Subject rows across completed academic terms."""
        terms = await self.get_academic_terms(db, user_id, completed_only=True)
        term_ids = [t.id for t in terms]
        if not term_ids:
            return []
        stmt = select(Subject).filter(Subject.term_id.in_(term_ids))
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_weak_subjects(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        *,
        threshold_marks: float = 60.0,
    ) -> list[Subject]:
        """Return subjects where the student scored below *threshold_marks*."""
        subjects = await self.get_subject_performance(db, user_id)
        return [s for s in subjects if float(s.marks) < threshold_marks]

    async def get_overall_gpa(self, db: AsyncSession, user_id: uuid.UUID) -> Decimal:
        """Return the simple mean GPA across completed terms."""
        terms = await self.get_academic_terms(db, user_id, completed_only=True)
        if not terms:
            return Decimal("0.00")
        avg = sum(float(t.gpa) for t in terms) / len(terms)
        return Decimal(str(round(avg, 2)))

    async def get_branch(self, db: AsyncSession, user_id: uuid.UUID) -> str:
        """Convenience: return the student's branch string."""
        profile = await self.get_student_profile(db, user_id)
        return profile.department
