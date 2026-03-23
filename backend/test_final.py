import requests
import sys

print("=== STEP 1: Import Check ===")
try:
    from app.main import app
    print("Import OK")
except Exception as e:
    print(f"Import Failed: {e}")
    sys.exit(1)

print("\n=== STEP 2: Login Test ===")
try:
    login_res = requests.post(
        "http://localhost:8000/api/auth/login",
        data={"username": "S00001", "password": "S00001@123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    print("Login Status:", login_res.status_code)
    token = login_res.json().get("access_token")
    if not token:
        print("Failed to get token!")
        print(login_res.text)
        sys.exit(1)
    print("Token retrieved successfully.")

    print("\n=== STEP 3: /api/auth/me Test ===")
    me_res = requests.get(
        "http://localhost:8000/api/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    print("Me Status:", me_res.status_code)
    print("Full JSON Response:")
    print(me_res.text)
except Exception as e:
    print(f"Request Error: {e}")
