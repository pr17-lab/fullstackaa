"""
Test script to verify CSV data integration.
Run this after starting the FastAPI server.
"""
import requests
import json

BASE_URL = "http://localhost:8000/api"

def test_csv_health():
    """Test if CSV data is loaded."""
    print("Testing CSV data health...")
    response = requests.get(f"{BASE_URL}/health/csv-data")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()

def test_get_student():
    """Test getting a specific student."""
    print("Testing get student by ID...")
    student_id = "STU001"
    response = requests.get(f"{BASE_URL}/students/{student_id}")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    else:
        print(f"Error: {response.text}")
    print()

def test_get_records():
    """Test getting student academic records."""
    print("Testing get student records...")
    student_id = "STU001"
    response = requests.get(f"{BASE_URL}/students/{student_id}/records")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Number of records: {len(data)}")
        print(f"First record: {json.dumps(data[0] if data else {}, indent=2)}")
    else:
        print(f"Error: {response.text}")
    print()

def test_gpa_trend():
    """Test getting GPA trend."""
    print("Testing GPA trend...")
    student_id = "STU001"
    response = requests.get(f"{BASE_URL}/analytics/gpa-trend/{student_id}")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    else:
        print(f"Error: {response.text}")
    print()

def test_search_students():
    """Test searching students."""
    print("Testing search students...")
    response = requests.get(f"{BASE_URL}/students", params={
        "department": "Computer Science",
        "limit": 5
    })
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Number of results: {len(data)}")
        if data:
            print(f"First result: {json.dumps(data[0], indent=2)}")
    else:
        print(f"Error: {response.text}")
    print()

if __name__ == "__main__":
    print("=" * 50)
    print("CSV Data Integration Test Suite")
    print("=" * 50)
    print()
    
    try:
        test_csv_health()
        test_get_student()
        test_get_records()
        test_gpa_trend()
        test_search_students()
        
        print("=" * 50)
        print("All tests completed!")
        print("=" * 50)
    except requests.exceptions.ConnectionError:
        print("ERROR: Could not connect to server.")
        print("Please make sure the FastAPI server is running on http://localhost:8000")
    except Exception as e:
        print(f"ERROR: {str(e)}")
