import requests
import json

print("=== STEP 1: Health Check ===")
try:
    r = requests.get("http://localhost:8000/api/health")
    print("Status:", r.status_code)
    print("Headers:", dict(r.headers))
    print("Body:", r.text)
except Exception as e:
    print("Error:", e)

print("\n=== STEP 2: Login Test ===")
try:
    r = requests.post(
        "http://localhost:8000/api/auth/login",
        data={"username": "S00001", "password": "S00001@123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    print("Status:", r.status_code)
    print("Headers:", dict(r.headers))
    print("Body:", r.text)
except Exception as e:
    print("Error:", e)
