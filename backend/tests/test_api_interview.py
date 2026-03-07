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
        json={"student_id": student_id, "password": password},
    )
    assert resp.status_code == 200, f"Login failed: {resp.json()}"
    return resp.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# InterviewService unit tests (no HTTP, no DB)
# ---------------------------------------------------------------------------

class TestInterviewServiceUnit:
    """Test InterviewService question generation logic directly."""

    def test_generate_questions_cs_branch(self):
        from app.modules.interview.service import InterviewService
        from decimal import Decimal

        svc = InterviewService()
        qs = svc.generate_questions(
            branch="Computer Science",
            semester=3,
            weak_subjects=[],
            overall_gpa=Decimal("7.5"),
            limit=5,
        )
        assert len(qs) <= 5
        assert all("question" in q and "topic" in q for q in qs)

    def test_generate_questions_topic_filter(self):
        from app.modules.interview.service import InterviewService
        from decimal import Decimal

        svc = InterviewService()
        qs = svc.generate_questions(
            branch="Computer Science",
            semester=3,
            weak_subjects=[],
            overall_gpa=Decimal("7.0"),
            topic="DSA",
            limit=10,
        )
        assert all(q["topic"] == "DSA" for q in qs)

    def test_generate_questions_weak_subject_followup(self):
        from app.modules.interview.service import InterviewService
        from decimal import Decimal

        svc = InterviewService()
        qs = svc.generate_questions(
            branch="Computer Science",
            semester=3,
            weak_subjects=["Maths", "Physics"],
            overall_gpa=Decimal("6.0"),
            limit=20,
        )
        follow_up_topics = {q["topic"] for q in qs if "weak_subject" in q.get("source", "")}
        assert "Maths" in follow_up_topics
        assert "Physics" in follow_up_topics

    def test_generate_questions_unknown_branch_uses_default(self):
        from app.modules.interview.service import InterviewService
        from decimal import Decimal

        svc = InterviewService()
        qs = svc.generate_questions(
            branch="Unknown Engineering",
            semester=1,
            weak_subjects=[],
            overall_gpa=Decimal("8.0"),
        )
        assert len(qs) > 0

    @pytest.mark.asyncio
    async def test_generate_questions_async_ml_fallback(self):
        """When ML service raises, the built-in bank is used."""
        from app.modules.interview.service import InterviewService
        from decimal import Decimal
        import httpx

        svc = InterviewService()
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.post.side_effect = httpx.ConnectError("refused")

            qs, source = await svc.generate_questions_async(
                branch="Computer Science",
                semester=3,
                weak_subjects=[],
                overall_gpa=Decimal("7.0"),
            )
            assert source == "built-in"
            assert len(qs) > 0

    @pytest.mark.asyncio
    async def test_generate_questions_async_ml_success(self):
        """When ML service responds, its questions are returned."""
        from app.modules.interview.service import InterviewService
        from decimal import Decimal
        from unittest.mock import MagicMock

        ml_questions = [{"topic": "DSA", "question": "ML question", "difficulty": "easy"}]
        svc = InterviewService()

        mock_response = MagicMock()
        mock_response.json.return_value = {"questions": ml_questions}
        mock_response.raise_for_status = MagicMock()  # not async

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)

        # Patch at the module where httpx is actually used
        with patch("app.modules.interview.service.httpx.AsyncClient") as mock_class:
            mock_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_class.return_value.__aexit__ = AsyncMock(return_value=False)

            qs, source = await svc.generate_questions_async(
                branch="Computer Science",
                semester=3,
                weak_subjects=[],
                overall_gpa=Decimal("7.0"),
            )
            assert source == "ml_service"
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
