"""Set a known password for demo user to enable testing."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import engine
from sqlalchemy import text
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Hash a known password
demo_password = "password123"
hashed = pwd_context.hash(demo_password)

with engine.connect() as conn:
    # Update priya.sharma's password
    conn.execute(
        text("UPDATE users SET password_hash = :hash WHERE email = 'priya.sharma@example.com'"),
        {"hash": hashed}
    )
    conn.commit()
    
    print(f"✓ Updated password for priya.sharma@example.com")
    print(f"  Password: {demo_password}")
    print(f"  Hash: {hashed[:50]}...")
    
    conn.close()
