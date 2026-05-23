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
        jd_text: str = "",
        resume_context: Optional[str] = None,
        limit: int = 10,
        on_chunk: Optional[Callable[[str], Any]] = None,
    ) -> tuple[list[dict], str]:
        prompt = f"""You are a senior technical interviewer.
Generate exactly {limit} interview questions tailored to this candidate.

Candidate Branch: {branch}
Candidate Semester: {semester}
"""
        if jd_text and jd_text.strip():
            prompt += f"\nJOB DESCRIPTION:\n{jd_text.strip()}\n"
        if resume_context and resume_context.strip() and resume_context.strip() != "None":
            prompt += f"\nCANDIDATE RESUME:\n{resume_context.strip()}\n"

        prompt += """
STRICT RULES:
- Instead of text trivia, force the questions to generate code snippets containing intentional bugs, time complexity traps (O(N^2)), or vulnerability risks.
- The student must evaluate and debug these code snippets to identify the issues.
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
                if on_chunk:
                    response_stream = await client.chat.completions.create(
                        model="llama-3.1-8b-instant",
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.7,
                        max_tokens=2000,
                        response_format={"type": "json_object"},
                        stream=True
                    )
                    full_text = ""
                    async for chunk in response_stream:
                        token = chunk.choices[0].delta.content
                        if token:
                            full_text += token
                            await on_chunk(token)
                    raw = full_text.strip()
                else:
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
        
        return bank[:limit], "static_fallback"

    async def create_micro_interview_session(
        self,
        db: Session,
        user_id: uuid.UUID,
        skill_id: uuid.UUID,
    ) -> InterviewSession:
        """
        Create a shortened interview session (capped strictly at 3 questions)
        focused explicitly on the provided skill_id.
        """
        from app.modules.academic.service import AcademicService
        from app.models.skill_taxonomy import SkillTaxonomy
        from app.models.roadmap import Roadmap, RoadmapTask
        from app.models.interview import InterviewQuestion
        
        _academic_svc = AcademicService()
        profile = _academic_svc.get_student_profile(db, user_id)
        branch = profile.department if profile else "CSE"
        
        skill = db.query(SkillTaxonomy).filter(SkillTaxonomy.id == skill_id).first()
        skill_name = skill.skill_name if skill else "Software Engineering"
        
        # Find corresponding roadmap task to associate
        roadmap = db.query(Roadmap).filter(Roadmap.user_id == user_id, Roadmap.status == "active").first()
        roadmap_task_id = None
        if roadmap:
            task = db.query(RoadmapTask).filter(
                RoadmapTask.roadmap_id == roadmap.id,
                RoadmapTask.skill_id == skill_id,
                RoadmapTask.phase == "apply"
            ).first()
            if task:
                roadmap_task_id = task.id
                
        # Specialized prompt for micro-interviews
        prompt = f"""You are a senior technical interviewer.
Conduct an advanced micro-interview focusing exclusively on the tool/skill: {skill_name}.
Bypass general icebreakers and warm-ups completely.
Generate exactly 3 extremely advanced code-review or troubleshooting puzzle questions targeting {skill_name}.
Each question must present a code snippet or architectural design containing a subtle bug, time complexity trap, security vulnerability, or concurrency deadlock, and ask the candidate to diagnose, debug, and fix it.

STRICT RULE:
Return ONLY a valid JSON object matching this schema exactly:
{{
  "questions": [
    {{
      "topic": "{skill_name}",
      "question": "string",
      "difficulty": "hard",
      "follow_up": "string"
    }}
  ]
}}
"""
        questions = []
        source = "static_fallback"
        
        # Try ML generators using 3-Tier Fallback
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
                parsed = json.loads(_strip_json_fences(raw))
                questions = parsed.get("questions", [])
                if isinstance(questions, list) and len(questions) > 0:
                    questions = questions[:3]
                    source = "groq"
            except Exception as e:
                logger.error(f"Micro-interview Tier 1 (Groq) failed: {e}")

        # Tier 2: Gemini
        if not questions and settings.GEMINI_API_KEY:
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
                    parsed = json.loads(_strip_json_fences(raw))
                    questions = parsed.get("questions", [])
                    if isinstance(questions, list) and len(questions) > 0:
                        questions = questions[:3]
                        source = "gemini"
            except Exception as e:
                logger.error(f"Micro-interview Tier 2 (Gemini) failed: {e}")

        # Tier 3: Static Fallback
        if not questions:
            logger.warning("Micro-interview Tier 1 and 2 failed. Falling back to static.")
            questions = [
                {
                    "topic": skill_name,
                    "question": f"Review this code snippet utilizing {skill_name}. Identify the concurrency leak or resource management error and show how to refactor it safely.",
                    "difficulty": "hard",
                    "follow_up": "What are the edge cases for this fix?"
                },
                {
                    "topic": skill_name,
                    "question": f"Explain the time and memory complexity footprint of {skill_name} under high payload volume. What design patterns resolve O(N^2) bottlenecks here?",
                    "difficulty": "hard",
                    "follow_up": "How does this scale across distributed nodes?"
                },
                {
                    "topic": skill_name,
                    "question": f"Identify a major security exploit (e.g. injection, session hijack) common in default implementations of {skill_name} and describe how to mitigate it.",
                    "difficulty": "hard",
                    "follow_up": "How do you test this vulnerability programmatically?"
                }
            ]
            source = "static_fallback"

        try:
            session = InterviewSession(
                user_id=user_id,
                branch=branch,
                topic=f"Micro-Interview: {skill_name}",
                status=SessionStatus.ACTIVE,
                is_micro=True,
                associated_skill_id=skill_id,
                roadmap_task_id=roadmap_task_id
            )
            db.add(session)
            db.flush()

            for q in questions:
                db.add(InterviewQuestion(
                    session_id=session.id,
                    topic=q.get("topic", skill_name),
                    question=q.get("question", ""),
                    difficulty=q.get("difficulty", "hard"),
                    source=source,
                    follow_up=q.get("follow_up"),
                ))

            db.commit()
            db.refresh(session)
            logger.info(
                "Micro-Interview session %s created: user=%s skill=%s",
                session.id, user_id, skill_name
            )
            return session
        except Exception:
            db.rollback()
            logger.exception("Failed to create micro-interview session — rolled back")
            raise

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
    "technical_score": 7,
    "communication_score": 8,
    "verdict": "Adequate",
    "feedback": "...",
    "model_answer": "...",
    "mistakes": ["...", "..."],
    "improvement": "..."
  }}
]

Rules:
- technical_score: integer from 1 to 10 evaluating technical accuracy
- communication_score: integer from 1 to 10 evaluating clarity and communication skills
- verdict:
    Strong (technical_score >= 8), Adequate (technical_score >= 5), Weak (technical_score <= 4)

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
    technical_score = 0
    communication_score = 0
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
        comm_scores = []
        for eval_item in evaluations:
            idx = eval_item.get("question_index", 1) - 1
            if not 0 <= idx < len(questions):
                continue
            q = questions[idx]
            tech_score = eval_item.get("technical_score", eval_item.get("score", 0))
            comm_score = eval_item.get("communication_score", 0)
            comm_scores.append(comm_score)
            
            q.ai_score = tech_score
            q.ai_verdict = eval_item.get("verdict")
            q.ai_feedback = eval_item.get("feedback")
            q.model_answer = eval_item.get("model_answer")
            q.mistakes = eval_item.get("mistakes", [])
            q.improvement = eval_item.get("improvement")
            q.evaluated_at = now

        db.commit()
        
        avg_comm = sum(comm_scores) / len(comm_scores) if comm_scores else 0.0

        # ------------------------------------------------------------------
        # Post-evaluation: extract weak skills (zero LLM calls)
        # ------------------------------------------------------------------
        weak_skills = extract_weak_skills(questions)
        _update_skill_weights(db, user_id, questions, avg_comm)

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

    async def evaluate_single_answer_async(
        self,
        db: Session,
        *,
        user_id: uuid.UUID,
        session_id: uuid.UUID,
        question_id: uuid.UUID,
        user_answer: str,
    ) -> dict:
        """
        Evaluate a single technical question answer using Gemini 1.5 Flash.
        Saves scores and applies weight calibration & score recalculation in real-time.
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

        question.user_answer = user_answer

        eval_prompt = f"""You are a senior technical interviewer evaluating a student's technical answer.
Question: {question.question}
Student's Answer: {user_answer}

STRICT RULE:
Return ONLY a valid JSON object matching this schema exactly:
{{
  "technical_score": 1..10,
  "communication_score": 1..10,
  "verdict": "Strong|Adequate|Weak",
  "feedback": "Concise 1-2 sentences of feedback",
  "mistakes": ["mistake 1", "mistake 2"],
  "improvement": "Actionable suggestion",
  "model_answer": "Concise ideal model answer"
}}
"""
        try:
            if not settings.GEMINI_API_KEY:
                raise ValueError("GEMINI_API_KEY not configured")
            url = (
                f"https://generativelanguage.googleapis.com/v1beta/models/"
                f"gemini-1.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
            )
            payload = {
                "contents": [{"parts": [{"text": eval_prompt}]}],
                "generationConfig": {"temperature": 0.3, "response_mime_type": "application/json"},
            }
            async with httpx.AsyncClient(timeout=30.0) as client_http:
                resp = await client_http.post(url, json=payload)
                resp.raise_for_status()
                raw = resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                eval_item = json.loads(_strip_json_fences(raw))
        except Exception as e:
            logger.error("Gemini real-time evaluation failed: %s", e)
            eval_item = {
                "technical_score": 5,
                "communication_score": 5,
                "verdict": "Adequate",
                "feedback": "Real-time evaluation fallback due to service interruption.",
                "mistakes": [],
                "improvement": "Review the question concepts.",
                "model_answer": "Model answer unavailable."
            }

        question.ai_score = eval_item.get("technical_score", 5)
        question.ai_verdict = eval_item.get("verdict", "Adequate")
        question.ai_feedback = eval_item.get("feedback")
        question.model_answer = eval_item.get("model_answer")
        question.mistakes = eval_item.get("mistakes", [])
        question.improvement = eval_item.get("improvement")
        question.evaluated_at = datetime.utcnow()

        import sqlalchemy as sa
        from app.models.student_skill import StudentSkill
        from app.models.skill_taxonomy import SkillTaxonomy
        from app.modules.skills.engine import calculate_composite_score
        from app.utils.academic import score_to_level

        topic = question.topic
        tech_score = int(question.ai_score)
        comm_score = int(eval_item.get("communication_score", 5))

        if db.bind.dialect.name == "sqlite":
            tax = (
                db.query(SkillTaxonomy)
                .filter(sa.func.lower(SkillTaxonomy.skill_name) == topic.lower())
                .first()
            )
            if not tax:
                # SQLite fallback python-based aliases search
                all_tax = db.query(SkillTaxonomy).all()
                for t in all_tax:
                    if t.aliases and any(topic.lower() in str(a).lower() for a in t.aliases):
                        tax = t
                        break
        else:
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

        new_conf = 0.0
        new_level = "weak"
        if tax:
            ss = (
                db.query(StudentSkill)
                .filter(
                    StudentSkill.user_id == user_id,
                    StudentSkill.skill_id == tax.id,
                )
                .first()
            )
            if not ss:
                ss = StudentSkill(
                    user_id=user_id,
                    skill_id=tax.id,
                    resume_weight=50.0,
                    project_weight=0.0,
                    interview_weight=0.0,
                    communication_weight=0.0,
                )
                db.add(ss)
                db.flush()

            current_int = float(ss.interview_weight) if ss.interview_weight else 0.0

            if tech_score >= 8:
                ss.interview_weight = min(current_int + 10.0, 100.0)
            elif tech_score <= 4:
                ss.interview_weight = max(current_int - 10.0, 0.0)

            ss.communication_weight = float(comm_score) * 10.0

            res_wt = float(ss.resume_weight) if ss.resume_weight else 0.0
            pr_wt = float(ss.project_weight) if ss.project_weight else 0.0
            in_wt = float(ss.interview_weight) if ss.interview_weight else 0.0
            comm_wt = float(ss.communication_weight) if ss.communication_weight else 0.0

            new_conf = calculate_composite_score(res_wt, pr_wt, in_wt, comm_wt)
            ss.confidence_score = new_conf
            ss.level = score_to_level(new_conf)
            new_level = ss.level

        db.commit()
        db.refresh(question)

        # Hook WebSocket Calibration into Roadmap Progress for micro-interviews
        session = question.session
        if session and session.is_micro:
            all_questions = session.questions
            all_evaluated = all(q.ai_score is not None for q in all_questions)
            if all_evaluated:
                scores = [int(q.ai_score) for q in all_questions]
                avg_score = sum(scores) / len(scores) if scores else 0.0
                if avg_score >= 7.0:
                    from app.models.roadmap import RoadmapTask
                    task = None
                    if session.roadmap_task_id:
                        task = db.query(RoadmapTask).filter(RoadmapTask.id == session.roadmap_task_id).first()
                    else:
                        from app.models.roadmap import Roadmap
                        roadmap = db.query(Roadmap).filter(Roadmap.user_id == user_id, Roadmap.status == "active").first()
                        if roadmap and session.associated_skill_id:
                            task = db.query(RoadmapTask).filter(
                                RoadmapTask.roadmap_id == roadmap.id,
                                RoadmapTask.skill_id == session.associated_skill_id,
                                RoadmapTask.phase == "apply"
                            ).first()
                    
                    if task:
                        task.status = "completed"
                        task.validation_status = "verified"
                        task.completed_at = datetime.utcnow()
                        
                        rm = task.roadmap
                        if rm:
                            rm.completed_tasks = (rm.completed_tasks or 0) + 1
                            if rm.completed_tasks >= rm.total_tasks:
                                rm.status = "completed"
                        
                        # Calibrate skill on task completion
                        from app.modules.roadmap.service import _update_skill_on_task_completion
                        _update_skill_on_task_completion(db, user_id, task.skill_id)
                        
                        db.commit()
                        logger.info("Micro-interview successful! RoadmapTask %s completed and verified", task.id)

        return {
            "question_id": str(question.id),
            "technical_score": tech_score,
            "communication_score": comm_score,
            "verdict": question.ai_verdict,
            "feedback": question.ai_feedback,
            "confidence_score": new_conf,
            "level": new_level,
        }


# ---------------------------------------------------------------------------
# Module-level singleton (imported by router)
# ---------------------------------------------------------------------------

interview_service = InterviewService()


async def create_micro_interview_session(user_id: uuid.UUID, skill_id: uuid.UUID, db: Session) -> InterviewSession:
    """Module-level initializer for micro-interview sessions."""
    return await interview_service.create_micro_interview_session(db, user_id, skill_id)


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


def _update_skill_weights(
    db: Session,
    user_id: UUID,
    questions: list,
    avg_comm: float,
) -> None:
    """
    Bi-directional confidence score update using technical and communication scores.
    Triggers composite score recalculation.
    """
    try:
        from app.models.student_skill import StudentSkill
        from app.models.skill_taxonomy import SkillTaxonomy
        from app.modules.skills.engine import calculate_composite_score
        from app.utils.academic import score_to_level
        import sqlalchemy as sa

        # First, add the average communication score to ALL skills for this student
        all_skills = db.query(StudentSkill).filter(StudentSkill.user_id == user_id).all()
        for ss in all_skills:
            current_comm = float(ss.communication_weight) if ss.communication_weight else 0.0
            ss.communication_weight = min(current_comm + avg_comm, 100.0)
            
        # Second, apply Technical Score logic per skill
        for q in questions:
            if q.ai_score is None:
                continue
            
            topic = q.topic
            tech_score = int(q.ai_score)
            
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
                continue

            ss = (
                db.query(StudentSkill)
                .filter(
                    StudentSkill.user_id == user_id,
                    StudentSkill.skill_id == tax.id,
                )
                .first()
            )
            if not ss:
                continue

            current_int = float(ss.interview_weight) if ss.interview_weight else 0.0
            
            if tech_score >= 8:
                ss.interview_weight = min(current_int + 10.0, 100.0)
            elif tech_score <= 4:
                ss.interview_weight = max(current_int - 10.0, 0.0)

            # Trigger calculate_composite_score
            res_wt = float(ss.resume_weight) if ss.resume_weight else 0.0
            pr_wt = float(ss.project_weight) if ss.project_weight else 0.0
            in_wt = float(ss.interview_weight) if ss.interview_weight else 0.0
            comm_wt = float(ss.communication_weight) if ss.communication_weight else 0.0
            
            new_conf = calculate_composite_score(res_wt, pr_wt, in_wt, comm_wt)
            ss.confidence_score = new_conf
            ss.level = score_to_level(new_conf)

        db.commit()
        logger.info("Skill weights updated for user %s", user_id)
    except Exception as exc:
        logger.warning("_update_skill_weights skipped due to error: %s", exc)
        db.rollback()
