"""
Interview Pydantic Schemas (Phase 2)
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


# ---------------------------------------------------------------------------
# Question schemas
# ---------------------------------------------------------------------------

class InterviewQuestionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    topic: str
    question: str
    difficulty: str
    source: Optional[str] = None
    follow_up: Optional[str] = None
    user_answer: Optional[str] = None
    ai_score: Optional[int] = None
    ai_verdict: Optional[str] = None
    ai_feedback: Optional[str] = None
    model_answer: Optional[str] = None
    mistakes: Optional[list] = None
    improvement: Optional[str] = None
    created_at: Optional[datetime] = None


class AnswerSubmitRequest(BaseModel):
    question_id: uuid.UUID
    answer: str


class AnswerSubmitResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    question: str
    user_answer: str
    session_completed: bool = False  # True when all questions in the session answered


# ---------------------------------------------------------------------------
# Session schemas
# ---------------------------------------------------------------------------

class InterviewSessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    branch: str
    topic: Optional[str] = None
    status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None  # advances when status changes (e.g. → completed)
    questions: list[InterviewQuestionOut] = []


# ---------------------------------------------------------------------------
# Question generation response
# ---------------------------------------------------------------------------

class GeneratedQuestionsResponse(BaseModel):
    student_id: str
    branch: str
    semester: int
    overall_gpa: str
    weak_subjects: list[str]
    questions: list[dict]
    source: str = "built-in"   # "built-in" | "groq_jd" | "groq_resume" | "groq_jd_resume" | *_gemini variants


# ---------------------------------------------------------------------------
# Session create request (used by POST /sessions)
# ---------------------------------------------------------------------------

class SessionCreateRequest(BaseModel):
    jd_text: str = ""           # Job description text (optional when resume is provided)
    resume_context: Optional[str] = None
    limit: int = 10
