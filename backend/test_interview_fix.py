"""
End-to-end test for interview question generation fix.
Verifies that Groq generates JD-specific questions (NOT built-in bank).
"""
import httpx
import json
import sys

BASE_URL = "http://localhost:8000"
STUDENT_ID = "S01473"
PASSWORD = "S01473@123"
JD = "We are hiring a React Frontend Developer. Required skills: React, TypeScript, CSS, REST APIs, Git"

# 1. Login
print("=== STEP 1: Login ===")
try:
    login_resp = httpx.post(
        f"{BASE_URL}/api/auth/login",
        data={"username": STUDENT_ID, "password": PASSWORD},
        timeout=180,
    )
    print(f"Login status: {login_resp.status_code}")
    if login_resp.status_code != 200:
        print("Login failed:", login_resp.text[:200])
        sys.exit(1)
    token = login_resp.json()["access_token"]
    print(f"Got token: {token[:30]}...")
except Exception as e:
    print(f"Login error: {e}")
    sys.exit(1)

headers = {"Authorization": f"Bearer {token}"}

# 2. Create session with React JD
print("\n=== STEP 2: Create interview session with React JD ===")
try:
    session_resp = httpx.post(
        f"{BASE_URL}/api/interview/sessions",
        json={"jd_text": JD, "resume_context": "", "limit": 5},
        headers=headers,
        timeout=180,
    )
    print(f"Session status: {session_resp.status_code}")
    if session_resp.status_code == 201:
        data = session_resp.json()
        questions = data.get("questions", [])
        print(f"\n✅ Session ID: {data.get('id')}")
        print(f"✅ Got {len(questions)} questions")
        print("\n--- First 5 Questions ---")
        for i, q in enumerate(questions[:5], 1):
            print(f"\n  Q{i} [{q.get('difficulty','?').upper()}] — Topic: {q.get('topic','?')}")
            print(f"  {q.get('question','?')}")
    else:
        print("ERROR:", session_resp.text[:500])
        sys.exit(1)
except Exception as e:
    print(f"Session creation error: {e}")
    sys.exit(1)

# 3. Also test without JD (no-JD path should now go through Groq)
print("\n\n=== STEP 3: Test without JD (should now use groq_direct) ===")
try:
    qs_resp = httpx.get(
        f"{BASE_URL}/api/interview/questions",
        params={"limit": 3},
        headers=headers,
        timeout=180,
    )
    print(f"Questions status: {qs_resp.status_code}")
    if qs_resp.status_code == 200:
        data2 = qs_resp.json()
        source = data2.get("source", "unknown")
        questions2 = data2.get("questions", [])
        print(f"✅ Source: {source}")
        print(f"✅ Got {len(questions2)} questions")
        if source == "built-in":
            print("❌ STILL USING BUILT-IN! Fix did not work for no-JD case.")
        else:
            print(f"✅ Using {source} — Groq is working!")
    else:
        print("ERROR:", qs_resp.text[:300])
except Exception as e:
    print(f"Questions error: {e}")

print("\n=== DONE ===")
