"""Unit tests for database models."""
import pytest
from datetime import datetime, timedelta
from app.models import User, StudentProfile, AcademicTerm, Subject

def test_user_creation(db_session):
    """Test creating a user."""
    user = User(
        student_id="S00001",
        email="student@test.com",
        password_hash="hashed_password",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    
    assert user.id is not None
    assert user.student_id == "S00001"
    assert user.email == "student@test.com"
    assert user.is_active is True
    assert user.failed_login_attempts == 0
    assert user.locked_until is None

def test_student_profile_relationship(db_session, sample_user):
    """Test user-profile relationship."""
    profile = StudentProfile(
        user_id=sample_user.id,
        name="Test Student",
        branch="Computer Science",
        semester=1,
        interests="AI, ML"
    )
    db_session.add(profile)
    db_session.commit()
    
    # Refresh to load relationship
    db_session.refresh(sample_user)
    assert sample_user.profile.name == "Test Student"
    assert sample_user.profile.branch == "Computer Science"

def test_academic_term_unique_constraint(db_session, sample_user):
    """Test that duplicate semester/year combinations are prevented."""
    term1 = AcademicTerm(
        user_id=sample_user.id,
        semester=1,
        year=2023,
        gpa=8.5
    )
    db_session.add(term1)
    db_session.commit()
    
    # Try to create duplicate - should fail
    term2 = AcademicTerm(
        user_id=sample_user.id,
        semester=1,
        year=2023,
        gpa=9.0
    )
    db_session.add(term2)
    
    with pytest.raises(Exception):  # SQLAlchemy will raise IntegrityError
        db_session.commit()

def test_user_account_lockout(db_session, sample_user):
    """Test account lockout functionality."""
    # Initially not locked
    assert sample_user.is_locked() is False
    
    # Record 5 failed attempts
    for i in range(5):
        sample_user.record_failed_login()
    
    db_session.commit()
    db_session.refresh(sample_user)
    
    # Should be locked now
    assert sample_user.is_locked() is True
    assert sample_user.failed_login_attempts == 5
    assert sample_user.locked_until is not None
    assert sample_user.locked_until > datetime.utcnow()

def test_user_reset_failed_attempts(db_session, sample_user):
    """Test resetting failed login attempts."""
    # Record some failed attempts
    for i in range(3):
        sample_user.record_failed_login()
    
    db_session.commit()
    assert sample_user.failed_login_attempts == 3
    
    # Reset
    sample_user.reset_failed_attempts()
    db_session.commit()
    
    assert sample_user.failed_login_attempts == 0
    assert sample_user.locked_until is None

def test_subject_relationship(db_session, sample_academic_term, sample_subject):
    """Test subject-term relationship."""
    db_session.refresh(sample_academic_term)
    
    assert len(sample_academic_term.subjects) > 0
    assert sample_academic_term.subjects[0].subject_name == "Database Systems"
    assert sample_academic_term.subjects[0].grade == "A"
