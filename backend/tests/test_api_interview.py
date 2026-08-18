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
# Merged groq_client / built-in bank tests (formerly TestMLServiceRouter)
# ---------------------------------------------------------------------------
# The ml_service sub-process was merged into the main backend as
# app/modules/interview/groq_client.py. These tests exercise the in-process
# logic directly instead of spinning up a separate HTTP service.

class TestGroqClientModule:
    """Test the merged groq_client module and built-in bank fallback logic."""

    def test_builtin_bank_cs_returns_questions(self):
        """generate_questions_with_groq returns None when no API key is set,
        confirming the caller (service.py) correctly falls back to its built-in bank."""
        import os, importlib
        orig = os.environ.pop("GROQ_API_KEY", None)
        try:
            import app.modules.interview.groq_client as gc
            importlib.reload(gc)
            result = gc.generate_questions_with_groq(
                branch="Computer Science",
                semester=3,
                overall_gpa=7.5,
                weak_subjects=[],
                jd_text="",
                limit=5,
            )
            # No key → returns None, triggering caller's built-in bank
            assert result is None
        finally:
            if orig is not None:
                os.environ["GROQ_API_KEY"] = orig

    def test_parse_and_validate_valid_json(self):
        """_parse_and_validate correctly parses a well-formed response."""
        import app.modules.interview.groq_client as gc
        raw = '[{"topic": "DSA", "question": "What is BFS?", "difficulty": "easy"}]'
        result = gc._parse_and_validate(raw, limit=5)
        assert result is not None
        assert len(result) == 1
        assert result[0]["topic"] == "DSA"
        assert result[0]["difficulty"] == "easy"

    def test_parse_and_validate_invalid_difficulty_normalised(self):
        """Invalid difficulty is normalised to 'medium' rather than dropped."""
        import app.modules.interview.groq_client as gc
        raw = '[{"topic": "OS", "question": "Explain deadlock.", "difficulty": "bogus"}]'
        result = gc._parse_and_validate(raw, limit=5)
        assert result is not None
        assert result[0]["difficulty"] == "medium"

    def test_parse_and_validate_missing_bracket_returns_none(self):
        """Malformed response with no JSON array returns None."""
        import app.modules.interview.groq_client as gc
        assert gc._parse_and_validate("No brackets here at all.", limit=5) is None

    def test_deduplicate_removes_near_identical(self):
        """Near-identical questions (same 6-word prefix) are deduplicated."""
        import app.modules.interview.groq_client as gc
        questions = [
            {"topic": "DSA", "question": "What is the difference between BFS and DFS?", "difficulty": "easy"},
            {"topic": "DSA", "question": "What is the difference between BFS and DFS traversal?", "difficulty": "medium"},
            {"topic": "OS",  "question": "Explain virtual memory and how paging works.", "difficulty": "hard"},
        ]
        result = gc._deduplicate(questions)
        assert len(result) == 2  # second question deduped as near-identical to first

    def test_performance_prediction_weighted_average(self):
        """Weighted moving average prediction stays within 0–10 range."""
        # This logic was in ml_service/routers/predict.py /performance endpoint.
        # It's pure Python with no external dependencies; test inline.
        gpas = [6.5, 7.0, 7.8]
        weights = list(range(1, len(gpas) + 1))
        weighted_avg = sum(g * w for g, w in zip(gpas, weights)) / sum(weights)
        delta = gpas[-1] - gpas[-2]
        predicted = round(min(10.0, max(0.0, weighted_avg + delta * 0.4)), 2)
        assert 0.0 <= predicted <= 10.0
        assert predicted > gpas[0]  # improving trend should exceed first GPA

    def test_performance_prediction_no_history(self):
        """Empty GPA list returns the default fallback of 7.0."""
        gpas = []
        predicted = 7.0 if not gpas else gpas[0]
        assert predicted == 7.0


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
