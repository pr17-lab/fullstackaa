"""
Prediction Router — ML Sub-Service (v3.0 — Groq LLM)
------------------------------------------------------
Endpoints called by the main app's InterviewService when ML is enabled.

Trust model:
  Internal Docker network only. Authentication handled by the core API.
  This service MUST NOT be publicly exposed.

Phase 3: Groq LLM (llama-3.1-8b-instant) generates dynamic questions
         tailored to the student's profile. Falls back to the built-in
         rule-based bank if Groq is unavailable or key is missing.

Configuration (all via environment variables):
  GROQ_API_KEY       — Groq API key (required for LLM path)
  GROQ_MODEL         — Model to use (default: llama-3.1-8b-instant)
  GROQ_TEMPERATURE   — 0.0–1.0, default 0.7 (lower = more consistent)
  GROQ_MAX_TOKENS    — Max response tokens, default 1024
  GROQ_TIMEOUT_SEC   — Request timeout in seconds, default 10.0
"""
from __future__ import annotations

import random
from typing import Any, Optional

from fastapi import APIRouter
from pydantic import BaseModel

from ml_service.groq_client import generate_questions_with_groq

router = APIRouter()


# ---------------------------------------------------------------------------
# Built-in fallback question bank (used when Groq is unavailable)
# ---------------------------------------------------------------------------

_QUESTION_BANK: dict[str, list[dict]] = {
    "Computer Science": [
        # DSA
        {"topic": "DSA",  "question": "Explain the difference between BFS and DFS.", "difficulty": "medium"},
        {"topic": "DSA",  "question": "What is the time complexity of quicksort in the worst case?", "difficulty": "medium"},
        {"topic": "DSA",  "question": "How does a hash table handle collisions?", "difficulty": "medium"},
        {"topic": "DSA",  "question": "Explain dynamic programming with a classic example.", "difficulty": "hard"},
        {"topic": "DSA",  "question": "What is the difference between a stack and a queue?", "difficulty": "easy"},
        {"topic": "DSA",  "question": "Explain binary search and its time complexity.", "difficulty": "easy"},
        {"topic": "DSA",  "question": "What is a balanced binary search tree? Give an example.", "difficulty": "medium"},
        {"topic": "DSA",  "question": "Explain Dijkstra vs Bellman-Ford for shortest paths.", "difficulty": "hard"},
        # DBMS
        {"topic": "DBMS", "question": "What is database normalisation? Explain 1NF, 2NF, 3NF.", "difficulty": "medium"},
        {"topic": "DBMS", "question": "Explain ACID properties with examples.", "difficulty": "medium"},
        {"topic": "DBMS", "question": "Explain the difference between SQL JOINs.", "difficulty": "medium"},
        {"topic": "DBMS", "question": "What is a database index and how does it speed up queries?", "difficulty": "medium"},
        {"topic": "DBMS", "question": "What is the difference between a primary key and a foreign key?", "difficulty": "easy"},
        {"topic": "DBMS", "question": "What is the difference between SQL and NoSQL databases?", "difficulty": "easy"},
        # OS
        {"topic": "OS",   "question": "What is a deadlock? How can it be prevented?", "difficulty": "hard"},
        {"topic": "OS",   "question": "Difference between process and thread?", "difficulty": "easy"},
        {"topic": "OS",   "question": "What is virtual memory and how does paging work?", "difficulty": "hard"},
        {"topic": "OS",   "question": "What is a context switch and when does it happen?", "difficulty": "medium"},
        {"topic": "OS",   "question": "What is the difference between preemptive and non-preemptive scheduling?", "difficulty": "medium"},
        # CN
        {"topic": "CN",   "question": "Explain the OSI model and its layers.", "difficulty": "easy"},
        {"topic": "CN",   "question": "What is TCP vs UDP? When would you use each?", "difficulty": "medium"},
        {"topic": "CN",   "question": "What is DNS and how does name resolution work?", "difficulty": "easy"},
        {"topic": "CN",   "question": "Explain the three-way handshake in TCP.", "difficulty": "medium"},
        {"topic": "CN",   "question": "What is subnetting and why is it used?", "difficulty": "medium"},
        # SE
        {"topic": "SE",   "question": "What is the Agile methodology?", "difficulty": "easy"},
        {"topic": "SE",   "question": "What is the difference between unit and integration testing?", "difficulty": "easy"},
        {"topic": "SE",   "question": "What is the SOLID principle in object-oriented design?", "difficulty": "medium"},
        {"topic": "SE",   "question": "Explain the concept of design patterns. Give two examples.", "difficulty": "medium"},
        {"topic": "SE",   "question": "What is CI/CD and why is it important?", "difficulty": "easy"},
        {"topic": "SE",   "question": "What is the difference between REST and GraphQL APIs?", "difficulty": "medium"},
    ],
    "Electronics": [
        {"topic": "Circuits",  "question": "Explain Kirchhoff's voltage and current laws.", "difficulty": "easy"},
        {"topic": "Signals",   "question": "What is the Nyquist theorem?", "difficulty": "medium"},
        {"topic": "Embedded",  "question": "Difference between microprocessor and microcontroller?", "difficulty": "easy"},
        {"topic": "VLSI",      "question": "Explain the CMOS fabrication process.", "difficulty": "hard"},
        {"topic": "Signals",   "question": "What is the Z-transform used for?", "difficulty": "hard"},
        {"topic": "Circuits",  "question": "What is an op-amp and its ideal characteristics?", "difficulty": "medium"},
        {"topic": "Embedded",  "question": "Explain the difference between RISC and CISC.", "difficulty": "medium"},
        {"topic": "Circuits",  "question": "What is the difference between AC and DC circuits?", "difficulty": "easy"},
        {"topic": "Signals",   "question": "Explain Fourier Transform and its applications.", "difficulty": "hard"},
        {"topic": "Embedded",  "question": "What is interrupt handling in embedded systems?", "difficulty": "medium"},
        {"topic": "VLSI",      "question": "What is the difference between combinational and sequential circuits?", "difficulty": "medium"},
    ],
    "Mechanical": [
        {"topic": "Thermo",    "question": "State and explain the laws of thermodynamics.", "difficulty": "medium"},
        {"topic": "Mechanics", "question": "Explain Newton's laws of motion with examples.", "difficulty": "easy"},
        {"topic": "Fluid",     "question": "What is Bernoulli's principle?", "difficulty": "medium"},
        {"topic": "Materials", "question": "Explain stress-strain curve for a ductile material.", "difficulty": "medium"},
        {"topic": "Thermo",    "question": "What is the Carnot cycle and its significance?", "difficulty": "hard"},
        {"topic": "Mechanics", "question": "Explain the difference between static and dynamic friction.", "difficulty": "easy"},
        {"topic": "Fluid",     "question": "What is Reynolds number and what does it indicate?", "difficulty": "medium"},
        {"topic": "Materials", "question": "What is the difference between a ductile and brittle material?", "difficulty": "easy"},
    ],
    "Civil": [
        {"topic": "Structures", "question": "Explain the difference between beams, columns, and slabs.", "difficulty": "easy"},
        {"topic": "Soil",       "question": "What is the bearing capacity of soil?", "difficulty": "medium"},
        {"topic": "Concrete",   "question": "What are the properties of good concrete?", "difficulty": "easy"},
        {"topic": "Structures", "question": "Difference between a simply supported and cantilever beam?", "difficulty": "easy"},
        {"topic": "Soil",       "question": "Explain the different types of soil consolidation.", "difficulty": "hard"},
        {"topic": "Concrete",   "question": "What is the water-cement ratio and how does it affect strength?", "difficulty": "medium"},
    ],
    "default": [
        {"topic": "General", "question": "Tell me about yourself and your key academic strengths.", "difficulty": "easy"},
        {"topic": "General", "question": "How do you prioritise tasks when studying multiple subjects?", "difficulty": "easy"},
        {"topic": "General", "question": "Describe a challenging project you worked on.", "difficulty": "medium"},
        {"topic": "General", "question": "Where do you see yourself in 5 years?", "difficulty": "easy"},
        {"topic": "General", "question": "What is your greatest professional strength?", "difficulty": "easy"},
        {"topic": "General", "question": "How do you handle failure or poor exam results?", "difficulty": "easy"},
        {"topic": "General", "question": "Describe a time you worked effectively in a team.", "difficulty": "easy"},
    ],
}

_WEAK_SUBJECT_TEMPLATE = (
    "Your performance in {subject} has room for improvement. "
    "Can you explain the core concepts of {subject} in simple terms?"
)


def _builtin_questions(
    branch: str,
    topic: Optional[str],
    weak_subjects: list[str],
    limit: int,
) -> list[dict]:
    """Return shuffled questions from the built-in bank.

    Weak-subject follow-ups are prepended so they are never cut off
    by the limit slice (they would otherwise fall behind a large bank).
    """
    bank = list(_QUESTION_BANK.get(branch, _QUESTION_BANK["default"]))
    if topic:
        filtered = [q for q in bank if q["topic"].lower() == topic.lower()]
        bank = filtered if filtered else bank
    random.shuffle(bank)
    follow_ups = [
        {
            "topic": subj,
            "question": _WEAK_SUBJECT_TEMPLATE.format(subject=subj),
            "difficulty": "medium",
            "source": "weak_subject_builtin",
        }
        for subj in weak_subjects[:3]
    ]
    # Prepend follow-ups so they are guaranteed within the limit
    return (follow_ups + bank)[:limit]


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class QuestionRequest(BaseModel):
    branch: str
    semester: int
    weak_subjects: list[str] = []
    overall_gpa: float = 0.0
    jd_text: str = ""          # Job description text (replaces topic)
    resume_context: Optional[str] = None
    limit: int = 10


class QuestionResponse(BaseModel):
    model_config = {"protected_namespaces": ()}
    questions: list[Any]  # Any preserves extra fields like 'source' in each dict
    model_version: str = "built-in-v3"


class PerformancePredictionRequest(BaseModel):
    branch: str
    semester: int
    historical_gpas: list[float]


class PerformancePredictionResponse(BaseModel):
    model_config = {"protected_namespaces": ()}
    predicted_next_gpa: float
    confidence: float
    trend: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/questions", response_model=QuestionResponse)
async def predict_questions(req: QuestionRequest):
    """
    Generate personalised interview questions.

    Strategy:
      1. Try Groq LLM (llama-3.1-8b-instant) with the student's full profile.
      2. On any failure (no key, timeout, rate limit, bad JSON) → built-in bank.
    """
    groq_questions = generate_questions_with_groq(
        branch=req.branch,
        semester=req.semester,
        overall_gpa=req.overall_gpa,
        weak_subjects=req.weak_subjects,
        jd_text=req.jd_text,
        resume_context=req.resume_context,
        limit=req.limit,
    )

    if groq_questions is not None:
        return QuestionResponse(
            questions=groq_questions,
            model_version="groq-llama-3.1-8b",
        )

    # Fallback: built-in shuffled bank
    return QuestionResponse(
        questions=_builtin_questions(
            branch=req.branch,
            topic=None,  # QuestionRequest has no topic field; JD not used in built-in bank
            weak_subjects=req.weak_subjects,
            limit=req.limit,
        ),
        model_version="built-in-v3",
    )


@router.post("/performance", response_model=PerformancePredictionResponse)
async def predict_performance(req: PerformancePredictionRequest):
    """
    Predict next-semester GPA using a weighted moving average.
    Weights recent semesters more heavily than older ones.
    """
    gpas = req.historical_gpas
    if len(gpas) >= 3:
        weights = list(range(1, len(gpas) + 1))
        weighted_avg = sum(g * w for g, w in zip(gpas, weights)) / sum(weights)
        delta = gpas[-1] - gpas[-2]
        predicted = round(min(10.0, max(0.0, weighted_avg + delta * 0.4)), 2)
        confidence = 0.75
    elif len(gpas) == 2:
        delta = gpas[-1] - gpas[-2]
        predicted = round(min(10.0, max(0.0, gpas[-1] + delta * 0.5)), 2)
        confidence = 0.60
    elif len(gpas) == 1:
        predicted = gpas[0]
        confidence = 0.40
    else:
        predicted = 7.0
        confidence = 0.20

    last = gpas[-1] if gpas else predicted
    trend = (
        "improving" if predicted > last + 0.2
        else "declining" if predicted < last - 0.2
        else "stable"
    )
    return PerformancePredictionResponse(
        predicted_next_gpa=predicted,
        confidence=confidence,
        trend=trend,
    )


@router.get("/health")
async def health():
    import os
    return {
        "service": "ml_service",
        "status": "ok",
        "version": "3.0.0",
        "llm_enabled": bool(os.environ.get("GROQ_API_KEY")),
    }
