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
import {
    StudentSkill,
    SkillGap,
    SkillsSummary,
    CareerRecommendation,
    Roadmap,
    RoadmapDetail,
    StudentPreferences,
    JobListingsResponse,
    TaxonomySearchResponse,
} from '../types/career';

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
        const response = await api.get<GPATrend>(`/analytics/gpa-trend/${studentId}`);
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

// ─── V2 Career Intelligence Services ──────────────────────────────────────────

export const SkillsService = {
    getMySkills: async () => {
        const response = await api.get<StudentSkill[]>('/skills/me');
        return response.data;
    },

    getSkillsSummary: async () => {
        const response = await api.get<SkillsSummary>('/skills/summary');
        return response.data;
    },

    getSkillGaps: async () => {
        const response = await api.get<SkillGap[]>('/skills/gaps');
        return response.data;
    },

    getRecommendation: async () => {
        const response = await api.get<CareerRecommendation>('/skills/recommendation');
        return response.data;
    },

    searchTaxonomy: async (query: string) => {
        const response = await api.get<TaxonomySearchResponse[]>('/skills/taxonomy/search', { params: { query } });
        return response.data;
    },

    addManualSkill: async (skill_name: string, confidence_score: number) => {
        const response = await api.post<StudentSkill>('/skills/manual', { skill_name, confidence_score });
        return response.data;
    },

    removeManualSkill: async (skill_id: string) => {
        await api.delete(`/skills/manual/${skill_id}`);
    },
};

export const RoadmapService = {
    listRoadmaps: async () => {
        const response = await api.get<Roadmap[]>('/roadmap');
        return response.data;
    },

    generateRoadmap: async (job_role: string) => {
        const response = await api.post<RoadmapDetail>('/roadmap/generate', { job_role });
        return response.data;
    },

    getRoadmap: async (roadmap_id: string) => {
        const response = await api.get<RoadmapDetail>(`/roadmap/${roadmap_id}`);
        return response.data;
    },

    completeTask: async (task_id: string, feedback_score?: number) => {
        const response = await api.post<{ status: string; message: string }>(
            `/roadmap/tasks/${task_id}/complete`,
            { feedback_score: feedback_score ?? null }
        );
        return response.data;
    },

    skipTask: async (task_id: string) => {
        const response = await api.post<{ status: string; message: string }>(
            `/roadmap/tasks/${task_id}/skip`,
            {}
        );
        return response.data;
    },

    addCustomTask: async (roadmap_id: string, data: { title: string; platform?: string; estimated_hours: number; resource_url?: string; phase: string }) => {
        const response = await api.post<any>(`/roadmap/${roadmap_id}/tasks/custom`, data);
        return response.data;
    },

    updateTaskStatus: async (task_id: string, status: 'pending' | 'in_progress' | 'completed') => {
        const response = await api.patch<any>(`/roadmap/tasks/${task_id}/status`, { status });
        return response.data;
    },

    deleteTask: async (task_id: string) => {
        await api.delete(`/roadmap/tasks/${task_id}`);
    },
};

export const PreferencesService = {
    getPreferences: async () => {
        const response = await api.get<StudentPreferences>('/preferences');
        return response.data;
    },

    updatePreferences: async (data: Omit<StudentPreferences, 'id' | 'user_id' | 'created_at' | 'updated_at'>) => {
        const response = await api.put<StudentPreferences>('/preferences', data);
        return response.data;
    },
};

export const JobListingsService = {
    getJobListings: async (job_role: string) => {
        const response = await api.get<JobListingsResponse>(`/jobs/listings/${encodeURIComponent(job_role)}`);
        return response.data;
    }
};

