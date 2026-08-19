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
    User, StudentProfile,
    InterviewSession, InterviewQuestion,
)
from app.core.security import get_password_hash


# ---------------------------------------------------------------------------
# 2. Session-scoped engine (created once on PostgreSQL)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def engine():
    """PostgreSQL engine shared across all tests, migrated with Alembic."""
    import os
    from alembic.config import Config
    from alembic import command
    
    # We use a dedicated test database on the local PostgreSQL service
    default_url = "postgresql://studentadmin:studentpass123@localhost:5432/postgres"
    test_db_name = "student_tracker_test"
    test_url = f"postgresql://studentadmin:studentpass123@localhost:5432/{test_db_name}"
    
    # Ensure test database exists and is completely fresh
    tmp_engine = create_engine(default_url, isolation_level="AUTOCOMMIT")
    with tmp_engine.connect() as conn:
        # Terminate any stale connections to test DB to prevent lockouts
        conn.execute(text(
            f"SELECT pg_terminate_backend(pg_stat_activity.pid) "
            f"FROM pg_stat_activity "
            f"WHERE pg_stat_activity.datname = '{test_db_name}' AND pid <> pg_backend_pid()"
        ))
        conn.execute(text(f"DROP DATABASE IF EXISTS {test_db_name}"))
        conn.execute(text(f"CREATE DATABASE {test_db_name}"))
    tmp_engine.dispose()
    
    # Connect to the test database
    _engine = create_engine(test_url)
    
    # Overwrite settings and database module components dynamically
    from app.core.config import settings
    settings.DATABASE_URL = test_url
    
    import app.core.database
    app.core.database.engine = _engine
    app.core.database.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
    
    # Run Alembic migrations programmatically
    os.environ["DATABASE_URL"] = test_url
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")
    
    # Run programmatic check to verify model-to-migration consistency (catches schema drift)
    try:
        command.check(alembic_cfg)
    except Exception as e:
        import pytest
        pytest.fail(f"Alembic detected schema/migration drift! Run 'alembic revision --autogenerate' to align them. Error: {e}")
    
    yield _engine
    
    # Teardown: drop tables
    Base.metadata.drop_all(bind=_engine)


# ---------------------------------------------------------------------------
# 3. Rate-limiter reset (autouse – runs before every test)
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Disable rate limiting during tests."""
    app.state.limiter.enabled = False
    try:
        from app.api.routes.auth import limiter as auth_limiter
        auth_limiter.enabled = False
    except Exception:
        pass
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

    # Clear all tables in public schema except alembic_version using CASCADE truncate
    with engine.connect() as conn:
        res = conn.execute(text(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'public' AND table_name != 'alembic_version'"
        ))
        tables = [row[0] for row in res]
        if tables:
            tables_str = ", ".join(f'"{t}"' for t in tables)
            conn.execute(text(f"TRUNCATE TABLE {tables_str} CASCADE"))
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
    client.cookies.set("access_token", resp.cookies.get("access_token"))
    return client


# ---------------------------------------------------------------------------
# 6. Data fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_user(db_session):
    from app.models.user import UserRole
    user = User(
        student_id="TEST001",
        email="test@example.com",
        password_hash=get_password_hash("Test@123"),
        is_active=True,
        failed_login_attempts=0,
        role=UserRole.admin,
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
        department="CSE",
        semester=3,
        interests="Testing, Python, FastAPI",
    )
    db_session.add(profile)
    db_session.commit()
    db_session.refresh(profile)
    return profile



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
