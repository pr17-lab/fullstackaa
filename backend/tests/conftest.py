import pytest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.core.database import Base, get_db
from app.main import app
from app.models import User, StudentProfile, AcademicTerm, Subject
from app.core.security import get_password_hash

# Test database URL - use in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="session")
def engine():
    """Create test database engine."""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session(engine):
    """Create a new database session for a test."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    yield session
    session.rollback()
    session.close()

@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with overridden database dependency."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def sample_user(db_session):
    """Create a sample user for testing."""
    user = User(
        student_id="TEST001",
        email="test@example.com",
        password_hash=get_password_hash("Test@123"),
        is_active=True,
        failed_login_attempts=0
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def sample_student_profile(db_session, sample_user):
    """Create a sample student profile for testing."""
    profile = StudentProfile(
        user_id=sample_user.id,
        name="Test Student",
        branch="CSE",
        semester=3,
        interests="Testing, Python, FastAPI"
    )
    db_session.add(profile)
    db_session.commit()
    db_session.refresh(profile)
    return profile

@pytest.fixture
def sample_academic_term(db_session, sample_user):
    """Create a sample academic term for testing."""
    term = AcademicTerm(
        user_id=sample_user.id,
        semester=1,
        year=2023,
        gpa=8.5
    )
    db_session.add(term)
    db_session.commit()
    db_session.refresh(term)
    return term

@pytest.fixture
def sample_subject(db_session, sample_academic_term):
    """Create a sample subject for testing."""
    subject = Subject(
        term_id=sample_academic_term.id,
        subject_name="Database Systems",
        subject_code="CS301",
        credits=4,
        marks=85.0,
        grade="A"
    )
    db_session.add(subject)
    db_session.commit()
    db_session.refresh(subject)
    return subject
