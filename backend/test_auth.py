import urllib.request
import json
import os

try:
    # Login data (assumes a user exists in DB from test seed data)
    # Using the standard seed user from SATA test DB
    login_data = b'username=kiran.iyer001&password=student123'
    req1 = urllib.request.Request('http://localhost:8000/api/auth/login', data=login_data)
    req1.add_header('Content-Type', 'application/x-www-form-urlencoded')
    
    with urllib.request.urlopen(req1) as r1:
        token = json.loads(r1.read().decode())['access_token']
        print('Got auth token.')

    # Create Session Request
    jd_payload = json.dumps({'jd_text': 'React Developer typescript css', 'limit': 3}).encode('utf-8')
    req2 = urllib.request.Request('http://localhost:8000/api/interview/sessions', data=jd_payload)
    req2.add_header('Content-Type', 'application/json')
    req2.add_header('Authorization', f'Bearer {token}')
    
    with urllib.request.urlopen(req2) as r2:
        res = json.loads(r2.read().decode())
        print(f"Total Questions: {len(res.get('questions', []))}")
        for q in res.get('questions', []):
            print(f"[{q.get('source')}] {q.get('question')}")

except urllib.error.HTTPError as e:
    print('HTTPError:', e.code, e.read().decode())
except Exception as e:
    print('Exception:', e)
