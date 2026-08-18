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
    PracticeTopicCreateRequest,
    PracticeProjectCreateRequest,
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

        jd_text = body.jd_text
        associated_skill_id = None
        is_micro_session = False

        if body.roadmap_task_id:
            from app.models.roadmap import RoadmapTask
            from app.models.skill_taxonomy import SkillTaxonomy
            task = db.query(RoadmapTask).filter(RoadmapTask.id == body.roadmap_task_id).first()
            if not task:
                raise HTTPException(status_code=404, detail="Roadmap task not found")
            
            skill = task.associated_skill or task.skill
            if not skill and task.skill_id:
                skill = db.query(SkillTaxonomy).filter(SkillTaxonomy.id == task.skill_id).first()
            
            if skill:
                associated_skill_id = skill.id
                is_micro_session = True
                from app.modules.interview.service import build_skill_practice_context
                jd_text = build_skill_practice_context(db, skill.id)

        from app.models.student_skill import StudentSkill
        student_skills = (
            db.query(StudentSkill)
            .filter(StudentSkill.user_id == current_user.id)
            .all()
        )

        questions, source = await _interview_svc.generate_questions_async(
            branch=profile.department,
            semester=profile.semester,
            jd_text=jd_text,
            student_skills=student_skills,
            limit=body.limit,
        )

        # Build a topic label
        if body.roadmap_task_id and associated_skill_id:
            from app.models.skill_taxonomy import SkillTaxonomy
            skill = db.query(SkillTaxonomy).filter(SkillTaxonomy.id == associated_skill_id).first()
            topic_label = f"Practice Interview: {skill.skill_name if skill else 'Skill'}"
        elif jd_text.strip():
            raw_topic = jd_text.strip()
            topic_label = raw_topic[:80] + ("..." if len(raw_topic) > 80 else "")
        else:
            topic_label = "General Interview"

        session = _interview_svc.create_session(
            db,
            user_id=current_user.id,
            branch=profile.department,
            topic=topic_label,
            questions=questions,
        )

        if body.roadmap_task_id:
            session.roadmap_task_id = body.roadmap_task_id
            session.associated_skill_id = associated_skill_id
            session.is_micro = is_micro_session
            db.commit()
            db.refresh(session)

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


@router.post("/sessions/micro", status_code=201, response_model=InterviewSessionOut)
async def create_micro_session(
    skill_id: uuid.UUID,
    roadmap_task_id: Optional[uuid.UUID] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Start a specialized micro-interview session focused explicitly on the provided skill_id.
    """
    try:
        session = await _interview_svc.create_micro_interview_session(
            db, current_user.id, skill_id, roadmap_task_id
        )
        return session
    except Exception as exc:
        logger.error("Error creating micro-interview session: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/sessions/practice-topic", status_code=201, response_model=InterviewSessionOut)
async def create_practice_topic_session(
    body: PracticeTopicCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Start a practice interview session for a specific topic (skill_id) from the taxonomy.
    """
    try:
        from app.models.skill_taxonomy import SkillTaxonomy
        skill = db.query(SkillTaxonomy).filter(SkillTaxonomy.id == body.skill_id).first()
        if not skill:
            raise HTTPException(status_code=404, detail="Skill not found")

        from app.modules.interview.service import build_skill_practice_context
        jd_text = build_skill_practice_context(db, body.skill_id)

        profile = _academic_svc.get_student_profile(db, current_user.id)
        branch = profile.department if profile else "CSE"
        semester = profile.semester if profile else 3
        
        from app.models.student_skill import StudentSkill
        student_skills = (
            db.query(StudentSkill)
            .filter(StudentSkill.user_id == current_user.id)
            .all()
        )

        questions, source = await _interview_svc.generate_questions_async(
            branch=branch,
            semester=semester,
            jd_text=jd_text,
            student_skills=student_skills,
            limit=body.limit or 3,
            associated_skill_id=body.skill_id,
            db=db,
        )

        topic_label = f"Practice Interview: {skill.skill_name}"

        session = _interview_svc.create_session(
            db,
            user_id=current_user.id,
            branch=branch,
            topic=topic_label,
            questions=questions,
        )
        
        session.associated_skill_id = body.skill_id
        session.is_micro = True
        db.commit()
        db.refresh(session)
        
        logger.info(
            "Practice-topic session %s created: user=%s skill=%s",
            session.id, current_user.id, skill.skill_name
        )
        return session
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error creating practice-topic session: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/sessions/practice-project", status_code=201, response_model=InterviewSessionOut)
async def create_practice_project_session(
    body: PracticeProjectCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Start a project depth-verification practice interview session.
    Grounds question generation in the project's repository context (files, README, tech stack).
    """
    try:
        session = await _interview_svc.create_practice_project_session(
            db,
            user_id=current_user.id,
            project_id=body.project_id,
            limit=body.limit or 3,
        )
        return session
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error creating project practice session: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


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
            await websocket.close(code=4001, reason="Unauthorized")
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
            await websocket.close(code=4004, reason="Session not found")
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
                    limit = int(payload.get("limit", 5))
                    
                    async def on_chunk(token: str):
                        await websocket.send_text(token)
                    
                    try:
                        from app.models.student_skill import StudentSkill
                        student_skills = (
                            db.query(StudentSkill)
                            .filter(StudentSkill.user_id == user.id)
                            .all()
                        )

                        questions, source = await _interview_svc.generate_questions_async(
                            branch=session.branch,
                            semester=user.profile.semester if user.profile else 1,
                            jd_text=jd_text,
                            student_skills=student_skills,
                            limit=1,
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
                        
                        payload_data = {
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
                        await websocket.send_json({
                            "event": "question_complete",
                            "data": payload_data
                        })
                        await websocket.send_json({
                            "event": "session_ready",
                            "data": payload_data
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
                        
                        db.refresh(session)
                        target_limit = 3 if session.is_micro else 5
                        if len(session.questions) < target_limit:
                            async def on_chunk(token: str):
                                await websocket.send_text(token)
                            next_q, source = await _interview_svc.generate_next_question_async(
                                db=db,
                                session=session,
                                user_id=user.id,
                                on_chunk=on_chunk
                            )
                            
                            from app.models.interview import InterviewQuestion
                            db.add(InterviewQuestion(
                                session_id=session.id,
                                topic=next_q.get("topic", "General"),
                                question=next_q.get("question", ""),
                                difficulty=next_q.get("difficulty", "medium"),
                                source=source,
                                follow_up=next_q.get("follow_up"),
                            ))
                            db.commit()
                            db.refresh(session)
                            
                            payload_data = {
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
                            await websocket.send_json({
                                "event": "question_complete",
                                "data": payload_data
                            })
                            await websocket.send_json({
                                "event": "session_ready",
                                "data": payload_data
                            })
                        else:
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
                        
                elif event == "ping":
                    await websocket.send_json({"event": "pong", "data": {}})
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
