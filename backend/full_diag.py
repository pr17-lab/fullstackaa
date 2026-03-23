import sys, os, requests, psycopg2

# 1. RAPIDAPI_KEY from settings
print("=== 1. RAPIDAPI_KEY from settings ===")
from app.core.config import settings
print("RAPIDAPI_KEY:", repr(settings.RAPIDAPI_KEY))

# 2. Test backend endpoint
print("\n=== 2. Test /api/jobs/listings/Software%20Engineer ===")
try:
    r = requests.get("http://127.0.0.1:8000/api/jobs/listings/Software%20Engineer", timeout=15)
    print("Status:", r.status_code)
    data = r.json()
    print("Source:", data.get("source"))
    print("Jobs Count:", len(data.get("jobs", [])))
    for j in data.get("jobs", [])[:3]:
        print(f"  - {j.get('job_title')} @ {j.get('employer_name')} ({j.get('job_city')}, {j.get('job_country')})")
except Exception as e:
    print("Error:", e)

# 3. job_cache table
print("\n=== 3. job_cache table ===")
try:
    conn = psycopg2.connect(settings.DATABASE_URL)
    cur = conn.cursor()
    cur.execute("SELECT query_key, job_title, source, job_count, fetched_at, expires_at FROM job_cache LIMIT 10")
    rows = cur.fetchall()
    if rows:
        for row in rows:
            print(row)
    else:
        print("(empty)")
    conn.close()
except Exception as e:
    print("DB Error:", e)

# 4. OpenAPI schema check
print("\n=== 4. OpenAPI schema - jobs routes ===")
try:
    r = requests.get("http://127.0.0.1:8000/openapi.json")
    paths = [p for p in r.json().get("paths", {}).keys() if "jobs" in p]
    if paths:
        for p in paths:
            print("FOUND:", p)
    else:
        print("No job routes found in schema!")
except Exception as e:
    print("Error:", e)

# 5. Router code
print("\n=== 5. Router /listings/{job_role} code ===")
with open("app/modules/jobs/router.py") as f:
    lines = f.readlines()
for i, line in enumerate(lines):
    if line.startswith('@router.get("/listings/'):
        print("".join(lines[i:i+30]))
        break
