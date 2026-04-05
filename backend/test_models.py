import httpx
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

models = [
    "gemini-1.5-flash",
    "gemini-1.5-flash-latest",
    "gemini-1.0-pro",
    "gemini-pro"
]

for m in models:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": "Hello"}]}],
        "generationConfig": {"temperature": 0.3, "response_mime_type": "application/json"}
    }
    try:
        resp = httpx.post(url, json=payload, timeout=5.0)
        print(f"{m} -> {resp.status_code} {resp.text[:100]}")
    except Exception as e:
        print(f"{m} -> ERROR {e}")
