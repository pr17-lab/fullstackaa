"""Set proper bcrypt hash for demo user."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import engine
from sqlalchemy import text
import bcrypt

# Generate proper bcrypt hash for "password123"
password = "password123"
salt = bcrypt.gensalt()
hashed = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

print(f"Setting password for priya.sharma@example.com")
print(f"Password: {password}")
print(f"Hash: {hashed}")

with engine.connect() as conn:
    result = conn.execute(
        text("UPDATE users SET password_hash = :hash WHERE email = 'priya.sharma@example.com'"),
        {"hash": hashed}
    )
    conn.commit()
    
    print(f"\n✓ Updated {result.rowcount} user(s)")
    
    conn.close()
