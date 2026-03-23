import os
import requests
import psycopg2
import json
from dotenv import load_dotenv

print('=== 1. Check RAPIDAPI_KEY ===')
from app.core.config import settings
print('RAPIDAPI_KEY:', repr(settings.RAPIDAPI_KEY))

print('\n=== 2. Test Endpoint (No Auth Needed for this route) ===')
try:
    r = requests.get('http://127.0.0.1:8000/api/jobs/listings/Software%20Engineer', timeout=15)
    print('Status:', r.status_code)
    try:
        data = r.json()
        print('Response Source:', data.get('source'))
        print('Jobs Count:', len(data.get('jobs', [])))
        if data.get('jobs'):
            print('First Job:', data['jobs'][0].get('job_title'), '-', data['jobs'][0].get('employer_name'))
    except:
        print('Raw Response:', r.text[:500])
except Exception as e:
    print('Endpoint Test Failed:', e)

print('\n=== 3. Check job_cache table ===')
try:
    load_dotenv('.env')
    conn = psycopg2.connect(settings.DATABASE_URL)
    cur = conn.cursor()
    cur.execute('SELECT query_key, job_title, source, job_count, fetched_at, expires_at FROM job_cache LIMIT 10')
    rows = cur.fetchall()
    if rows:
        for row in rows:
            print(row)
    else:
        print('(Table is empty)')
except Exception as e:
    print('DB Error:', e)

print('\n=== 4. Check OpenAPI Schema ===')
try:
    r = requests.get('http://127.0.0.1:8000/openapi.json')
    if '/api/jobs/listings/{job_role_encoded}' in r.json().get('paths', {}):
        print('Route /api/jobs/listings/{job_role_encoded} EXISTS in OpenAPI schemas.')
    else:
        paths = [p for p in r.json().get('paths', {}).keys() if 'jobs' in p]
        print('Route missing. Found job routes:', paths)
except Exception as e:
    print('OpenAPI check failed:', e)

print('\n=== 5. Router Code ===')
try:
    with open('app/modules/jobs/router.py', 'r') as f:
        lines = f.readlines()
        start = -1
        for i, line in enumerate(lines):
            if line.startswith('@router.get("/listings/'):
                start = i
                break
        if start != -1:
            print(''.join(lines[start:start+25]))
        else:
            print('Could not find router definition')
except Exception as e:
    print('Error reading router file:', e)
