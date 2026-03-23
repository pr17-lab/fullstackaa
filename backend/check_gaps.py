import requests, json, os, sys
sys.path.append(os.getcwd())
from dotenv import load_dotenv
from app.core.config import settings
from app.core.security import create_access_token
from datetime import timedelta
import psycopg2

load_dotenv('.env')
conn = psycopg2.connect(settings.DATABASE_URL)
cur = conn.cursor()
cur.execute("SELECT id, email, student_id FROM users WHERE student_id = 'S00001' LIMIT 1")
user = cur.fetchone()
token = create_access_token({'sub': user[1], 'user_id': str(user[0]), 'student_id': user[2]}, timedelta(minutes=60))
r = requests.get('http://127.0.0.1:8000/api/skills/gaps', headers={'Authorization': f'Bearer {token}'})
data = r.json()
if data:
    first_gap = data[0]
    print('Gap keys:', list(first_gap.keys()))
    print('Job role:', first_gap.get('job_role'))
    if first_gap.get('missing_skills'):
        print('Sample missing_skill entry:')
        print(json.dumps(first_gap['missing_skills'][0], indent=2))
    else:
        print('No missing_skills!')
