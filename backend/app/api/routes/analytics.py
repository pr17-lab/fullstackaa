"""
Analytics API routes — GPA trends, subject performance, semester comparisons,
cohort statistics, and system-wide overview.
"""

from decimal import Decimal
from typing import Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.core.database import get_db
from app.models import StudentProfile, User, AcademicTerm, Subject
from app.schemas import (
    GPATrend,
    GPATrendPoint,
    SubjectPerformance,
    SubjectPerformanceItem,
    SemesterComparison,
    SemesterStats,
    StudentAnalyticsSummary,
    CohortStats,
    AnalyticsOverview,
    GradeDistribution,
    StudentProfileResponse,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# Private helper: resolve student_id (tries user_id first, then profile_id)
# ---------------------------------------------------------------------------

def _get_student_or_404(db: Session, student_id: uuid.UUID) -> StudentProfile:
    """Look up a StudentProfile by user_id, falling back to profile id."""
    student = db.query(StudentProfile).filter(StudentProfile.user_id == student_id).first()
    if not student:
        student = db.query(StudentProfile).filter(StudentProfile.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student


def _determine_trend(terms: list) -> str:
    """Return 'improving', 'declining', or 'stable' based on GPA history."""
    if len(terms) < 2:
        return "stable"
    recent_avg = sum(float(t.gpa) for t in terms[-2:]) / 2
    earlier_avg = sum(float(t.gpa) for t in terms[:2]) / 2
    if recent_avg > earlier_avg + 0.3:
        return "improving"
    if recent_avg < earlier_avg - 0.3:
        return "declining"
    return "stable"


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/gpa-trend/{student_id}", response_model=GPATrend)
async def get_gpa_trend(
    student_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    """Get GPA trend over time for a specific student (completed semesters only)."""
    student = _get_student_or_404(db, student_id)

    terms = (
        db.query(AcademicTerm)
        .filter(
            AcademicTerm.user_id == student.user_id,
            AcademicTerm.semester <= student.semester,
        )
        .order_by(AcademicTerm.year, AcademicTerm.semester)
        .all()
    )

    if not terms:
        return GPATrend(
            student_id=student_id,
            data_points=[],
            average_gpa=Decimal("0.0"),
            trend="stable",
        )

    data_points = [
        GPATrendPoint(semester=t.semester, year=t.year, gpa=t.gpa, term_id=t.id)
        for t in terms
    ]

    # Weighted CGPA by credits
    total_credits = 0
    weighted_sum = 0.0
    for term in terms:
        subjects = db.query(Subject).filter(Subject.term_id == term.id).all()
        term_credits = sum(s.credits for s in subjects)
        total_credits += term_credits
        weighted_sum += float(term.gpa) * term_credits

    avg_gpa = (
        weighted_sum / total_credits
        if total_credits > 0
        else sum(float(t.gpa) for t in terms) / len(terms)
    )

    return GPATrend(
        student_id=student_id,
        data_points=data_points,
        average_gpa=Decimal(str(avg_gpa)),
        trend=_determine_trend(terms),
    )


@router.get("/subject-performance", response_model=SubjectPerformance)
async def get_subject_performance(
    student_id: uuid.UUID = Query(..., description="Student ID"),
    db: Session = Depends(get_db),
):
    """Analyse performance across all subjects for a student."""
    student = _get_student_or_404(db, student_id)

    subjects = (
        db.query(
            Subject.subject_code,
            Subject.subject_name,
            func.avg(Subject.marks).label("average_marks"),
            func.sum(Subject.credits).label("total_credits"),
            func.count(Subject.id).label("frequency"),
        )
        .join(AcademicTerm)
        .filter(AcademicTerm.user_id == student.user_id)
        .group_by(Subject.subject_code, Subject.subject_name)
        .all()
    )

    if not subjects:
        raise HTTPException(status_code=404, detail="No subject records found")

    performance_items = [
        SubjectPerformanceItem(
            subject_code=s.subject_code,
            subject_name=s.subject_name,
            average_marks=Decimal(str(s.average_marks)),
            total_credits=int(s.total_credits),
            frequency=s.frequency,
        )
        for s in subjects
    ]

    strongest = max(subjects, key=lambda x: x.average_marks)
    weakest = min(subjects, key=lambda x: x.average_marks)

    return SubjectPerformance(
        student_id=student_id,
        subjects=performance_items,
        strongest_subject=strongest.subject_name,
        weakest_subject=weakest.subject_name,
    )


@router.get("/semester-comparison", response_model=SemesterComparison)
async def get_semester_comparison(
    student_id: uuid.UUID = Query(..., description="Student ID"),
    db: Session = Depends(get_db),
):
    """Compare performance across different semesters."""
    student = _get_student_or_404(db, student_id)

    terms = (
        db.query(AcademicTerm)
        .filter(
            AcademicTerm.user_id == student.user_id,
            AcademicTerm.semester <= student.semester,
        )
        .order_by(AcademicTerm.year, AcademicTerm.semester)
        .all()
    )

    if not terms:
        raise HTTPException(status_code=404, detail="No academic records found")

    semester_stats = []
    for term in terms:
        subjects = db.query(Subject).filter(Subject.term_id == term.id).all()
        subjects_count = len(subjects)
        total_credits = sum(s.credits for s in subjects)
        avg_marks = sum(float(s.marks) for s in subjects) / subjects_count if subjects_count > 0 else 0.0

        semester_stats.append(SemesterStats(
            semester=term.semester,
            year=term.year,
            gpa=term.gpa,
            total_credits=total_credits,
            subjects_count=subjects_count,
            average_marks=Decimal(str(avg_marks)),
        ))

    best_semester = max(semester_stats, key=lambda x: x.gpa)
    current_semester = semester_stats[-1] if semester_stats else best_semester

    return SemesterComparison(
        student_id=student_id,
        semesters=semester_stats,
        best_semester=best_semester,
        current_semester=current_semester,
    )


@router.get("/student/{student_id}/summary", response_model=StudentAnalyticsSummary)
async def get_student_analytics_summary(
    student_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    """Get comprehensive analytics summary for a student."""
    student = _get_student_or_404(db, student_id)

    terms = (
        db.query(AcademicTerm)
        .filter(
            AcademicTerm.user_id == student.user_id,
            AcademicTerm.semester <= student.semester,
        )
        .all()
    )

    if not terms:
        return StudentAnalyticsSummary(
            student_id=student_id,
            student_name=student.name,
            branch=student.department,
            current_semester=student.semester,
            overall_gpa=Decimal("0.0"),
            total_credits=0,
            total_subjects=0,
            gpa_trend="stable",
            performance_percentile=Decimal("50.0"),
        )

    overall_gpa = sum(float(t.gpa) for t in terms) / len(terms)

    total_subjects = (
        db.query(func.count(Subject.id))
        .join(AcademicTerm)
        .filter(AcademicTerm.user_id == student.user_id)
        .scalar() or 0
    )
    total_credits = (
        db.query(func.sum(Subject.credits))
        .join(AcademicTerm)
        .filter(AcademicTerm.user_id == student.user_id)
        .scalar() or 0
    )

    # Percentile: single-query cohort GPA aggregation (no N+1)
    cohort_gpa_rows = (
        db.query(func.avg(AcademicTerm.gpa).label("avg_gpa"))
        .join(StudentProfile, StudentProfile.user_id == AcademicTerm.user_id)
        .filter(
            StudentProfile.department == student.department,
            StudentProfile.semester == student.semester,
        )
        .group_by(AcademicTerm.user_id)
        .all()
    )
    cohort_gpas = [float(row.avg_gpa) for row in cohort_gpa_rows if row.avg_gpa is not None]
    if cohort_gpas and overall_gpa > 0:
        better_count = sum(1 for gpa in cohort_gpas if gpa < overall_gpa)
        percentile = (better_count / len(cohort_gpas)) * 100
    else:
        percentile = 50.0

    return StudentAnalyticsSummary(
        student_id=student_id,
        student_name=student.name,
        branch=student.department,
        current_semester=student.semester,
        overall_gpa=Decimal(str(overall_gpa)),
        total_credits=total_credits,
        total_subjects=total_subjects,
        gpa_trend=_determine_trend(terms),
        performance_percentile=Decimal(str(percentile)),
    )


@router.get("/cohort-stats", response_model=CohortStats)
async def get_cohort_statistics(
    branch: str = Query(..., description="Branch name"),
    semester: int = Query(..., ge=1, le=10, description="Semester"),
    db: Session = Depends(get_db),
):
    """Get statistical analysis for a specific cohort (branch + semester)."""
    students = (
        db.query(StudentProfile)
        .filter(StudentProfile.department == branch, StudentProfile.semester == semester)
        .all()
    )
    if not students:
        raise HTTPException(status_code=404, detail="No students found for this cohort")

    gpas = []
    for student in students:
        terms = db.query(AcademicTerm).filter(AcademicTerm.user_id == student.user_id).all()
        if terms:
            gpas.append(sum(float(t.gpa) for t in terms) / len(terms))

    if not gpas:
        raise HTTPException(status_code=404, detail="No academic records found for cohort")

    avg_gpa = sum(gpas) / len(gpas)
    sorted_gpas = sorted(gpas)
    median_gpa = sorted_gpas[len(sorted_gpas) // 2]

    gpa_distribution = {
        "9.0-10.0": sum(1 for g in gpas if g >= 9.0),
        "8.0-8.9": sum(1 for g in gpas if 8.0 <= g < 9.0),
        "7.0-7.9": sum(1 for g in gpas if 7.0 <= g < 8.0),
        "6.0-6.9": sum(1 for g in gpas if 6.0 <= g < 7.0),
        "Below 6.0": sum(1 for g in gpas if g < 6.0),
    }

    return CohortStats(
        branch=branch,
        semester=semester,
        total_students=len(students),
        average_gpa=Decimal(str(avg_gpa)),
        median_gpa=Decimal(str(median_gpa)),
        top_gpa=Decimal(str(max(gpas))),
        bottom_gpa=Decimal(str(min(gpas))),
        gpa_distribution=gpa_distribution,
    )


@router.get("/overview", response_model=AnalyticsOverview)
async def get_analytics_overview(
    limit: int = Query(10, ge=1, le=50, description="Top performers limit"),
    db: Session = Depends(get_db),
):
    """Get overall analytics overview across all students."""
    all_students = db.query(StudentProfile).all()
    if not all_students:
        raise HTTPException(status_code=404, detail="No students found")

    all_gpas: list[float] = []
    student_summaries: list[dict] = []

    for student in all_students:
        terms = db.query(AcademicTerm).filter(AcademicTerm.user_id == student.user_id).all()
        if terms:
            avg_gpa = sum(float(t.gpa) for t in terms) / len(terms)
            all_gpas.append(avg_gpa)
            student_summaries.append({"student": student, "gpa": avg_gpa})

    overall_avg_gpa = sum(all_gpas) / len(all_gpas) if all_gpas else 0.0

    grade_ranges = [
        ("A+ (9.5-10.0)", 9.5, 10.0),
        ("A (9.0-9.4)", 9.0, 9.5),
        ("B+ (8.5-8.9)", 8.5, 9.0),
        ("B (8.0-8.4)", 8.0, 8.5),
        ("C+ (7.5-7.9)", 7.5, 8.0),
        ("C (7.0-7.4)", 7.0, 7.5),
        ("Below C (<7.0)", 0, 7.0),
    ]
    grade_dist = [
        GradeDistribution(
            grade=label,
            count=(c := sum(1 for g in all_gpas if low <= g < high or (high == 10.0 and g == 10.0))),
            percentage=Decimal(str((c / len(all_gpas) * 100) if all_gpas else 0)),
        )
        for label, low, high in grade_ranges
    ]

    top_students = sorted(student_summaries, key=lambda x: x["gpa"], reverse=True)[:limit]
    top_performers = []
    for item in top_students:
        student = item["student"]
        total_subjects = (
            db.query(func.count(Subject.id)).join(AcademicTerm)
            .filter(AcademicTerm.user_id == student.user_id).scalar() or 0
        )
        total_credits = (
            db.query(func.sum(Subject.credits)).join(AcademicTerm)
            .filter(AcademicTerm.user_id == student.user_id).scalar() or 0
        )
        top_performers.append(StudentAnalyticsSummary(
            student_id=student.id,
            student_name=student.name,
            branch=student.department,
            current_semester=student.semester,
            overall_gpa=Decimal(str(item["gpa"])),
            total_credits=total_credits,
            total_subjects=total_subjects,
            gpa_trend="stable",
            performance_percentile=Decimal("95.0"),
        ))

    return AnalyticsOverview(
        total_students=len(all_students),
        average_gpa=Decimal(str(overall_avg_gpa)),
        grade_distribution=grade_dist,
        top_performers=top_performers,
    )
