"""
API Endpoint Validation Test Script
Tests all API endpoints against imported data
"""

import requests
import json
from typing import List, Dict

BASE_URL = "http://127.0.0.1:8000"

def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)

def test_endpoint(method: str, url: str, description: str, expected_status: int = 200, params: Dict = None):
    """Test a single endpoint and print results."""
    print(f"\n[TEST] {description}")
    print(f"       {method} {url}")
    
    try:
        if method == "GET":
            response = requests.get(url, params=params)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        print(f"       Status: {response.status_code} (Expected: {expected_status})")
        
        if response.status_code == expected_status:
            print("       ✓ PASS")
            data = response.json()
            print(f"       Response preview: {json.dumps(data, indent=2, default=str)[:500]}...")
            return True, data
        else:
            print("       ✗ FAIL")
            print(f"       Error: {response.text}")
            return False, None
            
    except Exception as e:
        print(f"       ✗ ERROR: {str(e)}")
        return False, None

def main():
    """Run all API endpoint tests."""
    print_section("API ENDPOINT VALIDATION TEST SUITE")
    
    results = {
        "passed": 0,
        "failed": 0,
        "total": 0
    }
    
    # First, get a student ID to use for testing
    print_section("SETUP: Getting Student IDs")
    success, students_data = test_endpoint(
        "GET",
        f"{BASE_URL}/api/students",
        "Fetch students list to get test ID",
        params={"page": 1, "page_size": 5}
    )
    
    if success and students_data and students_data.get('students'):
        student_id = students_data['students'][0]['id']
        student_name = students_data['students'][0]['name']
        print(f"\n       Using student: {student_name} (ID: {student_id})")
    else:
        print("\n       ERROR: Could not get student ID for testing")
        return
    
    # Test Suite
    tests = [
        # Student Endpoints
        {
            "section": "STUDENT ENDPOINTS",
            "tests": [
                ("GET", f"{BASE_URL}/api/students", "List all students (page 1)", 200, {"page": 1, "page_size": 10}),
                ("GET", f"{BASE_URL}/api/students", "List students with branch filter", 200, {"branch": "Mechanical"}),
                ("GET", f"{BASE_URL}/api/students", "List students with semester filter", 200, {"semester": 8}),
                ("GET", f"{BASE_URL}/api/students/{student_id}", f"Get student by ID: {student_id}", 200, None),
                ("GET", f"{BASE_URL}/api/students/00000000-0000-0000-0000-000000000000", "Get non-existent student (404 test)", 404, None),
                ("GET", f"{BASE_URL}/api/students/{student_id}/academic-records", "Get student academic records", 200, None),
            ]
        },
        # Analytics Endpoints
        {
            "section": "ANALYTICS ENDPOINTS",
            "tests": [
                ("GET", f"{BASE_URL}/api/analytics/gpa-trend", "GPA trend analysis", 200, {"student_id": student_id}),
                ("GET", f"{BASE_URL}/api/analytics/subject-performance", "Subject performance analysis", 200, {"student_id": student_id}),
                ("GET", f"{BASE_URL}/api/analytics/semester-comparison", "Semester comparison", 200, {"student_id": student_id}),
                ("GET", f"{BASE_URL}/api/analytics/student/{student_id}/summary", "Student analytics summary", 200, None),
                ("GET", f"{BASE_URL}/api/analytics/gpa-trend", "GPA trend - invalid student (404 test)", 404, {"student_id": "00000000-0000-0000-0000-000000000000"}),
            ]
        }
    ]
    
    # Run all tests
    for test_group in tests:
        print_section(test_group["section"])
        
        for test in test_group["tests"]:
            method, url, description, expected_status, params = test
            success, data = test_endpoint(method, url, description, expected_status, params)
            
            results["total"] += 1
            if success:
                results["passed"] += 1
            else:
                results["failed"] += 1
    
    # Summary
    print_section("TEST SUMMARY")
    print(f"\n  Total Tests: {results['total']}")
    print(f"  Passed: {results['passed']}")
    print(f"  Failed: {results['failed']}")
    print(f"  Success Rate: {(results['passed']/results['total']*100):.1f}%\n")
    
    if results['failed'] == 0:
        print("  ✓ ALL TESTS PASSED!")
    else:
        print(f"  ✗ {results['failed']} TEST(S) FAILED")
    
    print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    main()
