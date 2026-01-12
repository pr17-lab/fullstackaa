import api from '../api/client';
import {
    StudentListResponse,
    Student,
    AcademicRecordSummary,
    GPATrend,
    SubjectPerformance,
    SemesterComparison,
    StudentAnalyticsSummary,
    CohortStats,
    AnalyticsOverview
} from '../api/types';

export const StudentService = {
    getStudents: async (page = 1, pageSize = 20, branch?: string, semester?: number) => {
        const params: any = { page, page_size: pageSize };
        if (branch) params.branch = branch;
        if (semester) params.semester = semester;

        const response = await api.get<StudentListResponse>('/students', { params });
        return response.data;
    },

    getStudent: async (id: string) => {
        const response = await api.get<Student>(`/students/${id}`);
        return response.data;
    },

    getAcademicRecords: async (id: string) => {
        const response = await api.get<AcademicRecordSummary>(`/students/${id}/academic-records`);
        return response.data;
    }
};

export const AnalyticsService = {
    getGPATrend: async (studentId: string) => {
        const response = await api.get<GPATrend>('/analytics/gpa-trend', {
            params: { student_id: studentId }
        });
        return response.data;
    },

    getSubjectPerformance: async (studentId: string) => {
        const response = await api.get<SubjectPerformance>('/analytics/subject-performance', {
            params: { student_id: studentId }
        });
        return response.data;
    },

    getSemesterComparison: async (studentId: string) => {
        const response = await api.get<SemesterComparison>('/analytics/semester-comparison', {
            params: { student_id: studentId }
        });
        return response.data;
    },

    getStudentSummary: async (studentId: string) => {
        const response = await api.get<StudentAnalyticsSummary>(`/analytics/student/${studentId}/summary`);
        return response.data;
    },

    getCohortStats: async (branch: string, semester: number) => {
        const response = await api.get<CohortStats>('/analytics/cohort-stats', {
            params: { branch, semester }
        });
        return response.data;
    },

    getOverview: async (limit = 10) => {
        const response = await api.get<AnalyticsOverview>('/analytics/overview', {
            params: { limit }
        });
        return response.data;
    }
};
