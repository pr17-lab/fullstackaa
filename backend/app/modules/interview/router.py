"""
Interview Module Router (v2.0)
------------------------------
Phase 2: DB-backed sessions, async ML question generation, answer submission
with session lifecycle management.

Endpoints
---------
GET  /api/interview/questions               — generate questions (ML or built-in)
GET  /api/interview/sessions                — list past sessions
POST /api/interview/sessions               — start + persist a new session
GET  /api/interview/sessions/{id}          — get session with all questions
POST /api/interview/sessions/{id}/answer   — submit answer; advances lifecycle
GET  /api/interview/health                 — module health probe
"""
from __future__ import annotations

import io
import uuid
import logging
from typing import Optional

import PyPDF2
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.dependencies.auth import get_current_user
from app.models.user import User
from app.modules.academic.service import AcademicService
from app.modules.interview.service import interview_service as _interview_svc
from app.schemas.interview import (
    AnswerSubmitRequest,
    AnswerSubmitResponse,
    GeneratedQuestionsResponse,
    InterviewSessionOut,
    SessionCreateRequest,
)

logger = logging.getLogger(__name__)
router = APIRouter()

_academic_svc = AcademicService()


# ---------------------------------------------------------------------------
# Question generation
# ---------------------------------------------------------------------------

@router.get("/questions", response_model=GeneratedQuestionsResponse)
async def get_interview_questions(
    topic: Optional[str] = Query(None, description="Filter by topic e.g. 'DSA'"),
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Generate interview questions tailored to the logged-in student.
    Tries the ML sub-service first; falls back to built-in bank if unreachable.
    The `source` field indicates which path was used.
    """
    try:
        profile = _academic_svc.get_student_profile(db, current_user.id)

        questions, source = await _interview_svc.generate_questions_async(
            branch=profile.department,
            semester=profile.semester,
            limit=limit,
        )

        return GeneratedQuestionsResponse(
            student_id=str(current_user.id),
            branch=profile.department,
            semester=profile.semester,
            questions=questions,
            source=source,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error generating questions: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate interview questions")


# ---------------------------------------------------------------------------
# Session management
# ---------------------------------------------------------------------------

@router.get("/sessions")
async def list_sessions(
    limit:  int = Query(20, ge=1, le=100, description="Max sessions per page"),
    offset: int = Query(0,  ge=0,        description="Number of sessions to skip"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List past interview sessions for the current user, newest first.

    Supports SQL-level pagination via `?limit=` and `?offset=` parameters.
    Returns `total` so clients can calculate page counts without a second request.
    """
    sessions, total = _interview_svc.list_sessions(
        db, current_user.id, limit=limit, offset=offset
    )
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "sessions": [
            {
                "id": str(s.id),
                "branch": s.branch,
                "topic": s.topic,
                "status": s.status,
                "created_at": s.created_at.isoformat() if s.created_at else None,
                "question_count": len(s.questions),
            }
            for s in sessions
        ],
    }


@router.post("/sessions/parse-resume")
async def parse_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """
    Extract text from an uploaded PDF resume.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    try:
        content = await file.read()
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
        text = ""
        for page in pdf_reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
        
        return {"text": text.strip()}
    except Exception as exc:
        logger.error("Error parsing PDF resume: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to parse PDF resume")


@router.post("/sessions", status_code=201, response_model=InterviewSessionOut)
async def create_session(
    body: SessionCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Start a new interview session.
    Generates questions, atomically persists session + questions, returns full session.
    """
    try:
        profile = _academic_svc.get_student_profile(db, current_user.id)

        questions, source = await _interview_svc.generate_questions_async(
            branch=profile.department,
            semester=profile.semester,
            jd_text=body.jd_text,
            resume_context=body.resume_context,
            limit=body.limit,
        )

        # Build a topic label — prefer JD snippet, fall back to resume snippet
        if body.jd_text.strip():
            raw_topic = body.jd_text.strip()
            topic_label = raw_topic[:80] + ("..." if len(raw_topic) > 80 else "")
        elif body.resume_context and body.resume_context.strip():
            raw_topic = body.resume_context.strip()
            topic_label = "Resume: " + raw_topic[:72] + ("..." if len(raw_topic) > 72 else "")
        else:
            topic_label = "General Interview"

        session = _interview_svc.create_session(
            db,
            user_id=current_user.id,
            branch=profile.department,
            topic=topic_label,
            questions=questions,
        )
        logger.info(
            "Session %s created for user %s (%d questions, source=%s)",
            session.id, current_user.id, len(session.questions), source,
        )
        return session
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error creating interview session: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create interview session")


@router.get("/sessions/{session_id}", response_model=InterviewSessionOut)
async def get_session(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get full details and all questions for a specific session."""
    session = _interview_svc.get_session(db, session_id, current_user.id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.post("/sessions/{session_id}/answer", response_model=AnswerSubmitResponse)
async def submit_answer(
    session_id: uuid.UUID,
    body: AnswerSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Submit a student's answer for a question.
    When all questions in the session are answered, status advances to 'completed'.
    """
    question, session_completed = _interview_svc.submit_answer(
        db,
        session_id=session_id,
        question_id=body.question_id,
        user_id=current_user.id,
        answer=body.answer,
    )
    return AnswerSubmitResponse(
        id=question.id,
        question=question.question,
        user_answer=question.user_answer,
        session_completed=session_completed,
    )

@router.post("/sessions/{session_id}/evaluate")
async def evaluate_session(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Evaluate all answered questions via Groq AI.
    Assigns scores, verdicts, model answers, and concise feedback.
    """
    return await _interview_svc.evaluate_session(db, session_id, current_user.id)

@router.delete("/sessions/{session_id}", status_code=204)
async def delete_session(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Permanently delete an interview session and all its questions.
    Returns 204 No Content on success, 404 if the session is not found.
    """
    deleted = _interview_svc.delete_session(db, session_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")


# ---------------------------------------------------------------------------
# Real-Time WebSocket technical screen & evaluation
# ---------------------------------------------------------------------------

import json

async def get_websocket_user(websocket: WebSocket, db: Session) -> Optional[User]:
    token = websocket.query_params.get("token")
    print("DEBUG get_websocket_user: token from query params =", token)
    if not token:
        token = websocket.cookies.get("access_token")
        print("DEBUG get_websocket_user: token from cookies =", token)
    if not token:
        print("DEBUG get_websocket_user: no token found")
        return None
    
    # Strip enclosing quotes if present (e.g. Starlette TestClient cookie format)
    token = token.strip('"').strip("'")
    
    if token.startswith("Bearer "):
        token = token[7:]
        print("DEBUG get_websocket_user: stripped Bearer, raw =", token)
    
    try:
        from app.core.security import decode_access_token
        payload = decode_access_token(token)
        print("DEBUG get_websocket_user: decoded payload =", payload)
        if payload is None:
            return None
        email = payload.get("sub")
        print("DEBUG get_websocket_user: email =", email)
        if email is None:
            return None
        user = db.query(User).filter(User.email == email).first()
        print("DEBUG get_websocket_user: user =", user)
        return user
    except Exception as exc:
        print("DEBUG get_websocket_user: exception =", exc)
        return None


@router.websocket("/ws/interview/{session_id}")
async def websocket_interview(
    websocket: WebSocket,
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    await websocket.accept()
    
    try:
        user = await get_websocket_user(websocket, db)
        if not user:
            await websocket.send_json({"event": "error", "data": {"message": "Unauthorized"}})
            await websocket.close()
            return
            
        from app.models.interview import InterviewSession
        session = (
            db.query(InterviewSession)
            .filter(
                InterviewSession.id == session_id,
                InterviewSession.user_id == user.id,
            )
            .first()
        )
        if not session:
            await websocket.send_json({"event": "error", "data": {"message": "Session not found"}})
            await websocket.close()
            return
            
        if len(session.questions) > 0:
            await websocket.send_json({
                "event": "session_ready",
                "data": {
                    "session_id": str(session.id),
                    "questions": [
                        {
                            "question_id": str(q.id),
                            "topic": q.topic,
                            "question": q.question,
                            "difficulty": q.difficulty,
                            "user_answer": q.user_answer,
                            "ai_score": q.ai_score,
                            "ai_verdict": q.ai_verdict,
                        }
                        for q in session.questions
                    ]
                }
            })
        else:
            await websocket.send_json({
                "event": "session_created",
                "data": {
                    "session_id": str(session.id),
                    "message": "Session is active. Send 'start_interview' event to generate code review questions."
                }
            })
            
        while True:
            try:
                data = await websocket.receive_json()
                event = data.get("event")
                payload = data.get("data", {})
                
                if event == "start_interview":
                    jd_text = payload.get("jd_text", "")
                    resume_context = payload.get("resume_context", "")
                    limit = int(payload.get("limit", 5))
                    
                    async def on_chunk(token: str):
                        await websocket.send_json({
                            "event": "stream_chunk",
                            "data": {"token": token}
                        })
                    
                    try:
                        questions, source = await _interview_svc.generate_questions_async(
                            branch=session.branch,
                            semester=user.profile.semester if user.profile else 1,
                            jd_text=jd_text,
                            resume_context=resume_context,
                            limit=limit,
                            on_chunk=on_chunk
                        )
                        
                        from app.models.interview import InterviewQuestion
                        for q in questions:
                            db.add(InterviewQuestion(
                                session_id=session.id,
                                topic=q.get("topic", "General"),
                                question=q.get("question", ""),
                                difficulty=q.get("difficulty", "medium"),
                                source=source,
                                follow_up=q.get("follow_up"),
                            ))
                        db.commit()
                        db.refresh(session)
                        
                        await websocket.send_json({
                            "event": "session_ready",
                            "data": {
                                "session_id": str(session.id),
                                "questions": [
                                    {
                                        "question_id": str(q.id),
                                        "topic": q.topic,
                                        "question": q.question,
                                        "difficulty": q.difficulty,
                                    }
                                    for q in session.questions
                                ]
                            }
                        })
                    except Exception as e:
                        logger.error("Error generating questions in WebSocket: %s", e)
                        await websocket.send_json({
                            "event": "error",
                            "data": {"message": f"Question generation failed: {str(e)}"}
                        })
                        
                elif event == "submit_answer":
                    question_id_str = payload.get("question_id")
                    answer_text = payload.get("answer_text", "")
                    
                    try:
                        question_id = uuid.UUID(question_id_str)
                        
                        result = await _interview_svc.evaluate_single_answer_async(
                            db,
                            user_id=user.id,
                            session_id=session.id,
                            question_id=question_id,
                            user_answer=answer_text
                        )
                        
                        await websocket.send_json({
                            "event": "answer_evaluated",
                            "data": result
                        })
                        
                        from app.models.interview import SessionStatus
                        sibling_questions = session.questions
                        all_answered = all(
                            (q.user_answer is not None and q.user_answer.strip())
                            for q in sibling_questions
                        )
                        if all_answered and session.status == SessionStatus.ACTIVE:
                            session.status = SessionStatus.COMPLETED
                            db.commit()
                            await websocket.send_json({
                                "event": "session_completed",
                                "data": {
                                    "session_id": str(session.id),
                                    "message": "All interview questions answered. Session completed."
                                }
                            })
                    except Exception as e:
                        logger.error("Error submitting answer in WebSocket: %s", e)
                        await websocket.send_json({
                            "event": "error",
                            "data": {"message": f"Answer submission failed: {str(e)}"}
                        })
                        
                else:
                    await websocket.send_json({
                        "event": "error",
                        "data": {"message": f"Unknown event: {event}"}
                    })
                    
            except json.JSONDecodeError:
                await websocket.send_json({"event": "error", "data": {"message": "Invalid JSON frame"}})
                
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected for session: %s", session_id)
    except Exception as e:
        logger.error("Error in WebSocket session %s: %s", session_id, e)
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Health probe
# ---------------------------------------------------------------------------

@router.get("/health")
async def interview_health():
    return {"module": "interview", "status": "ok", "version": "2.0.0"}
