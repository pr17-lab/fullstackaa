"""
Analytics API routes — GPA trends, subject performance, semester comparisons,
cohort statistics, and system-wide overview.
"""

from decimal import Decimal
from typing import Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, desc, select, case

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

from app.api.dependencies.auth import RequireRole

router = APIRouter(dependencies=[Depends(RequireRole(['admin', 'faculty']))])


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
    db: AsyncSession = Depends(get_db),
):
    """Get overall analytics overview across all students."""
    
    # 1. Total students
    stmt_total = select(func.count(StudentProfile.id))
    total_students_result = await db.execute(stmt_total)
    total_students = total_students_result.scalar() or 0

    if total_students == 0:
        raise HTTPException(status_code=404, detail="No students found")

    # 2. Overall average GPA
    stmt_avg_gpa = select(func.avg(AcademicTerm.gpa))
    avg_gpa_result = await db.execute(stmt_avg_gpa)
    overall_avg_gpa = avg_gpa_result.scalar() or 0.0

    # 3. Grade distribution & student averages
    student_gpa_cte = (
        select(
            AcademicTerm.user_id,
            func.avg(AcademicTerm.gpa).label('avg_gpa')
        )
        .group_by(AcademicTerm.user_id)
        .cte('student_gpa')
    )

    stmt_dist = select(
        func.sum(case((student_gpa_cte.c.avg_gpa >= 9.5, 1), else_=0)).label('A+'),
        func.sum(case((student_gpa_cte.c.avg_gpa >= 9.0) & (student_gpa_cte.c.avg_gpa < 9.5), 1, else_=0)).label('A'),
        func.sum(case((student_gpa_cte.c.avg_gpa >= 8.5) & (student_gpa_cte.c.avg_gpa < 9.0), 1, else_=0)).label('B+'),
        func.sum(case((student_gpa_cte.c.avg_gpa >= 8.0) & (student_gpa_cte.c.avg_gpa < 8.5), 1, else_=0)).label('B'),
        func.sum(case((student_gpa_cte.c.avg_gpa >= 7.5) & (student_gpa_cte.c.avg_gpa < 8.0), 1, else_=0)).label('C+'),
        func.sum(case((student_gpa_cte.c.avg_gpa >= 7.0) & (student_gpa_cte.c.avg_gpa < 7.5), 1, else_=0)).label('C'),
        func.sum(case((student_gpa_cte.c.avg_gpa < 7.0, 1), else_=0)).label('Below C')
    )
    
    dist_result = await db.execute(stmt_dist)
    dist_row = dist_result.fetchone()
    
    grade_ranges = [
        ("A+ (9.5-10.0)", dist_row[0] or 0),
        ("A (9.0-9.4)", dist_row[1] or 0),
        ("B+ (8.5-8.9)", dist_row[2] or 0),
        ("B (8.0-8.4)", dist_row[3] or 0),
        ("C+ (7.5-7.9)", dist_row[4] or 0),
        ("C (7.0-7.4)", dist_row[5] or 0),
        ("Below C (<7.0)", dist_row[6] or 0),
    ]
    
    total_with_gpa = sum(count for _, count in grade_ranges)
    grade_dist = [
        GradeDistribution(
            grade=label,
            count=count,
            percentage=Decimal(str((count / total_with_gpa * 100) if total_with_gpa > 0 else 0))
        )
        for label, count in grade_ranges
    ]

    # 4. Top performers with window functions
    stmt_top = (
        select(
            StudentProfile,
            student_gpa_cte.c.avg_gpa,
            func.count(Subject.id).label('total_subjects'),
            func.sum(Subject.credits).label('total_credits'),
            func.percent_rank().over(
                partition_by=StudentProfile.department,
                order_by=student_gpa_cte.c.avg_gpa
            ).label('cohort_percentile')
        )
        .join(student_gpa_cte, StudentProfile.user_id == student_gpa_cte.c.user_id)
        .outerjoin(AcademicTerm, AcademicTerm.user_id == StudentProfile.user_id)
        .outerjoin(Subject, Subject.term_id == AcademicTerm.id)
        .group_by(StudentProfile.id, student_gpa_cte.c.avg_gpa)
        .order_by(student_gpa_cte.c.avg_gpa.desc())
        .limit(limit)
    )
    
    top_result = await db.execute(stmt_top)
    top_rows = top_result.all()

    top_performers = [
        StudentAnalyticsSummary(
            student_id=row.StudentProfile.id,
            student_name=row.StudentProfile.name,
            branch=row.StudentProfile.department,
            current_semester=row.StudentProfile.semester,
            overall_gpa=Decimal(str(round(row.avg_gpa or 0.0, 2))),
            total_credits=row.total_credits or 0,
            total_subjects=row.total_subjects or 0,
            gpa_trend="stable",
            performance_percentile=Decimal(str(round((row.cohort_percentile or 0.0) * 100, 1)))
        )
        for row in top_rows
    ]

    return AnalyticsOverview(
        total_students=total_students,
        average_gpa=Decimal(str(round(overall_avg_gpa, 2))),
        grade_distribution=grade_dist,
        top_performers=top_performers,
    )
