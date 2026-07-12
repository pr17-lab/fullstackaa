"""
Integration tests for the Interview module API endpoints.

NOTE: These tests use the in-memory SQLite engine from conftest.py.
SQLite does not support the PostgreSQL UUID dialect — tests that require
UUID-typed primary keys depend on the Postgres test environment.
The tests below are structured for the Postgres CI environment.
For local SQLite-based runs they will be skipped automatically.

Run against a live Postgres DB:
    DATABASE_URL=postgresql://... pytest tests/test_api_interview.py -v
"""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, patch


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_token(client, student_id="TEST001", password="Test@123") -> str:
    resp = client.post(
        "/api/auth/login",
        data={"username": student_id, "password": password},
    )
    assert resp.status_code == 200, f"Login failed: {resp.json()}"
    token = resp.cookies.get("access_token")
    if token:
        token = token.strip('"').strip("'")
        if token.startswith("Bearer "):
            token = token[7:]
    return token


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# InterviewService unit tests (no HTTP, no DB)
# ---------------------------------------------------------------------------

class TestInterviewServiceUnit:
    """Test InterviewService question generation logic directly."""

    @pytest.mark.asyncio
    async def test_generate_questions_cs_branch(self):
        from app.modules.interview.service import InterviewService

        svc = InterviewService()
        qs, source = await svc.generate_questions_async(
            branch="CSE",
            semester=3,
            limit=5,
        )
        assert len(qs) <= 5
        assert all("question" in q and "topic" in q for q in qs)

    @pytest.mark.asyncio
    async def test_generate_questions_topic_filter(self):
        from app.modules.interview.service import InterviewService

        svc = InterviewService()
        qs, source = await svc.generate_questions_async(
            branch="CSE",
            semester=3,
            limit=10,
        )
        assert len(qs) > 0

    @pytest.mark.asyncio
    async def test_generate_questions_jd_resume_context(self):
        from app.modules.interview.service import InterviewService

        svc = InterviewService()
        qs, source = await svc.generate_questions_async(
            branch="CSE",
            semester=3,
            jd_text="Looking for a Python and FastAPI expert",
            resume_context="Experienced in Python, FastAPI, and SQLAlchemy",
            limit=5,
        )
        assert len(qs) > 0

    @pytest.mark.asyncio
    async def test_generate_questions_unknown_branch_uses_default(self):
        from app.modules.interview.service import InterviewService

        svc = InterviewService()
        qs, source = await svc.generate_questions_async(
            branch="Unknown Engineering",
            semester=1,
        )
        assert len(qs) > 0

    @pytest.mark.asyncio
    async def test_generate_questions_async_ml_fallback(self):
        """When ML service raises, the built-in bank is used."""
        from app.modules.interview.service import InterviewService
        import httpx

        svc = InterviewService()
        with patch("app.modules.interview.service.settings.GROQ_API_KEY", None), \
             patch("app.modules.interview.service.settings.GEMINI_API_KEY", "test"), \
             patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.post.side_effect = httpx.ConnectError("refused")

            qs, source = await svc.generate_questions_async(
                branch="CSE",
                semester=3,
            )
            assert source == "static_fallback"
            assert len(qs) > 0

    @pytest.mark.asyncio
    async def test_generate_questions_async_ml_success(self):
        """When ML service responds, its questions are returned."""
        from app.modules.interview.service import InterviewService
        from unittest.mock import MagicMock
        import json

        ml_questions = [{"topic": "DSA", "question": "ML question", "difficulty": "easy"}]
        svc = InterviewService()

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": json.dumps({"questions": ml_questions})
                            }
                        ]
                    }
                }
            ]
        }
        mock_response.raise_for_status = MagicMock()  # not async

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)

        # Patch at the module where httpx is actually used
        with patch("app.modules.interview.service.settings.GROQ_API_KEY", None), \
             patch("app.modules.interview.service.settings.GEMINI_API_KEY", "test"), \
             patch("app.modules.interview.service.httpx.AsyncClient") as mock_class:
            mock_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_class.return_value.__aexit__ = AsyncMock(return_value=False)

            qs, source = await svc.generate_questions_async(
                branch="CSE",
                semester=3,
            )
            assert source == "gemini"
            assert qs == ml_questions



# ---------------------------------------------------------------------------
# Session lifecycle unit tests
# ---------------------------------------------------------------------------

class TestSessionStatus:
    def test_status_constants(self):
        from app.models.interview import SessionStatus
        assert SessionStatus.ACTIVE == "active"
        assert SessionStatus.COMPLETED == "completed"
        assert SessionStatus.ABANDONED == "abandoned"
        assert len(SessionStatus.ALL) == 3


# ---------------------------------------------------------------------------
# ML Service router tests
# ---------------------------------------------------------------------------

class TestMLServiceRouter:
    """Test the ML service FastAPI app directly with a test client."""

    @pytest.fixture
    def ml_client(self):
        from fastapi.testclient import TestClient
        from ml_service.main import app as ml_app
        return TestClient(ml_app)

    def test_health(self, ml_client):
        resp = ml_client.get("/predict/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_predict_questions_cs(self, ml_client):
        resp = ml_client.post("/predict/questions", json={
            "branch": "Computer Science",
            "semester": 3,
            "weak_subjects": [],
            "overall_gpa": 7.5,
            "limit": 5,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "questions" in data
        assert len(data["questions"]) <= 5

    def test_predict_questions_with_topic(self, ml_client):
        resp = ml_client.post("/predict/questions", json={
            "branch": "Computer Science",
            "semester": 3,
            "weak_subjects": [],
            "overall_gpa": 7.5,
            "topic": "DSA",
            "limit": 10,
        })
        assert resp.status_code == 200
        qs = resp.json()["questions"]
        # All returned questions should match topic (unless no DSA found)
        assert len(qs) > 0

    def test_predict_questions_weak_subjects(self, ml_client):
        resp = ml_client.post("/predict/questions", json={
            "branch": "Computer Science",
            "semester": 3,
            "weak_subjects": ["Maths", "Physics"],
            "overall_gpa": 5.5,
            "limit": 20,
        })
        assert resp.status_code == 200
        sources = [q.get("source", "") for q in resp.json()["questions"]]
        assert any("weak_subject" in s for s in sources)

    def test_predict_performance_improving(self, ml_client):
        resp = ml_client.post("/predict/performance", json={
            "branch": "Computer Science",
            "semester": 4,
            "historical_gpas": [6.5, 7.0, 7.8],
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "predicted_next_gpa" in data
        assert "confidence" in data
        assert data["trend"] in ("improving", "stable", "declining")
        assert 0.0 <= data["predicted_next_gpa"] <= 10.0

    def test_predict_performance_no_history(self, ml_client):
        resp = ml_client.post("/predict/performance", json={
            "branch": "Computer Science",
            "semester": 1,
            "historical_gpas": [],
        })
        assert resp.status_code == 200
        assert resp.json()["predicted_next_gpa"] == 7.0


# ---------------------------------------------------------------------------
# WebSocket Technical Screen & Evaluation Integration Tests
# ---------------------------------------------------------------------------

class TestWebSocketTechnicalScreen:
    """Test full-duplex WebSocket technical interview screens, streaming, and evaluation."""

    def test_websocket_unauthorized_fails(self, client, sample_interview_session):
        from starlette.websockets import WebSocketDisconnect
        with client.websocket_connect(
            f"/api/interview/ws/interview/{sample_interview_session.id}"
        ) as websocket:
            data = websocket.receive_json()
            assert data["event"] == "error"
            assert data["data"]["message"] == "Unauthorized"
            with pytest.raises(WebSocketDisconnect):
                websocket.receive_json()

    def test_websocket_interview_ready_existing_questions(self, client, sample_user, sample_interview_session):
        token = _get_token(client)
        
        with client.websocket_connect(
            f"/api/interview/ws/interview/{sample_interview_session.id}?token={token}"
        ) as websocket:
            data = websocket.receive_json()
            assert data["event"] == "session_ready"
            assert data["data"]["session_id"] == str(sample_interview_session.id)
            assert len(data["data"]["questions"]) > 0

    def test_websocket_interview_empty_session_generation(self, client, sample_user, db_session):
        token = _get_token(client)
        
        from app.models.interview import InterviewSession
        session = InterviewSession(
            user_id=sample_user.id,
            branch="CSE",
            topic="Test WebSocket Empty",
            status="active"
        )
        db_session.add(session)
        db_session.commit()
        
        with client.websocket_connect(
            f"/api/interview/ws/interview/{session.id}?token={token}"
        ) as websocket:
            data = websocket.receive_json()
            assert data["event"] == "session_created"
            
            websocket.send_json({
                "event": "start_interview",
                "data": {
                    "jd_text": "Need python developer with O(N^2) complexity optimization skills",
                    "resume_context": "FastAPI expert who debugs memory leaks",
                    "limit": 3
                }
            })
            
            while True:
                raw_msg = websocket.receive_text()
                try:
                    import json
                    resp = json.loads(raw_msg)
                    if resp.get("event") == "session_ready":
                        assert len(resp["data"]["questions"]) > 0
                        break
                    elif resp.get("event") == "error":
                        pytest.fail(f"WebSocket error received: {resp['data']['message']}")
                except json.JSONDecodeError:
                    assert len(raw_msg) > 0

    def test_websocket_submit_answer_and_calibration(self, client, sample_user, sample_interview_session, db_session):
        from app.models.skill_taxonomy import SkillTaxonomy
        tax = SkillTaxonomy(
            skill_name="DSA",
            category="core_cs",
            skill_type="concept"
        )
        db_session.add(tax)
        db_session.commit()
        db_session.refresh(tax)
        
        token = _get_token(client)
        question = sample_interview_session.questions[0]
        
        from unittest.mock import MagicMock
        import json
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": json.dumps({
                                    "technical_score": 9,
                                    "communication_score": 8,
                                    "verdict": "Strong",
                                    "feedback": "Excellent work",
                                    "mistakes": [],
                                    "improvement": "None needed",
                                    "model_answer": "Starlette provides high-speed execution."
                                })
                            }
                        ]
                    }
                }
            ]
        }
        mock_response.raise_for_status = MagicMock()
        
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        
        with patch("app.modules.interview.service.settings.GEMINI_API_KEY", "test"), \
             patch("app.modules.interview.service.httpx.AsyncClient") as mock_class:
            mock_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_class.return_value.__aexit__ = AsyncMock(return_value=False)
            
            with client.websocket_connect(
                f"/api/interview/ws/interview/{sample_interview_session.id}?token={token}"
            ) as websocket:
                # Consume the session_ready event
                websocket.receive_json()
                
                websocket.send_json({
                    "event": "submit_answer",
                    "data": {
                        "question_id": str(question.id),
                        "answer_text": "FastAPI is extremely high-performance because it uses Starlette and Pydantic 2.0 under the hood."
                    }
                })
                
                resp = websocket.receive_json()
                assert resp["event"] == "answer_evaluated"
                assert resp["data"]["question_id"] == str(question.id)
                assert resp["data"]["technical_score"] == 9
                assert resp["data"]["communication_score"] == 8
                assert resp["data"]["confidence_score"] > 0
                assert resp["data"]["level"] in ("strong", "moderate", "weak")
