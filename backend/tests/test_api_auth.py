"""Integration tests for authentication endpoints."""
import pytest
from app.core.security import get_password_hash

def test_login_success(client, sample_user):
    """Test successful login."""
    response = client.post(
        "/api/auth/login",
        data={
            "username": "TEST001",
            "password": "Test@123"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_invalid_credentials(client, sample_user):
    """Test login with invalid credentials."""
    response = client.post(
        "/api/auth/login",
        data={
            "username": "TEST001",
            "password": "WrongPassword"
        }
    )
    
    assert response.status_code == 401
    assert "Incorrect student ID or password" in response.json()["detail"]

def test_login_nonexistent_user(client):
    """Test login with non-existent user."""
    response = client.post(
        "/api/auth/login",
        data={
            "username": "NOTEXIST",
            "password": "AnyPassword"
        }
    )
    
    assert response.status_code == 401

def test_account_lockout_after_failed_attempts(client, sample_user, db_session):
    """Test account lockout after 5 failed login attempts."""
    # Make 5 failed login attempts
    for i in range(5):
        response = client.post(
            "/api/auth/login",
            data={
                "username": "TEST001",
                "password": "WrongPassword"
            }
        )
        assert response.status_code == 401
    
    # 6th attempt should be locked
    response = client.post(
        "/api/auth/login",
        data={
            "username": "TEST001",
            "password": "Test@123"  # Even correct password
        }
    )
    
    assert response.status_code == 403
    assert "locked" in response.json()["detail"].lower()

def test_get_current_user(client, sample_user, sample_student_profile):
    """Test getting current user details."""
    # First login
    login_response = client.post(
        "/api/auth/login",
        data={
            "username": "TEST001",
            "password": "Test@123"
        }
    )
    token = login_response.json()["access_token"]
    
    # Get current user
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["student_id"] == "TEST001"
    assert data["name"] == "Test Student"
    assert data["branch"] == "CSE"

def test_unauthorized_access(client):
    """Test accessing protected endpoint without token."""
    response = client.get("/api/auth/me")
    
    assert response.status_code == 401
