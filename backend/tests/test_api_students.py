"""Integration tests for student endpoints."""
import pytest

def test_list_students_pagination(client, sample_student_profile):
    """Test student list endpoint with pagination."""
    response = client.get("/api/students?page=1&page_size=10")
    
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "page" in data
    assert "page_size" in data
    assert "students" in data
    assert data["page"] == 1
    assert data["page_size"] == 10

def test_list_students_filter_by_branch(client, sample_student_profile):
    """Test filtering students by branch."""
    response = client.get("/api/students?branch=CSE")
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] > 0
    for student in data["students"]:
        assert student["branch"] == "CSE"

def test_list_students_filter_by_semester(client, sample_student_profile):
    """Test filtering students by semester."""
    response = client.get("/api/students?semester=3")
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] > 0
    for student in data["students"]:
        assert student["semester"] == 3

def test_search_students_by_name(client, sample_student_profile):
    """Test searching students by name."""
    response = client.get("/api/students/search?q=Test&page=1&page_size=10")
    
    assert response.status_code == 200
    data = response.json()
    assert "students" in data
    # Should find our test student
    assert data["total"] > 0

def test_search_students_by_student_id(client, sample_student_profile):
    """Test searching students by student ID."""
    response = client.get("/api/students/search?q=TEST001")
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] > 0

def test_get_student_by_id(client, sample_student_profile):
    """Test getting a single student by ID."""
    response = client.get(f"/api/students/{sample_student_profile.user_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Student"
    assert data["branch"] == "CSE"

def test_get_nonexistent_student(client):
    """Test getting a non-existent student."""
    import uuid
    fake_id = str(uuid.uuid4())
    response = client.get(f"/api/students/{fake_id}")
    
    assert response.status_code == 404

def test_search_minimum_query_length(client):
    """Test that search requires minimum query length."""
    response = client.get("/api/students/search?q=a")
    
    assert response.status_code == 422  # Validation error
