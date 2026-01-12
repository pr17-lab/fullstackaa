export interface Student {
    id: string;
    user_id: string;
    name: string;
    branch: string;
    semester: number;
    interests?: string;
    created_at: string;
    updated_at: string;
}

export interface StudentListResponse {
    total: number;
    page: number;
    page_size: number;
    students: Student[];
}

export interface Subject {
    id: string;
    term_id: string;
    subject_name: string;
    subject_code: string;
    credits: number;
    marks: number;
    grade: string;
}

export interface AcademicTerm {
    id: string;
    user_id: string;
    semester: number;
    year: number;
    gpa: number;
    subjects?: Subject[];
}

export interface AcademicRecordSummary {
    student_id: string;
    total_terms: number;
    overall_gpa: number;
    total_credits: number;
    terms: AcademicTerm[];
}

// Analytics Types
export interface GPATrendPoint {
    semester: number;
    year: number;
    gpa: number;
    term_id: string;
}

export interface GPATrend {
    student_id: string;
    data_points: GPATrendPoint[];
    average_gpa: number;
    trend: 'improving' | 'declining' | 'stable';
}

export interface SubjectPerformanceItem {
    subject_code: string;
    subject_name: string;
    average_marks: number;
    total_credits: number;
    frequency: number;
}

export interface SubjectPerformance {
    student_id: string;
    subjects: SubjectPerformanceItem[];
    strongest_subject: string;
    weakest_subject: string;
}

export interface SemesterStats {
    semester: number;
    year: number;
    gpa: number;
    total_credits: number;
    subjects_count: number;
    average_marks: number;
}

export interface SemesterComparison {
    student_id: string;
    semesters: SemesterStats[];
    best_semester: SemesterStats;
    current_semester: SemesterStats;
}

export interface StudentAnalyticsSummary {
    student_id: string;
    student_name: string;
    branch: string;
    current_semester: number;
    overall_gpa: number;
    total_credits: number;
    total_subjects: number;
    gpa_trend: 'improving' | 'declining' | 'stable';
    performance_percentile: number;
}

export interface CohortStats {
    branch: string;
    semester: number;
    total_students: number;
    average_gpa: number;
    median_gpa: number;
    top_gpa: number;
    bottom_gpa: number;
    gpa_distribution: Record<string, number>;
}

export interface GradeDistribution {
    grade: string;
    count: number;
    percentage: number;
}

export interface AnalyticsOverview {
    total_students: number;
    average_gpa: number;
    grade_distribution: GradeDistribution[];
    top_performers: StudentAnalyticsSummary[];
}
