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

FALLBACK_QUESTION_BANK: dict[str, list[dict]] = {
    "CSE": [
        {"topic": "Data Structures", "question": "Explain the difference between a stack and a queue, and provide a real-world software use case for each.", "difficulty": "medium"},
        {"topic": "Databases", "question": "What is the purpose of database normalization, and how does it prevent data anomalies?", "difficulty": "medium"},
        {"topic": "Operating Systems", "question": "Describe the concept of virtual memory and how paging mechanisms work in a modern OS.", "difficulty": "medium"},
        {"topic": "Networking", "question": "Explain the differences between TCP and UDP protocols, highlighting scenarios where one is preferred over the other.", "difficulty": "medium"},
        {"topic": "Software Engineering", "question": "What are the core principles of RESTful API design?", "difficulty": "medium"},
    ],
    "ECE": [
        {"topic": "Digital Logic", "question": "Explain the difference between combinational and sequential logic circuits.", "difficulty": "medium"},
        {"topic": "Signals", "question": "What is the Nyquist-Shannon sampling theorem, and why is it critical in digital signal processing?", "difficulty": "medium"},
        {"topic": "Embedded Systems", "question": "Describe the function of an interrupt in a microcontroller architecture and how it differs from polling.", "difficulty": "medium"},
        {"topic": "Circuits", "question": "Explain the operational principles of an ideal operational amplifier (Op-Amp).", "difficulty": "medium"},
        {"topic": "Communication", "question": "What are the key differences between amplitude modulation (AM) and frequency modulation (FM)?", "difficulty": "medium"},
    ],
    "MECH": [
        {"topic": "Thermodynamics", "question": "State the second law of thermodynamics and explain its implications for heat engine efficiency.", "difficulty": "medium"},
        {"topic": "Fluid Mechanics", "question": "Explain Bernoulli's principle and describe one of its practical engineering applications.", "difficulty": "medium"},
        {"topic": "Materials Science", "question": "Describe the typical stress-strain curve for a ductile material, identifying the yield point and ultimate tensile strength.", "difficulty": "medium"},
        {"topic": "Manufacturing", "question": "What are the primary differences between casting and forging manufacturing processes?", "difficulty": "medium"},
        {"topic": "Mechanics", "question": "Explain the concept of fatigue failure in mechanical components and how it can be mitigated.", "difficulty": "medium"},
    ],
    "default": [
        {"topic": "General Engineering", "question": "Describe a challenging technical problem you encountered and the analytical steps you took to solve it.", "difficulty": "medium"},
        {"topic": "General Engineering", "question": "How do you approach learning a completely new tool or technology required for a project?", "difficulty": "medium"},
        {"topic": "General Engineering", "question": "Explain a complex engineering concept to someone without a technical background.", "difficulty": "medium"},
        {"topic": "General Engineering", "question": "Discuss the importance of version control in collaborative engineering projects.", "difficulty": "medium"},
        {"topic": "General Engineering", "question": "What strategies do you use to ensure the quality and reliability of your technical deliverables?", "difficulty": "medium"},
    ]
}


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
    # Question generation — async pipeline (3-Tier Fallback)
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
        weak_str = ", ".join(weak_subjects) if weak_subjects else "none"
        
        prompt = f"""You are a senior technical interviewer.
Generate exactly {limit} interview questions tailored to this candidate.

Candidate Branch: {branch}
Candidate Semester: {semester}
Candidate Overall GPA: {overall_gpa:.1f}/10
Weak Subjects: {weak_str}
"""
        if jd_text and jd_text.strip():
            prompt += f"\nJOB DESCRIPTION:\n{jd_text.strip()}\n"
        if resume_context and resume_context.strip() and resume_context.strip() != "None":
            prompt += f"\nCANDIDATE RESUME:\n{resume_context.strip()}\n"

        prompt += """
STRICT RULES:
- Generate technical questions appropriate for the candidate's background.
- If Job Description is provided, heavily base questions on its requirements.
- If Resume is provided, probe their listed skills and projects.
- Difficulty distribution: 40% easy, 40% medium, 20% hard.
- Return ONLY a valid JSON object matching this schema exactly:
{
  "questions": [
    {
      "topic": "string",
      "question": "string",
      "difficulty": "easy|medium|hard",
      "follow_up": "string"
    }
  ]
}
"""

        # Tier 1: Groq
        if settings.GROQ_API_KEY:
            try:
                from groq import AsyncGroq
                client = AsyncGroq(api_key=settings.GROQ_API_KEY)
                response = await client.chat.completions.create(
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
                    return questions[:limit], "groq"
            except Exception as e:
                logger.error(f"Tier 1 (Groq) failed: {type(e).__name__}: {e}")

        # Tier 2: Gemini
        if settings.GEMINI_API_KEY:
            try:
                url = (
                    "https://generativelanguage.googleapis.com/v1beta/models/"
                    f"gemini-1.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
                )
                payload = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "temperature": 0.7, 
                        "response_mime_type": "application/json"
                    },
                }
                async with httpx.AsyncClient(timeout=30.0) as http_client:
                    resp = await http_client.post(url, json=payload)
                    resp.raise_for_status()
                    raw = resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                    import json
                    parsed = json.loads(raw)
                    questions = parsed.get("questions", [])
                    if isinstance(questions, list) and len(questions) > 0:
                        return questions[:limit], "gemini"
            except Exception as e:
                logger.error(f"Tier 2 (Gemini) failed: {type(e).__name__}: {e}")

        # Tier 3: Static Fallback
        logger.warning("Tier 1 and 2 failed. Falling back to Tier 3 (Static Fallback).")
        bank = list(FALLBACK_QUESTION_BANK.get(branch.upper(), FALLBACK_QUESTION_BANK["default"]))
        random.shuffle(bank)
        
        # Add a weak subject personalization if applicable
        follow_ups = [
            {
                "topic": subj,
                "question": f"Your performance in {subj} has room for improvement. Can you explain the core concepts of {subj} in simple terms?",
                "difficulty": "medium",
                "source": "weak_subject_personalisation",
            }
            for subj in weak_subjects[:3]
        ]
        
        return (follow_ups + bank)[:limit], "static_fallback"

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
