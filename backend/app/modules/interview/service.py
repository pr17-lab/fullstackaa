"""
InterviewService (v2.0)
-----------------------
DB-backed sessions, async ML inference with fallback, and
session-state lifecycle management.

Architectural notes:
  - Transaction safety: session + questions committed atomically with rollback on error.
  - Lifecycle: status auto-advances to "completed" when all questions are answered.
  - Performance: list_sessions() uses joinedload to avoid N+1 on question_count.
  - ML pipeline: Groq → Gemini → built-in question bank (graceful degradation).

ML Sub-Service — Network Boundary
----------------------------------
The ML sub-service (ML_SERVICE_URL) must run exclusively inside the private Docker
network and must NOT be exposed publicly. All authentication is handled by the core
FastAPI application before this service is called. See docker-compose.yml for the
correct network isolation pattern.
"""
from __future__ import annotations

import io
import json
import logging
import random
import re
import uuid
from collections import Counter
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

import httpx
from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc

from app.core.config import settings
from app.models.interview import InterviewSession, InterviewQuestion, SessionStatus

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Built-in question bank — fallback when ML service is unavailable
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
        {"topic": "DSA",  "question": "Explain graph shortest path algorithms (Dijkstra vs Bellman-Ford).", "difficulty": "hard"},
        # DBMS
        {"topic": "DBMS", "question": "What is database normalisation? Explain 1NF, 2NF, 3NF.", "difficulty": "medium"},
        {"topic": "DBMS", "question": "Explain ACID properties with examples.", "difficulty": "medium"},
        {"topic": "DBMS", "question": "Explain the difference between SQL JOINs.", "difficulty": "medium"},
        {"topic": "DBMS", "question": "What is a database index and how does it speed up queries?", "difficulty": "medium"},
        {"topic": "DBMS", "question": "What is the difference between a primary key and a foreign key?", "difficulty": "easy"},
        {"topic": "DBMS", "question": "Explain what a transaction is and why rollback matters.", "difficulty": "medium"},
        {"topic": "DBMS", "question": "What is the difference between SQL and NoSQL databases?", "difficulty": "easy"},
        # OS
        {"topic": "OS",   "question": "What is a deadlock? How can it be prevented?", "difficulty": "hard"},
        {"topic": "OS",   "question": "Difference between process and thread?", "difficulty": "easy"},
        {"topic": "OS",   "question": "What is virtual memory and how does paging work?", "difficulty": "hard"},
        {"topic": "OS",   "question": "What is a context switch and when does it happen?", "difficulty": "medium"},
        {"topic": "OS",   "question": "Explain the producer-consumer problem and a solution.", "difficulty": "hard"},
        {"topic": "OS",   "question": "What is the difference between preemptive and non-preemptive scheduling?", "difficulty": "medium"},
        # CN
        {"topic": "CN",   "question": "Explain the OSI model and its layers.", "difficulty": "easy"},
        {"topic": "CN",   "question": "What is TCP vs UDP? When would you use each?", "difficulty": "medium"},
        {"topic": "CN",   "question": "What is the difference between HTTP and HTTPS?", "difficulty": "easy"},
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
        {"topic": "Signals",   "question": "Explain the concept of Fourier Transform and its applications.", "difficulty": "hard"},
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
        {"topic": "Structures", "question": "What is the difference between a simply supported and cantilever beam?", "difficulty": "easy"},
        {"topic": "Soil",       "question": "Explain the different types of soil consolidation.", "difficulty": "hard"},
        {"topic": "Concrete",   "question": "What is the water-cement ratio and how does it affect concrete strength?", "difficulty": "medium"},
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


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _strip_json_fences(raw: str) -> str:
    """Remove markdown code fences (```json ... ```) from an LLM response."""
    if "```" in raw:
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return raw.strip()


def _clean_text(t: str) -> str:
    """Strip HTML tags, collapse whitespace, and cap at 3000 chars."""
    if not t:
        return ""
    t = re.sub(r"<[^>]+>", " ", t)
    t = re.sub(r"\s+", " ", t)
    return t.strip()[:3000]


# ---------------------------------------------------------------------------
# InterviewService
# ---------------------------------------------------------------------------

class InterviewService:
    """Business logic for the Interview module (v2.0 — DB-backed)."""

    # ------------------------------------------------------------------
    # Question generation — sync fallback (built-in bank)
    # ------------------------------------------------------------------

    def generate_questions(
        self,
        *,
        branch: str,
        semester: int,
        weak_subjects: list[str],
        overall_gpa: Decimal,
        topic: Optional[str] = None,
        limit: int = 10,
    ) -> list[dict]:
        """Synchronous question generation from the built-in bank."""
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
                "source": "weak_subject_personalisation",
            }
            for subj in weak_subjects[:3]
        ]
        return (follow_ups + bank)[:limit]

    # ------------------------------------------------------------------
    # Question generation — async pipeline (ML service → Groq → bank)
    # ------------------------------------------------------------------

    async def generate_questions_async(
        self,
        *,
        branch: str,
        semester: int,
        weak_subjects: list[str],
        overall_gpa: Decimal,
        jd_text: str = "",
        resume_context: Optional[str] = None,
        limit: int = 10,
    ) -> tuple[list[dict], str]:
        # Groq / Gemini is the PRIMARY path
        if settings.GROQ_API_KEY or settings.GEMINI_API_KEY:
            try:
                with open("log_api_inputs.txt", "a", encoding="utf-8") as f:
                    f.write(f"generate_questions_async inputs: jd_text='{jd_text}', resume_context='{resume_context}', branch='{branch}'\n")
            except:
                pass
                
            ai_result, source_tag = await self._groq_fallback(
                branch=branch, semester=semester,
                weak_subjects=weak_subjects, overall_gpa=overall_gpa,
                jd_text=jd_text, resume_context=resume_context or "",
                limit=limit
            )
            if ai_result:
                try:
                    with open("log_api_inputs.txt", "a", encoding="utf-8") as f:
                        f.write(f"AI Success: {source_tag}\n")
                except:
                    pass
                return ai_result, source_tag

        # Try ML service as fallback
        ml_result = await self._try_ml_service(
            branch=branch, semester=semester,
            weak_subjects=weak_subjects, overall_gpa=overall_gpa,
            jd_text=jd_text, resume_context=resume_context or "",
            limit=limit
        )
        if ml_result:
            return ml_result, "ml_service"
        
        # Built-in is last resort ONLY
        logger.warning("Both Groq and ML service failed — using built-in bank")
        return self.generate_questions(
            branch=branch, semester=semester,
            weak_subjects=weak_subjects, overall_gpa=overall_gpa,
            topic=jd_text if jd_text else None,
            limit=limit
        ), "built-in"

    async def _try_ml_service(self, **kwargs):
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.post(
                    f"{settings.ML_SERVICE_URL}/predict/questions",
                    json={
                        "branch": kwargs["branch"],
                        "semester": kwargs["semester"],
                        "weak_subjects": kwargs["weak_subjects"],
                        "overall_gpa": float(kwargs["overall_gpa"]),
                        "jd_text": kwargs.get("jd_text", ""),
                        "resume_context": kwargs.get("resume_context", ""),
                        "limit": kwargs.get("limit", 10)
                    }
                )
                resp.raise_for_status()
                questions = resp.json().get("questions", [])
                if questions:
                    return questions
        except Exception as e:
            logger.warning(f"ML service unavailable: {e}")
        return None

    async def _groq_fallback(self, *, branch, semester, 
        weak_subjects, overall_gpa, jd_text, 
        resume_context, limit):
        
        weak_str = ", ".join(weak_subjects) if weak_subjects else "none"
        resume_str = resume_context.strip() if resume_context else "not provided"
        
        has_jd     = bool(jd_text and jd_text.strip())
        has_resume = bool(resume_context and resume_context.strip() and resume_context.strip() != "None")

        if has_jd and has_resume:
            # Both JD and resume provided — deep probing prompt
            prompt = f"""You are a senior technical interviewer.

Generate exactly {limit} interview questions tailored to this candidate.

JOB DESCRIPTION:
{jd_text.strip()}

CANDIDATE RESUME:
{resume_context.strip()}

STRICT RULES:
- At least 60% of questions MUST be derived directly from the job description requirements (skills, tools, responsibilities).
- At least 40% of questions MUST probe the candidate's resume (projects, technologies, tools, or experience).

- Resume-based questions MUST be deep and practical:
    → Ask how something was implemented
    → Ask design decisions or trade-offs
    → Ask challenges faced and solutions

- Questions MUST test real understanding, not definitions:
    → Prefer "how", "why", "when", "what happens if"

- Difficulty distribution:
    40% easy, 40% medium, 20% hard

- Questions must:
    → Sound like a real interviewer (not exam-style)
    → Be specific and technical
    → Avoid generic questions

- If the candidate lacks a skill from the JD, ask a fundamental question to test basic understanding.

- Each question MUST be unique

- For EACH question, also generate ONE follow-up question that probes deeper understanding.

Return ONLY a valid JSON object:
{{
  "questions": [
    {{
      "topic": "specific skill name",
      "question": "question text",
      "difficulty": "easy|medium|hard",
      "follow_up": "deeper probing question"
    }}
  ]
}}"""

        elif has_jd:
            # JD only — base questions strictly on JD requirements
            prompt = f"""You are a senior technical interviewer.
Generate exactly {limit} interview questions based STRICTLY on this job description.

JOB DESCRIPTION:
{jd_text.strip()}

STRICT RULES:
- Questions MUST test specific technical skills and requirements mapped to the JD.
- 40% easy, 40% medium, 20% hard.
- Do NOT generate generic computer science questions. Be highly specific and technical.
- Ensure all {limit} questions are strictly UNIQUE and distinct.

Return ONLY a valid JSON object:
{{"questions": [{{"topic": "specific skill name", "question": "question text", "difficulty": "easy|medium|hard"}}]}}"""

        elif has_resume:
            # Resume only — probe the candidate's background and skills
            prompt = f"""You are a senior technical interviewer.
Generate exactly {limit} interview questions tailored to this candidate's resume.

CANDIDATE RESUME:
{resume_context.strip()}

STRICT RULES:
- Questions MUST probe the specific skills, projects, tools, and experiences listed in the resume.
- Ask about technologies they claim to know, projects they built, and roles they held.
- 40% easy, 40% medium, 20% hard.
- Do NOT ask generic questions unrelated to what is on the resume.
- Ensure all {limit} questions are strictly UNIQUE and distinct.

Return ONLY a valid JSON object:
{{"questions": [{{"topic": "skill or project from resume", "question": "question text", "difficulty": "easy|medium|hard"}}]}}"""

        else:
            # No JD or resume — fall back to student academic profile
            prompt = f"""Generate exactly {limit} technical interview questions
for a {branch} engineering student, semester {semester}, GPA {overall_gpa:.1f}/10.
Weak subjects: {weak_str}

Cover core technical topics appropriate for their branch and semester.
Mix difficulties: 40% easy, 40% medium, 20% hard.
Ensure all {limit} questions are strictly UNIQUE and distinct.

Return ONLY a valid JSON object:
{{"questions": [{{"topic": "topic", "question": "question text", "difficulty": "easy|medium|hard"}}]}}"""

        try:
            if settings.GROQ_API_KEY:
                from groq import Groq
                client = Groq(api_key=settings.GROQ_API_KEY)
                
                response = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=2000,
                    response_format={"type": "json_object"}
                )
                
                raw = response.choices[0].message.content.strip()
                
                import json
                parsed = json.loads(raw)
                questions = parsed.get("questions", [])
                
                if isinstance(questions, list) and len(questions) > 0:
                    return questions, "groq_direct"
                    
        except Exception as e:
            logger.error(f"Groq primary attempt failed: {type(e).__name__}: {e}")
            try:
                with open("log_api_inputs.txt", "a", encoding="utf-8") as f:
                    f.write(f"Groq exception: {type(e).__name__}: {e}\n")
            except:
                pass

        # --- Gemini Fallback ---
        if settings.GEMINI_API_KEY:
            try:
                logger.info("Attempting Gemini fallback for question generation...")
                url = (
                    "https://generativelanguage.googleapis.com/v1beta/models/"
                    f"gemini-1.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
                )
                payload = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"temperature": 0.7, "response_mime_type": "application/json"},
                }
                async with httpx.AsyncClient(timeout=30.0) as http_client:
                    resp = await http_client.post(url, json=payload)
                    resp.raise_for_status()
                    raw = resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                    
                    import json
                    parsed = json.loads(raw)
                    questions = parsed.get("questions", [])
                    if isinstance(questions, list) and len(questions) > 0:
                        return questions, "gemini_fallback"
            except Exception as e:
                logger.error(f"Gemini fallback failed: {type(e).__name__}: {e}")
                try:
                    with open("log_api_inputs.txt", "a", encoding="utf-8") as f:
                        f.write(f"Gemini exception: {type(e).__name__}: {e}\n")
                except:
                    pass

        return None, "ai_failed"

    # ------------------------------------------------------------------
    # Session management
    # ------------------------------------------------------------------

    def list_sessions(
        self,
        db: Session,
        user_id: uuid.UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[InterviewSession], int]:
        """Return a paginated page of sessions for user_id, newest first."""
        base_query = db.query(InterviewSession).filter(InterviewSession.user_id == user_id)
        total = base_query.count()
        sessions = (
            base_query
            .options(joinedload(InterviewSession.questions))
            .order_by(desc(InterviewSession.created_at))
            .limit(limit)
            .offset(offset)
            .all()
        )
        return sessions, total

    def create_session(
        self,
        db: Session,
        user_id: uuid.UUID,
        branch: str,
        topic: Optional[str],
        questions: list[dict],
    ) -> InterviewSession:
        """Atomically persist a new session + all its questions."""
        try:
            session = InterviewSession(
                user_id=user_id,
                branch=branch,
                topic=topic,
                status=SessionStatus.ACTIVE,
            )
            db.add(session)
            db.flush()

            for q in questions:
                db.add(InterviewQuestion(
                    session_id=session.id,
                    topic=q.get("topic", "General"),
                    question=q.get("question", ""),
                    difficulty=q.get("difficulty", "medium"),
                    source=q.get("source"),
                    follow_up=q.get("follow_up"),
                ))

            db.commit()
            db.refresh(session)
            logger.info(
                "Session %s created: user=%s branch=%s questions=%d",
                session.id, user_id, branch, len(session.questions),
            )
            return session
        except Exception:
            db.rollback()
            logger.exception("Failed to create interview session — rolled back")
            raise

    def get_session(
        self,
        db: Session,
        session_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Optional[InterviewSession]:
        """Return a session owned by user_id, eagerly loading its questions."""
        return (
            db.query(InterviewSession)
            .filter(
                InterviewSession.id == session_id,
                InterviewSession.user_id == user_id,
            )
            .options(joinedload(InterviewSession.questions))
            .first()
        )

    # ------------------------------------------------------------------
    # Answer submission + lifecycle
    # ------------------------------------------------------------------

    def submit_answer(
        self,
        db: Session,
        session_id: uuid.UUID,
        question_id: uuid.UUID,
        user_id: uuid.UUID,
        answer: str,
    ) -> tuple[InterviewQuestion, bool]:
        """
        Persist the student's answer and advance the session lifecycle.

        Returns (question, session_completed) — session_completed is True
        when the session just transitioned to 'completed'.
        Raises HTTP 404 if the question is not found or belongs to another user.
        """
        question = (
            db.query(InterviewQuestion)
            .join(InterviewSession)
            .filter(
                InterviewQuestion.id == question_id,
                InterviewSession.id == session_id,
                InterviewSession.user_id == user_id,
            )
            .first()
        )
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")

        question.user_answer = answer

        session_completed = False
        sibling_questions = (
            db.query(InterviewQuestion)
            .filter(InterviewQuestion.session_id == session_id)
            .all()
        )
        all_answered = all(
            (q.user_answer is not None and q.user_answer.strip())
            for q in sibling_questions
            if q.id != question_id
        )
        if all_answered and answer.strip():
            session = db.query(InterviewSession).filter(
                InterviewSession.id == session_id
            ).first()
            if session and session.status == SessionStatus.ACTIVE:
                session.status = SessionStatus.COMPLETED
                session_completed = True
                logger.info("Session %s marked as completed", session_id)

        db.commit()
        db.refresh(question)
        return question, session_completed

    def delete_session(
        self,
        db: Session,
        session_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> bool:
        """Delete a session and all its questions. Returns False if not found."""
        session = (
            db.query(InterviewSession)
            .filter(
                InterviewSession.id == session_id,
                InterviewSession.user_id == user_id,
            )
            .first()
        )
        if not session:
            return False
        db.delete(session)
        db.commit()
        logger.info("Session %s deleted by user %s", session_id, user_id)
        return True

    # ------------------------------------------------------------------
    # AI answer evaluation
    # ------------------------------------------------------------------

    async def evaluate_session(
        self,
        db: Session,
        session_id: UUID,
        user_id: UUID,
    ) -> dict:
        """
        Evaluate all answered questions in a completed session using Groq → Gemini.
        Returns a structured result dict with per-question scores and an overall verdict.
        """
        session = db.query(InterviewSession).filter(
            InterviewSession.id == session_id,
            InterviewSession.user_id == user_id,
        ).first()
        if not session:
            raise HTTPException(404, "Session not found")
        # Mark session as completed since evaluation is requested
        if session.status != SessionStatus.COMPLETED:
            session.status = SessionStatus.COMPLETED

        questions = db.query(InterviewQuestion).filter(
            InterviewQuestion.session_id == session_id,
        ).all()
        if not questions:
            raise HTTPException(400, "No questions found in this session")

        qa_text = "\n".join(
            f"Q{i}: {q.question}\nStudent Answer: {q.user_answer if q.user_answer and q.user_answer.strip() else 'skipped'}\nDifficulty: {q.difficulty}\n---"
            for i, q in enumerate(questions, 1)
        )

        eval_prompt = f"""You are a senior technical interviewer evaluating a student's mock interview answers.

Evaluate each answer and return ONLY a valid JSON array.

Format:
[
  {{
    "question_index": 1,
    "score": 7,
    "verdict": "Adequate",
    "feedback": "...",
    "model_answer": "...",
    "mistakes": ["...", "..."],
    "improvement": "..."
  }}
]

Rules:
- score: integer from 1 to 10
- verdict:
    Strong (>=7), Adequate (>=4), Weak (<4)

- feedback:
    1-2 sentences explaining overall quality of the answer

- mistakes:
    Identify EXACT issues such as:
    - Missing key concept
    - Incorrect explanation
    - Lack of example
    - Poor structure
    - Too vague

- improvement:
    Give a clear, actionable suggestion on how the student can improve their answer

- model_answer:
    Provide a concise (2-3 sentences) ideal answer

- Keep feedback specific and practical (avoid generic comments)

- If the question is skipped:
    score = 0
    verdict = "Weak"
    feedback = "Question was skipped."
    mistakes = ["No answer provided"]
    improvement = "Attempt the question by covering key concepts."

Now evaluate the following:

{qa_text}

Return ONLY the JSON array. No other text."""

        evaluations = None

        # --- Gemini ---
        try:
            if not settings.GEMINI_API_KEY:
                raise ValueError("GEMINI_API_KEY not configured")
            url = (
                f"https://generativelanguage.googleapis.com/v1beta/models/"
                f"gemini-1.5-flash-latest:generateContent?key={settings.GEMINI_API_KEY}"
            )
            payload = {
                "contents": [{"parts": [{"text": eval_prompt}]}],
                "generationConfig": {"temperature": 0.3, "response_mime_type": "application/json"},
            }
            async with httpx.AsyncClient(timeout=30.0) as client_http:
                resp = await client_http.post(url, json=payload)
                resp.raise_for_status()
                raw = resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                evaluations = json.loads(_strip_json_fences(raw))
        except Exception as e:
            logger.warning("Gemini evaluation failed: %s — trying Groq as fallback.", e)

        # --- Groq fallback ---
        if not evaluations:
            try:
                from groq import Groq
                client = Groq(api_key=settings.GROQ_API_KEY)
                response = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role": "user", "content": eval_prompt}],
                    temperature=0.3,
                    max_tokens=2000,
                )
                evaluations = json.loads(_strip_json_fences(response.choices[0].message.content.strip()))
            except Exception as e:
                logger.error("Groq evaluation error: %s", e)
                raise HTTPException(
                    503,
                    f"AI evaluation unavailable: {e}. Please try again in a moment.",
                )

        # --- Write results back to DB ---
        now = datetime.utcnow()
        for eval_item in evaluations:
            idx = eval_item.get("question_index", 1) - 1
            if not 0 <= idx < len(questions):
                continue
            q = questions[idx]
            q.ai_score = eval_item.get("score")
            q.ai_verdict = eval_item.get("verdict")
            q.ai_feedback = eval_item.get("feedback")
            q.model_answer = eval_item.get("model_answer")
            q.mistakes = eval_item.get("mistakes", [])
            q.improvement = eval_item.get("improvement")
            q.evaluated_at = now

        db.commit()

        # ------------------------------------------------------------------
        # Post-evaluation: extract weak skills (zero LLM calls)
        # ------------------------------------------------------------------
        weak_skills = extract_weak_skills(questions)
        _penalise_student_skills(db, user_id, weak_skills)

        # ------------------------------------------------------------------
        # Post-evaluation: roadmap trigger (zero LLM calls)
        # ------------------------------------------------------------------
        if weak_skills:
            try:
                from app.modules.roadmap.service import get_active_roadmap, update_roadmap_with_weak_skills, generate_roadmap
                roadmap = get_active_roadmap(db, user_id)
                if roadmap:
                    await update_roadmap_with_weak_skills(db, roadmap, weak_skills)
                    logger.info("Roadmap updated with weak skills for user %s", user_id)
                else:
                    from app.modules.skills.service import get_career_recommendation
                    rec = get_career_recommendation(db, user_id)
                    job_role = rec.get("primary", {}).get("job_role") if rec.get("primary") else None
                    if job_role:
                        await generate_roadmap(db, user_id, job_role)
                        logger.info("New roadmap generated for user %s", user_id)
            except Exception as e:
                logger.error("Failed to trigger roadmap update: %s", e)

        results = [
            {
                "question_id": str(q.id),
                "question": q.question,
                "topic": q.topic,
                "difficulty": q.difficulty,
                "user_answer": q.user_answer,
                "ai_score": q.ai_score,
                "ai_verdict": q.ai_verdict,
                "ai_feedback": q.ai_feedback,
                "model_answer": q.model_answer,
                "mistakes": q.mistakes or [],
                "improvement": q.improvement,
            }
            for q in questions
        ]

        avg_score = sum(r["ai_score"] or 0 for r in results) / len(results) if results else 0
        return {
            "session_id": str(session_id),
            "total_questions": len(results),
            "avg_score": round(avg_score, 1),
            "strong_count": sum(1 for r in results if r["ai_verdict"] == "Strong"),
            "adequate_count": sum(1 for r in results if r["ai_verdict"] == "Adequate"),
            "weak_count": sum(1 for r in results if r["ai_verdict"] == "Weak"),
            "overall_verdict": "Strong" if avg_score >= 7 else "Adequate" if avg_score >= 4 else "Needs Improvement",
            "weak_skills": weak_skills,
            "questions": results,
        }


# ---------------------------------------------------------------------------
# Module-level singleton (imported by router)
# ---------------------------------------------------------------------------

interview_service = InterviewService()


# ---------------------------------------------------------------------------
# Post-evaluation helpers — zero LLM calls
# ---------------------------------------------------------------------------

def extract_weak_skills(
    questions: list,
    score_threshold: int = 5,
    top_n: int = 5,
) -> list[str]:
    """
    Derive weak skill topics purely from scored interview questions.

    Rules:
    - Only consider questions where ai_score is set and ai_score < score_threshold.
    - Count topic frequency with Counter.
    - Return the top_n most frequent topics (deduped, ordered by frequency desc).
    - Returns [] when no questions qualify (no LLM needed).
    """
    weak_topics = [
        q.topic
        for q in questions
        if q.ai_score is not None and int(q.ai_score) < score_threshold and q.topic
    ]
    if not weak_topics:
        return []
    counts = Counter(weak_topics)
    return [topic for topic, _ in counts.most_common(top_n)]


def _penalise_student_skills(
    db,
    user_id: UUID,
    weak_skills: list[str],
    penalty: float = 7.0,
    min_score: float = 5.0,
) -> None:
    """
    Lightweight confidence score update — no recompute, no LLM.

    For each weak skill topic:
    - If the student already has a StudentSkill entry for a matching taxonomy
      skill, reduce its confidence_score by `penalty` (floor = min_score).
    - Skips gracefully if the skill is not in the taxonomy or not mapped
      to the student — no creates here (keeps it light).
    """
    if not weak_skills:
        return

    try:
        from app.models.student_skill import StudentSkill
        from app.models.skill_taxonomy import SkillTaxonomy
        import sqlalchemy as sa

        for topic in weak_skills:
            # Fuzzy-match topic name against taxonomy (case-insensitive)
            tax = (
                db.query(SkillTaxonomy)
                .filter(
                    sa.or_(
                        sa.func.lower(SkillTaxonomy.skill_name) == topic.lower(),
                        sa.func.array_to_string(SkillTaxonomy.aliases, ",").ilike(f"%{topic}%"),
                    )
                )
                .first()
            )
            if not tax:
                continue  # Not in taxonomy — skip silently

            ss = (
                db.query(StudentSkill)
                .filter(
                    StudentSkill.user_id == user_id,
                    StudentSkill.skill_id == tax.id,
                )
                .first()
            )
            if not ss:
                continue  # Student doesn't have this skill mapped yet — skip

            current = float(ss.confidence_score) if ss.confidence_score else 0.0
            ss.confidence_score = max(current - penalty, min_score)
            # Recalculate level bucket inline (avoids importing score_to_level in a hot path)
            new_score = float(ss.confidence_score)
            ss.level = "strong" if new_score >= 70 else "moderate" if new_score >= 40 else "weak"

        db.commit()
        logger.info(
            "Confidence penalty applied for user %s weak skills: %s",
            user_id, weak_skills,
        )
    except Exception as exc:
        logger.warning("_penalise_student_skills skipped due to error: %s", exc)
        db.rollback()
