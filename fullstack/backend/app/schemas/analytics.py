from pydantic import BaseModel, Field
from typing import List, Dict
from decimal import Decimal
import uuid

# GPA Trend Analysis
class GPATrendPoint(BaseModel):
    semester: int
    year: int
    gpa: Decimal
    term_id: uuid.UUID

class GPATrend(BaseModel):
    student_id: uuid.UUID
    data_points: List[GPATrendPoint]
    average_gpa: Decimal
    trend: str = Field(..., description="'improving', 'declining', or 'stable'")

# Subject Performance Analysis
class SubjectPerformanceItem(BaseModel):
    subject_code: str
    subject_name: str
    average_marks: Decimal
    total_credits: int
    frequency: int = Field(..., description="Number of times subject was taken")

class SubjectPerformance(BaseModel):
    student_id: uuid.UUID
    subjects: List[SubjectPerformanceItem]
    strongest_subject: str
    weakest_subject: str

# Semester Comparison
class SemesterStats(BaseModel):
    semester: int
    year: int
    gpa: Decimal
    total_credits: int
    subjects_count: int
    average_marks: Decimal

class SemesterComparison(BaseModel):
    student_id: uuid.UUID
    semesters: List[SemesterStats]
    best_semester: SemesterStats
    current_semester: SemesterStats

# Individual Student Analytics Summary
class StudentAnalyticsSummary(BaseModel):
    student_id: uuid.UUID
    student_name: str
    branch: str
    current_semester: int
    overall_gpa: Decimal
    total_credits: int
    total_subjects: int
    gpa_trend: str
    performance_percentile: Decimal = Field(..., description="Percentile rank in cohort")

# Cohort Statistics
class CohortStats(BaseModel):
    branch: str
    semester: int
    total_students: int
    average_gpa: Decimal
    median_gpa: Decimal
    top_gpa: Decimal
    bottom_gpa: Decimal
    gpa_distribution: Dict[str, int] = Field(..., description="Distribution by grade ranges")

# Grade Distribution
class GradeDistribution(BaseModel):
    grade: str
    count: int
    percentage: Decimal

class AnalyticsOverview(BaseModel):
    total_students: int
    average_gpa: Decimal
    grade_distribution: List[GradeDistribution]
    top_performers: List[StudentAnalyticsSummary]
