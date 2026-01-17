"""Quick test to check if S00001 user exists and password works."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import engine
from sqlalchemy import text
from app.core.security import verify_password

with engine.connect() as conn:
    result = conn.execute(
        text("SELECT student_id, email, password_hash FROM users WHERE student_id = 'S00001'")
    )
    user = result.fetchone()
    
    if user:
        sid, email, pwd_hash = user
        print(f"User found: {sid} ({email})")
        
        # Test password
        test_pwd = f"{sid}@123"
        if pwd_hash and verify_password(test_pwd, pwd_hash):
            print(f"SUCCESS: Password {test_pwd} works!")
        else:
            print(f"FAILED: Password {test_pwd} does not work")
            print(f"Hash: {pwd_hash[:60] if pwd_hash else 'NULL'}...")
    else:
        print("User S00001 NOT FOUND")
        # Show first user
        result = conn.execute(text( "SELECT student_id FROM users WHERE student_id IS NOT NULL LIMIT 1"))
        first = result.fetchone()
        print(f"First student_id in database: {first[0] if first else 'NONE'}")
