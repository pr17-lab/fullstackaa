"""Test login API endpoint."""
import requests

# Test login
url = "http://localhost:8000/api/auth/login"
data = {
    "username": "S00001",
    "password": "S00001@123"
}

try:
    response = requests.post(url, data=data)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"SUCCESS! Got token:")
        print(f"  Access token (first 50 chars): {result['access_token'][:50]}...")
        print(f"  Token type: {result['token_type']}")
        
        # Test /me endpoint
        token = result['access_token']
        me_response = requests.get(
            "http://localhost:8000/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        if me_response.status_code == 200:
            user = me_response.json()
            print(f"\n/auth/me endpoint SUCCESS:")
            print(f"  User ID: {user.get('id')}")
            print(f"  Email: {user.get('email')}")
            print(f"  Student ID: {user.get('student_id')}")
        else:
            print(f"\n/auth/me FAILED: {me_response.status_code}")
            print(me_response.text)
    else:
        print(f"FAILED:")
        print(response.text)
        
except requests.exceptions.ConnectionError:
    print("ERROR: Cannot connect to http://localhost:8000")
    print("Backend server may not be running.")
    print("\nTo start the backend server, run:")
    print("  cd backend")
    print("  uvicorn app.main:app --reload")
