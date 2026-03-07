"""
Test configuration and fixtures.

Uses an in-memory SQLite database for fast, isolated tests.

Key design decisions:
  1. UUID shim  – SQLite doesn't understand the PostgreSQL UUID dialect, so we
     monkey-patch its type compiler to render UUID columns as VARCHAR(36).
  2. Table cleanup – an autouse fixture deletes all rows before every test so
     committed data never leaks between tests.
  3. Rate-limiter reset – slowapi counters are cleared before each test so
     failed-login tests don't trigger the global rate limit on subsequent tests.
"""
import uuid
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.core.database import Base, get_db
from app.main import app
from app.models import (
    User, StudentProfile, AcademicTerm, Subject,
    InterviewSession, InterviewQuestion,
)
from app.core.security import get_password_hash


# ---------------------------------------------------------------------------
# 1. SQLite UUID compatibility shim
# ---------------------------------------------------------------------------
from sqlalchemy.dialects.sqlite import base as _sqlite_base

def _visit_UUID(self, type_, **kw):          # noqa: N802
    return "VARCHAR(36)"

_sqlite_base.SQLiteTypeCompiler.visit_UUID = _visit_UUID   # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# 2. Session-scoped engine (created once)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def engine():
    """In-memory SQLite engine shared across all tests."""
    _engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=_engine)
    yield _engine
    Base.metadata.drop_all(bind=_engine)


# ---------------------------------------------------------------------------
# 3. Rate-limiter reset (autouse – runs before every test)
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Clear slowapi in-memory rate-limit counters before every test."""
    try:
        limiter = app.state.limiter
        storage = limiter._storage
        # Depending on slowapi/limits version the internal dict lives here:
        for attr in ("storage", "_storage", "STORAGE"):
            backend = getattr(storage, attr, None)
            if isinstance(backend, dict):
                backend.clear()
                break
    except Exception:
        pass  # best-effort; tests still run, some may see 429 if reset fails
    yield


# ---------------------------------------------------------------------------
# 4. Per-test DB cleanup and session
# ---------------------------------------------------------------------------

@pytest.fixture(scope="function")
def db_session(engine):
    """DB session; all tables are cleared before yielding."""
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=engine
    )
    session = TestingSessionLocal()

    # Clear all tables in reverse dependency order before each test
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM interview_questions"))
        conn.execute(text("DELETE FROM interview_sessions"))
        conn.execute(text("DELETE FROM subjects"))
        conn.execute(text("DELETE FROM academic_terms"))
        conn.execute(text("DELETE FROM student_profiles"))
        conn.execute(text("DELETE FROM users"))
        conn.commit()

    yield session

    session.rollback()
    session.close()


# ---------------------------------------------------------------------------
# 5. Test clients
# ---------------------------------------------------------------------------

@pytest.fixture(scope="function")
def client(db_session):
    """FastAPI test client with the DB dependency overridden."""
    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as tc:
        yield tc
    app.dependency_overrides.clear()


@pytest.fixture
def auth_client(client, sample_user):
    """Authenticated test client (TEST001 / Test@123)."""
    resp = client.post(
        "/api/auth/login",
        data={"username": "TEST001", "password": "Test@123"},
    )
    assert resp.status_code == 200, f"auth fixture login failed: {resp.json()}"
    token = resp.json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client


# ---------------------------------------------------------------------------
# 6. Data fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_user(db_session):
    user = User(
        student_id="TEST001",
        email="test@example.com",
        password_hash=get_password_hash("Test@123"),
        is_active=True,
        failed_login_attempts=0,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def sample_student_profile(db_session, sample_user):
    profile = StudentProfile(
        user_id=sample_user.id,
        name="Test Student",
        branch="CSE",
        semester=3,
        interests="Testing, Python, FastAPI",
    )
    db_session.add(profile)
    db_session.commit()
    db_session.refresh(profile)
    return profile


@pytest.fixture
def sample_academic_term(db_session, sample_user):
    term = AcademicTerm(
        user_id=sample_user.id,
        semester=1,
        year=2023,
        gpa=8.5,
    )
    db_session.add(term)
    db_session.commit()
    db_session.refresh(term)
    return term


@pytest.fixture
def sample_subject(db_session, sample_academic_term):
    subject = Subject(
        term_id=sample_academic_term.id,
        subject_name="Database Systems",
        subject_code="CS301",
        credits=4,
        marks=85.0,
        grade="A",
    )
    db_session.add(subject)
    db_session.commit()
    db_session.refresh(subject)
    return subject


@pytest.fixture
def sample_interview_session(db_session, sample_user):
    session = InterviewSession(
        user_id=sample_user.id,
        branch="CSE",
        topic="DSA",
        status="active",
    )
    db_session.add(session)
    db_session.flush()

    db_session.add_all([
        InterviewQuestion(
            session_id=session.id,
            topic="DSA",
            question="Explain BFS vs DFS.",
            difficulty="medium",
        ),
        InterviewQuestion(
            session_id=session.id,
            topic="DSA",
            question="What is dynamic programming?",
            difficulty="hard",
        ),
    ])
    db_session.commit()
    db_session.refresh(session)
    return session
