import asyncio
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal
from app.models.user import User

client = TestClient(app)

def test_create_session():
    db = SessionLocal()
    user = db.query(User).filter(User.username == "kiran.iyer001").first()
    db.close()
    
    if not user:
        print("User not found")
        return
        
    print(f"Testing with user: {user.username}")
    
    # We need to bypass JWT auth for test, or mint a token.
    # We can just mint a token using our own auth service.
    from app.services.auth import create_access_token
    token = create_access_token({"sub": user.id})
    
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "jd_text": "React Developer typescript css",
        "resume_context": "",
        "limit": 3
    }
    
    response = client.post("/api/interview/sessions", json=payload, headers=headers)
    
    print("Status:", response.status_code)
    try:
        data = response.json()
        print("Response JSON Keys:", data.keys())
        questions = data.get("questions", [])
        for i, q in enumerate(questions):
            print(f"[{q.get('source')}] {q.get('question')}")
    except Exception as e:
        print("Raw response text:", response.text)

if __name__ == "__main__":
    test_create_session()
