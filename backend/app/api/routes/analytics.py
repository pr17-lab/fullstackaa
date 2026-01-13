from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from decimal import Decimal
import uuid

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
    StudentProfileResponse
)

router = APIRouter()

@router.get("/gpa-trend/{student_id}", response_model=GPATrend)
async def get_gpa_trend(
    student_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """Get GPA trend over time for a specific student."""
    # Verify student exists
    student = db.query(StudentProfile).filter(StudentProfile.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Get all academic terms
    terms = db.query(AcademicTerm).filter(
        AcademicTerm.user_id == student.user_id
    ).order_by(AcademicTerm.year, AcademicTerm.semester).all()
    
    # Return empty state if no academic records found (instead of 404)
    if not terms:
        return GPATrend(
            student_id=student_id,
            data_points=[],
            average_gpa=Decimal("0.0"),
            trend="stable"
        )
    
    # Build data points
    data_points = [
        GPATrendPoint(
            semester=term.semester,
            year=term.year,
            gpa=term.gpa,
            term_id=term.id
        )
        for term in terms
    ]
    
    # Calculate average GPA (safe from division by zero due to check above)
    avg_gpa = sum(float(term.gpa) for term in terms) / len(terms)
    
    # Determine trend
    if len(terms) >= 2:
        recent_avg = sum(float(t.gpa) for t in terms[-2:]) / 2
        earlier_avg = sum(float(t.gpa) for t in terms[:2]) / 2
        
        if recent_avg > earlier_avg + 0.3:
            trend = "improving"
        elif recent_avg < earlier_avg - 0.3:
            trend = "declining"
        else:
            trend = "stable"
    else:
        trend = "stable"
    
    return GPATrend(
        student_id=student_id,
        data_points=data_points,
        average_gpa=Decimal(str(avg_gpa)),
        trend=trend
    )

@router.get("/subject-performance", response_model=SubjectPerformance)
async def get_subject_performance(
    student_id: uuid.UUID = Query(..., description="Student ID"),
    db: Session = Depends(get_db)
):
    """Analyze performance across all subjects for a student."""
    # Verify student exists
    student = db.query(StudentProfile).filter(StudentProfile.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Get all subjects across all terms
    subjects = db.query(
        Subject.subject_code,
        Subject.subject_name,
        func.avg(Subject.marks).label('average_marks'),
        func.sum(Subject.credits).label('total_credits'),
        func.count(Subject.id).label('frequency')
    ).join(AcademicTerm).filter(
        AcademicTerm.user_id == student.user_id
    ).group_by(
        Subject.subject_code, Subject.subject_name
    ).all()
    
    if not subjects:
        raise HTTPException(status_code=404, detail="No subject records found")
    
    # Build performance items
    performance_items = [
        SubjectPerformanceItem(
            subject_code=subj.subject_code,
            subject_name=subj.subject_name,
            average_marks=Decimal(str(subj.average_marks)),
            total_credits=int(subj.total_credits),
            frequency=subj.frequency
        )
        for subj in subjects
    ]
    
    # Find strongest and weakest subjects
    strongest = max(subjects, key=lambda x: x.average_marks)
    weakest = min(subjects, key=lambda x: x.average_marks)
    
    return SubjectPerformance(
        student_id=student_id,
        subjects=performance_items,
        strongest_subject=strongest.subject_name,
        weakest_subject=weakest.subject_name
    )

@router.get("/semester-comparison", response_model=SemesterComparison)
async def get_semester_comparison(
    student_id: uuid.UUID = Query(..., description="Student ID"),
    db: Session = Depends(get_db)
):
    """Compare performance across different semesters."""
    # Verify student exists
    student = db.query(StudentProfile).filter(StudentProfile.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Get all terms with aggregated statistics
    terms = db.query(AcademicTerm).filter(
        AcademicTerm.user_id == student.user_id
    ).order_by(AcademicTerm.year, AcademicTerm.semester).all()
    
    if not terms:
        raise HTTPException(status_code=404, detail="No academic records found")
    
    semester_stats = []
    for term in terms:
        # Get subjects for this term
        subjects = db.query(Subject).filter(Subject.term_id == term.id).all()
        
        total_credits = sum(s.credits for s in subjects)
        subjects_count = len(subjects)
        avg_marks = sum(float(s.marks) for s in subjects) / subjects_count if subjects_count > 0 else 0
        
        semester_stats.append(
            SemesterStats(
                semester=term.semester,
                year=term.year,
                gpa=term.gpa,
                total_credits=total_credits,
                subjects_count=subjects_count,
                average_marks=Decimal(str(avg_marks))
            )
        )
    
    # Find best semester
    best_semester = max(semester_stats, key=lambda x: x.gpa)
    current_semester = semester_stats[-1] if semester_stats else best_semester
    
    return SemesterComparison(
        student_id=student_id,
        semesters=semester_stats,
        best_semester=best_semester,
        current_semester=current_semester
    )

@router.get("/student/{student_id}/summary", response_model=StudentAnalyticsSummary)
async def get_student_analytics_summary(
    student_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """Get comprehensive analytics summary for a student."""
    # Get student profile
    student = db.query(StudentProfile).filter(StudentProfile.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Get academic terms
    terms = db.query(AcademicTerm).filter(
        AcademicTerm.user_id == student.user_id
    ).all()
    
    # Handle empty terms with defensive defaults
    if not terms or len(terms) == 0:
        # Return default summary for student with no academic records
        return StudentAnalyticsSummary(
            student_id=student_id,
            student_name=student.name,
            branch=student.branch,
            current_semester=student.semester,
            overall_gpa=Decimal("0.0"),
            total_credits=0,
            total_subjects=0,
            gpa_trend="stable",
            performance_percentile=Decimal("50.0")
        )
    
    # Calculate overall GPA (safe from division by zero)
    overall_gpa = sum(float(t.gpa) for t in terms) / len(terms)
    
    # Get total credits and subjects
    total_subjects = db.query(func.count(Subject.id)).join(
        AcademicTerm
    ).filter(AcademicTerm.user_id == student.user_id).scalar() or 0
    
    total_credits = db.query(func.sum(Subject.credits)).join(
        AcademicTerm
    ).filter(AcademicTerm.user_id == student.user_id).scalar() or 0
    
    # Determine GPA trend
    if len(terms) >= 2:
        recent_avg = sum(float(t.gpa) for t in terms[-2:]) / 2
        earlier_avg = sum(float(t.gpa) for t in terms[:2]) / 2
        
        if recent_avg > earlier_avg + 0.3:
            gpa_trend = "improving"
        elif recent_avg < earlier_avg - 0.3:
            gpa_trend = "declining"
        else:
            gpa_trend = "stable"
    else:
        gpa_trend = "stable"
    
    # Calculate percentile rank (simplified - compares to branch/semester cohort)
    cohort_students = db.query(StudentProfile).filter(
        StudentProfile.branch == student.branch,
        StudentProfile.semester == student.semester
    ).all()
    
    # Get GPAs for cohort
    cohort_gpas = []
    for cohort_student in cohort_students:
        student_terms = db.query(AcademicTerm).filter(
            AcademicTerm.user_id == cohort_student.user_id
        ).all()
        if student_terms:
            cohort_gpa = sum(float(t.gpa) for t in student_terms) / len(student_terms)
            cohort_gpas.append(cohort_gpa)
    
    # Calculate percentile
    if cohort_gpas and overall_gpa > 0:
        better_count = sum(1 for gpa in cohort_gpas if gpa < overall_gpa)
        percentile = (better_count / len(cohort_gpas)) * 100
    else:
        percentile = 50.0
    
    return StudentAnalyticsSummary(
        student_id=student_id,
        student_name=student.name,
        branch=student.branch,
        current_semester=student.semester,
        overall_gpa=Decimal(str(overall_gpa)),
        total_credits=total_credits,
        total_subjects=total_subjects,
        gpa_trend=gpa_trend,
        performance_percentile=Decimal(str(percentile))
    )

@router.get("/cohort-stats", response_model=CohortStats)
async def get_cohort_statistics(
    branch: str = Query(..., description="Branch name"),
    semester: int = Query(..., ge=1, le=10, description="Semester"),
    db: Session = Depends(get_db)
):
    """Get statistical analysis for a specific cohort (branch + semester)."""
    # Get all students in cohort
    students = db.query(StudentProfile).filter(
        StudentProfile.branch == branch,
        StudentProfile.semester == semester
    ).all()
    
    if not students:
        raise HTTPException(status_code=404, detail="No students found for this cohort")
    
    # Calculate GPAs for all students
    gpas = []
    for student in students:
        terms = db.query(AcademicTerm).filter(
            AcademicTerm.user_id == student.user_id
        ).all()
        if terms:
            avg_gpa = sum(float(t.gpa) for t in terms) / len(terms)
            gpas.append(avg_gpa)
    
    if not gpas:
        raise HTTPException(status_code=404, detail="No academic records found for cohort")
    
    # Calculate statistics
    avg_gpa = sum(gpas) / len(gpas)
    sorted_gpas = sorted(gpas)
    median_gpa = sorted_gpas[len(sorted_gpas) // 2]
    top_gpa = max(gpas)
    bottom_gpa = min(gpas)
    
    # GPA distribution
    gpa_distribution = {
        "9.0-10.0": sum(1 for gpa in gpas if gpa >= 9.0),
        "8.0-8.9": sum(1 for gpa in gpas if 8.0 <= gpa < 9.0),
        "7.0-7.9": sum(1 for gpa in gpas if 7.0 <= gpa < 8.0),
        "6.0-6.9": sum(1 for gpa in gpas if 6.0 <= gpa < 7.0),
        "Below 6.0": sum(1 for gpa in gpas if gpa < 6.0),
    }
    
    return CohortStats(
        branch=branch,
        semester=semester,
        total_students=len(students),
        average_gpa=Decimal(str(avg_gpa)),
        median_gpa=Decimal(str(median_gpa)),
        top_gpa=Decimal(str(top_gpa)),
        bottom_gpa=Decimal(str(bottom_gpa)),
        gpa_distribution=gpa_distribution
    )

@router.get("/overview", response_model=AnalyticsOverview)
async def get_analytics_overview(
    limit: int = Query(10, ge=1, le=50, description="Top performers limit"),
    db: Session = Depends(get_db)
):
    """Get overall analytics overview across all students."""
    # Get all students
    all_students = db.query(StudentProfile).all()
    
    if not all_students:
        raise HTTPException(status_code=404, detail="No students found")
    
    # Calculate overall statistics
    all_gpas = []
    student_summaries = []
    
    for student in all_students:
        terms = db.query(AcademicTerm).filter(
            AcademicTerm.user_id == student.user_id
        ).all()
        
        if terms:
            avg_gpa = sum(float(t.gpa) for t in terms) / len(terms)
            all_gpas.append(avg_gpa)
            
            # Create summary for sorting
            student_summaries.append({
                'student': student,
                'gpa': avg_gpa,
                'terms': terms
            })
    
    overall_avg_gpa = sum(all_gpas) / len(all_gpas) if all_gpas else 0.0
    
    # Grade distribution
    grade_ranges = [
        ("A+ (9.5-10.0)", 9.5, 10.0),
        ("A (9.0-9.4)", 9.0, 9.5),
        ("B+ (8.5-8.9)", 8.5, 9.0),
        ("B (8.0-8.4)", 8.0, 8.5),
        ("C+ (7.5-7.9)", 7.5, 8.0),
        ("C (7.0-7.4)", 7.0, 7.5),
        ("Below C (<7.0)", 0, 7.0),
    ]
    
    grade_dist = []
    for grade_label, low, high in grade_ranges:
        count = sum(1 for gpa in all_gpas if low <= gpa < high or (high == 10.0 and gpa == 10.0))
        percentage = (count / len(all_gpas) * 100) if all_gpas else 0
        grade_dist.append(
            GradeDistribution(
                grade=grade_label,
                count=count,
                percentage=Decimal(str(percentage))
            )
        )
    
    # Get top performers
    top_students = sorted(student_summaries, key=lambda x: x['gpa'], reverse=True)[:limit]
    
    top_performers = []
    for item in top_students:
        student = item['student']
        terms = item['terms']
        
        total_subjects = db.query(func.count(Subject.id)).join(
            AcademicTerm
        ).filter(AcademicTerm.user_id == student.user_id).scalar() or 0
        
        total_credits = db.query(func.sum(Subject.credits)).join(
            AcademicTerm
        ).filter(AcademicTerm.user_id == student.user_id).scalar() or 0
        
        top_performers.append(
            StudentAnalyticsSummary(
                student_id=student.id,
                student_name=student.name,
                branch=student.branch,
                current_semester=student.semester,
                overall_gpa=Decimal(str(item['gpa'])),
                total_credits=total_credits,
                total_subjects=total_subjects,
                gpa_trend="stable",
                performance_percentile=Decimal("95.0")
            )
        )
    
    return AnalyticsOverview(
        total_students=len(all_students),
        average_gpa=Decimal(str(overall_avg_gpa)),
        grade_distribution=grade_dist,
        top_performers=top_performers
    )
