// Interview module TypeScript types

export interface InterviewQuestion {
    id: string;
    topic: string;
    question: string;
    difficulty: 'easy' | 'medium' | 'hard';
    source?: string;
    user_answer?: string;
    ai_score?: string;
    ai_verdict?: string;
    ai_feedback?: string;
    model_answer?: string;
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
    /** 'built-in' | 'groq_jd' | 'groq_resume' | 'groq_jd_resume' | *_gemini variants */
    source: string;
}

export interface AnswerSubmitResponse {
    id: string;
    question: string;
    user_answer: string;
    session_completed: boolean;
}

export interface QuestionEvaluation {
    question_id: string;
    question: string;
    topic: string;
    difficulty: string;
    user_answer: string;
    ai_score: number;
    ai_verdict: 'Strong' | 'Adequate' | 'Weak';
    ai_feedback: string;
    model_answer: string;
}

export interface EvaluationResult {
    session_id: string;
    total_questions: number;
    avg_score: number;
    strong_count: number;
    adequate_count: number;
    weak_count: number;
    overall_verdict: string;
    questions: QuestionEvaluation[];
}
