"""
InterviewService (v2.0)
-----------------------
Phase 2: DB-backed sessions, async ML inference with fallback, and
session state lifecycle management.

Architectural refinements:
  - Transaction safety: session + questions in one atomic commit with rollback.
  - Lifecycle: status auto-advances to "completed" when all questions answered.
  - Performance: list_sessions() uses joinedload to avoid N+1 on question_count.
  - ML fallback: httpx call with configurable timeout; built-in bank on failure.

ML Sub-Service — Network Boundary
----------------------------------
The ML sub-service (configured via ML_SERVICE_URL) is an **internal service**
intended to run exclusively within the private Docker network.  It operates
without its own authentication layer by design:

  - It MUST NOT be exposed on a public port or via any public DNS name.
  - All authentication is handled by the core FastAPI application BEFORE
    this service is called.  The ML service trusts all callers implicitly.
  - In docker-compose, the ml_service container should NOT publish ports
    to the host (no "ports:" key, or only bind to 127.0.0.1).
  - The ML_SERVICE_URL env var should point to the Docker service name
    (e.g. http://ml_service:8001) so it is only reachable inside the
    compose network, never from outside.

Rationale: adding auth to the ML service is deferred to a future phase.
Until then, network isolation is the security boundary.
"""
from __future__ import annotations

import uuid
import random
import logging
from decimal import Decimal
from typing import Optional

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
        {"topic": "DSA",  "question": "Explain the concept of graph shortest path algorithms (Dijkstra vs Bellman-Ford).", "difficulty": "hard"},
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


class InterviewService:
    """Business logic for the Interview module (Phase 2 — DB-backed)."""

    # ------------------------------------------------------------------
    # Question generation — sync fallback
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
            bank = filtered if filtered else bank  # fallback if topic not found

        random.shuffle(bank)  # randomise order on every call

        follow_ups = [
            {
                "topic": subj,
                "question": _WEAK_SUBJECT_TEMPLATE.format(subject=subj),
                "difficulty": "medium",
                "source": "weak_subject_personalisation",
            }
            for subj in weak_subjects[:3]
        ]
        # Prepend follow-ups so they are guaranteed within the limit
        return (follow_ups + bank)[:limit]

    # ------------------------------------------------------------------
    # Question generation — async ML path with graceful fallback
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
        """
        Try the ML sub-service; retry once before falling back to built-in bank.

        Strategy:
          - Attempt 1: call ML service (timeout = ML_SERVICE_TIMEOUT)
          - Attempt 2 (retry): one more call on transient failure
          - If both attempts fail: return questions from the built-in bank

        Returns:
            (questions, source) where source is "ml_service" or "built-in".
        """
        payload = {
            "branch": branch,
            "semester": semester,
            "weak_subjects": weak_subjects,
            "overall_gpa": float(overall_gpa),
            "jd_text": jd_text,
            "resume_context": resume_context,
            "limit": limit,
        }
        url = f"{settings.ML_SERVICE_URL}/predict/questions"

        for attempt in range(2):  # attempt 0 = first try, attempt 1 = retry
            try:
                async with httpx.AsyncClient(timeout=settings.ML_SERVICE_TIMEOUT) as client:
                    resp = await client.post(url, json=payload)
                    resp.raise_for_status()
                    questions = resp.json().get("questions", [])
                    logger.info(
                        "ML service: %d questions for branch=%s (attempt %d)",
                        len(questions), branch, attempt + 1,
                    )
                    return questions, "ml_service"
            except Exception as exc:
                logger.warning(
                    "ML service attempt %d failed (%s)%s",
                    attempt + 1,
                    exc,
                    " — retrying" if attempt == 0 else " — falling back to built-in bank",
                )

        return (
            self.generate_questions(
                branch=branch,
                semester=semester,
                weak_subjects=weak_subjects,
                overall_gpa=overall_gpa,
                topic=None,   # built-in bank doesn't support JD filtering
                limit=limit,
            ),
            "built-in",
        )


    # ------------------------------------------------------------------
    # Session management — DB-backed with transaction safety
    # ------------------------------------------------------------------

    def list_sessions(
        self,
        db: Session,
        user_id: uuid.UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[InterviewSession], int]:
        """
        Return a paginated page of sessions for *user_id*, newest first.

        Uses joinedload to avoid N+1 on session.questions.
        Executes COUNT(*) + paginated SELECT in the same DB round-trip scope.

        Returns:
            (sessions, total) — total is the unpaginated count.
        """
        base_query = (
            db.query(InterviewSession)
            .filter(InterviewSession.user_id == user_id)
        )
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
        """
        Atomically persist a new session + all its questions.

        Transaction safety: if any question insert fails, the entire
        session creation is rolled back — no partial records in the DB.
        """
        try:
            session = InterviewSession(
                user_id=user_id,
                branch=branch,
                topic=topic,
                status=SessionStatus.ACTIVE,
            )
            db.add(session)
            db.flush()  # get session.id before creating questions

            for q in questions:
                db.add(
                    InterviewQuestion(
                        session_id=session.id,
                        topic=q.get("topic", "General"),
                        question=q.get("question", ""),
                        difficulty=q.get("difficulty", "medium"),
                        source=q.get("source", None),
                    )
                )

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
        """Return a session owned by *user_id*, eagerly loading its questions."""
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

        Lifecycle logic:
          - Stores the answer on the InterviewQuestion row.
          - If ALL questions in the session now have a user_answer,
            the session status is advanced to "completed".

        Returns:
            (question, session_completed) where session_completed is True
            when the session just transitioned to "completed".

        Raises:
            HTTP 404 if question not found or belongs to a different user's session.
        """
        # Load the question and its owning session in one query
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

        # Lifecycle check: mark session completed when all questions answered
        session_completed = False
        sibling_questions = (
            db.query(InterviewQuestion)
            .filter(InterviewQuestion.session_id == session_id)
            .all()
        )
        all_answered = all(
            (q.user_answer is not None and q.user_answer.strip() != "")
            for q in sibling_questions
            if q.id != question_id  # the current question's answer is in-memory
        )
        # Include the answer we're about to save
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
        """
        Delete a session and all its questions for the given user.

        Returns True if deleted, False if the session was not found
        (or belongs to a different user).
        """
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
