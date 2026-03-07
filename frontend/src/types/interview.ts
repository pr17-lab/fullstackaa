// Interview module TypeScript types

export interface InterviewQuestion {
    id: string;
    topic: string;
    question: string;
    difficulty: 'easy' | 'medium' | 'hard';
    source?: string;
    user_answer?: string;
    created_at?: string;
}

export interface InterviewSession {
    id: string;
    branch: string;
    topic?: string;
    status: 'active' | 'completed' | 'abandoned';
    created_at?: string;
    questions: InterviewQuestion[];
}

export interface InterviewSessionSummary {
    id: string;
    branch: string;
    topic?: string;
    status: 'active' | 'completed' | 'abandoned';
    created_at?: string;
    question_count: number;
}

export interface GeneratedQuestionsResponse {
    student_id: string;
    branch: string;
    semester: number;
    overall_gpa: string;
    weak_subjects: string[];
    questions: InterviewQuestion[];
    source: 'built-in' | 'ml_service';
}

export interface AnswerSubmitResponse {
    id: string;
    question: string;
    user_answer: string;
    session_completed: boolean;
}
