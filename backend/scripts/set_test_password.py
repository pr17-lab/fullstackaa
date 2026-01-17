#!/usr/bin/env python3
"""
Simple script to set password for a single test user to verify it works.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import bcrypt
from sqlalchemy import create_engine, text
from app.core.config import settings
from app.core.security import get_password_hash

def set_test_password():
    """Set password for S00001 user."""
    
    student_id = "S00001"
    password = f"{student_id}@123"
    
    print(f"\n[*] Setting password for student_id: {student_id}")
    print(f"[*] Password: {password}")
    
    # Hash the password using the same function as the app
    password_hash = get_password_hash(password)
    print(f"[*] Generated hash: {password_hash[:60]}...")
    print(f"[*] Hash format: {password_hash[:4]}")
    
    # Update database
    engine = create_engine(settings.DATABASE_URL)
    conn = engine.connect()
    
    try:
        # Update the user
        result = conn.execute(
            text("UPDATE users SET password_hash = :hash WHERE student_id = :sid"),
            {"hash": password_hash, "sid": student_id}
        )
        conn.commit()
        
        print(f"[*] Rows updated: {result.rowcount}")
        
        # Verify
        verify_result = conn.execute(
            text("SELECT student_id, password_hash FROM users WHERE student_id = :sid"),
            {"sid": student_id}
        )
        user = verify_result.fetchone()
        
        if user:
            print(f"\n✅ Verification:")
            print(f"   Student ID: {user[0]}")
            print(f"   Hash: {user[1][:60]}...")
            print(f"   Hash starts with $2b$: {user[1].startswith('$2b$')}")
        
    finally:
        conn.close()

if __name__ == "__main__":
    set_test_password()
