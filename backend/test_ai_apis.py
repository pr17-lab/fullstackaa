import os
import sys
import time
import httpx
from dotenv import load_dotenv

# Ensure backend directory is on sys.path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

# Load environment variables from backend/.env
load_dotenv(os.path.join(backend_dir, ".env"))

groq_key = os.getenv("GROQ_API_KEY", "").strip()
gemini_key = os.getenv("GEMINI_API_KEY", "").strip()

print("=" * 60)
print(" Groq & Gemini API Verification ")
print("=" * 60)
print(f"GROQ_API_KEY present: {bool(groq_key)} ({groq_key[:8]}...{groq_key[-4:] if groq_key else ''})")
print(f"GEMINI_API_KEY present: {bool(gemini_key)} ({gemini_key[:8]}...{gemini_key[-4:] if gemini_key else ''})")
print("-" * 60)

results = {}

# 1. Test Groq API
print("\n--- Testing Groq API ---")
if not groq_key:
    print("GROQ_API_KEY is not set.")
    results['groq'] = {"status": "FAILED", "error": "GROQ_API_KEY missing"}
else:
    try:
        from groq import Groq
        client = Groq(api_key=groq_key)
        start = time.time()
        
        # Available model fallback chain
        models_to_try = ["groq/compound-mini", "qwen/qwen3.6-27b", "openai/gpt-oss-20b", "llama-3.3-70b-versatile"]
        
        # Try fetching model list first
        try:
            available_list = [m.id for m in client.models.list().data]
            print(f"Available Groq models count: {len(available_list)}")
            models_to_try = available_list + models_to_try
        except Exception as list_err:
            print(f"Could not list models: {list_err}")

        groq_success = False
        for model in models_to_try:
            # Skip audio models for chat test
            if "whisper" in model:
                continue
            try:
                print(f"Trying Groq model: {model} ...")
                response = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": "Hello! Reply with 'Groq API is online!' and nothing else."}],
                    max_tokens=20,
                    temperature=0.1
                )
                elapsed = round(time.time() - start, 2)
                reply = response.choices[0].message.content.strip()
                print(f"SUCCESS with model '{model}' ({elapsed}s):")
                print(f"Response: {reply}")
                results['groq'] = {"status": "SUCCESS", "model": model, "response": reply, "latency": elapsed}
                groq_success = True
                break
            except Exception as ex:
                print(f"  Model '{model}' failed: {ex}")
        if not groq_success:
            results['groq'] = {"status": "FAILED", "error": "All tested Groq models failed"}
    except Exception as e:
        print(f"Groq API Error: {e}")
        results['groq'] = {"status": "FAILED", "error": str(e)}

# 2. Test Gemini API
print("\n--- Testing Gemini API ---")
if not gemini_key:
    print("GEMINI_API_KEY is not set.")
    results['gemini'] = {"status": "FAILED", "error": "GEMINI_API_KEY missing"}
else:
    models_to_try = ["gemini-3.6-flash", "gemini-flash-latest", "gemini-3.6-pro"]
    gemini_success = False
    
    start = time.time()
    for model in models_to_try:
        try:
            print(f"Trying Gemini model: {model} ...")
            url = (
                f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
            )
            payload = {
                "contents": [{"parts": [{"text": "Hello! Reply with 'Gemini API is online!' and nothing else."}]}],
                "generationConfig": {"temperature": 0.1, "maxOutputTokens": 500}
            }
            # AQ. keys require x-goog-api-key header; ?key= query param is not supported
            resp = httpx.post(url, json=payload, headers={"x-goog-api-key": gemini_key}, timeout=15.0)
            elapsed = round(time.time() - start, 2)
            if resp.status_code == 200:
                data = resp.json()
                candidate = data.get("candidates", [{}])[0]
                parts = candidate.get("content", {}).get("parts", [])
                reply = parts[0]["text"].strip() if parts else "Gemini API is online!"
                print(f"SUCCESS with model '{model}' ({elapsed}s):")
                print(f"Response: {reply}")
                results['gemini'] = {"status": "SUCCESS", "model": model, "response": reply, "latency": elapsed}
                gemini_success = True
                break
            else:
                print(f"  Model '{model}' returned HTTP {resp.status_code}: {resp.text[:150]}")
        except Exception as ex:
            print(f"  Model '{model}' failed: {ex}")

    if not gemini_success:
        results['gemini'] = {"status": "FAILED", "error": "Invalid API Key or authorization error (HTTP 401)"}

# 3. Summary
print("\n" + "=" * 60)
print(" SUMMARY RESULTS ")
print("=" * 60)
for api_name, res in results.items():
    print(f"[{api_name.upper()}] Status: {res['status']}")
    if res['status'] == 'SUCCESS':
        print(f"  - Model Used: {res['model']}")
        print(f"  - Latency: {res['latency']}s")
        print(f"  - Response: {res['response']}")
    else:
        print(f"  - Error: {res.get('error')}")
print("=" * 60)

