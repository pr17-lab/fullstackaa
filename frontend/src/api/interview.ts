import api from './client';
import type {
    GeneratedQuestionsResponse,
    InterviewSession,
    InterviewSessionSummary,
    AnswerSubmitResponse,
    EvaluationResult,
} from '../types/interview';
import type { TaxonomySearchResponse } from '../types/career';

// Generate questions (does not create a session)
export const generateQuestions = async (
    topic?: string,
    limit = 10
): Promise<GeneratedQuestionsResponse> => {
    const params: Record<string, string | number> = { limit };
    if (topic) params.topic = topic;
    const res = await api.get('/interview/questions', { params });
    return res.data;
};

// List all past sessions
export const listSessions = async (): Promise<{ sessions: InterviewSessionSummary[] }> => {
    const res = await api.get('/interview/sessions');
    return res.data;
};

// Start a new session (generates + persists questions)
export const createSession = async (
    jdText: string,
    limit = 10,
): Promise<InterviewSession> => {
    const res = await api.post('/interview/sessions', {
        jd_text: jdText,
        limit,
    });
    return res.data;
};

// Get a specific session with all questions
export const getSession = async (sessionId: string): Promise<InterviewSession> => {
    const res = await api.get(`/interview/sessions/${sessionId}`);
    return res.data;
};

// Submit an answer for a question
export const submitAnswer = async (
    sessionId: string,
    questionId: string,
    answer: string
): Promise<AnswerSubmitResponse> => {
    const res = await api.post(`/interview/sessions/${sessionId}/answer`, {
        question_id: questionId,
        answer,
    });
    return res.data;
};

// Delete a session permanently
export const deleteSession = async (sessionId: string): Promise<void> => {
    await api.delete(`/interview/sessions/${sessionId}`);
};

// Evaluate an interview session answers
export const evaluateSession = async (sessionId: string): Promise<EvaluationResult> => {
    const res = await api.post(`/interview/sessions/${sessionId}/evaluate`);
    return res.data;
};

// Parse a PDF resume using the backend endpoint
export const parseResumePdf = async (file: File): Promise<{ text: string }> => {
    const formData = new FormData();
    formData.append('file', file);

    const res = await api.post('/interview/sessions/parse-resume', formData, {
        headers: {
            'Content-Type': 'multipart/form-data',
        },
    });
    return res.data;
};

// Create a micro-interview session
export const createMicroSession = async (
    skillId: string,
    roadmapTaskId?: string,
): Promise<InterviewSession> => {
    const params: Record<string, string> = { skill_id: skillId };
    if (roadmapTaskId) params.roadmap_task_id = roadmapTaskId;
    const res = await api.post('/interview/sessions/micro', null, { params });
    return res.data;
};

// Create a project-based depth-verification interview session
export const createProjectSession = async (
    projectId: string,
    limit = 3,
): Promise<InterviewSession> => {
    const res = await api.post('/interview/sessions/practice-project', {
        project_id: projectId,
        limit,
    });
    return res.data;
};

// Create a topic-based practice interview session
export const createPracticeTopicSession = async (
    skillId: string,
    limit = 3,
): Promise<InterviewSession> => {
    const res = await api.post('/interview/sessions/practice-topic', {
        skill_id: skillId,
        limit,
    });
    return res.data;
};

// Get list of practiceable topics
export const getPracticeTopics = async (): Promise<TaxonomySearchResponse[]> => {
    const res = await api.get('/skills/topics');
    return res.data;
};

export interface StudentProject {
    id: string;
    title: string;
    repo_url?: string;
    tech_stack?: string[];
    extracted_skills?: string[];
    depth_verified: boolean;
    calculated_complexity?: number;
    analyzed_at?: string;
}

// Get list of user's projects
export const getStudentProjects = async (): Promise<StudentProject[]> => {
    const res = await api.get('/skills/project');
    return res.data;
};

