"""Test the actual API endpoint for student lookup"""
import requests

# Test getting student by user_id (S00005's user.id)
user_id = "eed6e249-bb0e-4ebc-a39b-cda12b70ae77"

print("Testing /api/students/{user_id} endpoint...")
print(f"User ID: {user_id}")
print()

response = requests.get(f"http://localhost:8000/api/students/{user_id}")
print(f"Status Code: {response.status_code}")
print(f"Response: {response.json()}")
print()

if response.status_code == 200:
    print("✓ API lookup by user_id works!")
else:
    print("✗ API lookup failed!")
    
# Test academic records
print("\nTesting /api/students/{user_id}/academic-records endpoint...")
response2 = requests.get(f"http://localhost:8000/api/students/{user_id}/academic-records")
print(f"Status Code: {response2.status_code}")

if response2.status_code == 200:
    data = response2.json()
    print(f"✓ Found academic records!")
    print(f"  - Terms: {data.get('total_terms')}")
    print(f"  - GPA: {data.get('overall_gpa')}")
    print(f"  - Credits: {data.get('total_credits')}")
else:
    print(f"✗ Failed: {response2.json()}")
