"""Check if priya.sharma@example.com exists and test authentication."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import engine
from sqlalchemy import text
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

with engine.connect() as conn:
    # Check if user exists
    result = conn.execute(text("SELECT email, password_hash FROM users WHERE email = 'priya.sharma@example.com'"))
    user = result.fetchone()
    
    if user:
        print(f"✓ User found: {user[0]}")
        print(f"  Password hash: {user[1][:50] if user[1] else 'NULL'}...")
        
        if user[1]:
            # Try common passwords
            test_passwords = ['student123', 'password123', 'test123', 'admin123']
            for pwd in test_passwords:
                try:
                    if pwd_context.verify(pwd, user[1]):
                        print(f"\n✓✓✓ MATCH FOUND: '{pwd}' works!")
                        break
                except Exception as e:
                    print(f"  Error testing '{pwd}': {e}")
            else:
                print("\n✗ None of the test passwords matched")
        else:
            print("\n✗ Password hash is NULL - user has no password set")
    else:
        print("✗ User not found")
    
    conn.close()
