import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import engine
from sqlalchemy import text

conn = engine.connect()

# Check a specific user
result = conn.execute(text("SELECT student_id, email, password_hash FROM users WHERE student_id = 'S00001' LIMIT 1"))
user = result.fetchone()

if user:
    print(f"Student ID: {user[0]}")
    print(f"Email: {user[1]}")
    print(f"Password hash: {user[2][:60]}...")
    print(f"Hash starts with $2b$: {user[2].startswith('$2b$')}")
    print(f"Hash length: {len(user[2])}")
else:
    print("User S00001 not found")

conn.close()
