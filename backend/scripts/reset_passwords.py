"""Clear all password hashes and set demo user password."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import engine
from sqlalchemy import text
import bcrypt

# Generate proper bcrypt hash
password = "password123"
salt = bcrypt.gensalt()
hashed = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

print(f"Generated hash: {hashed}")

with engine.connect() as conn:
    # Clear all password hashes first
    conn.execute(text("UPDATE users SET password_hash = NULL"))
    conn.commit()
    print("Cleared all password hashes")
    
    # Set demo user password
    conn.execute(
        text("UPDATE users SET password_hash = :hash WHERE email = 'priya.sharma@example.com'"),
        {"hash": hashed}
    )
    conn.commit()
    
    print(f"✓ Set password for priya.sharma@example.com = '{password}'")
    
    conn.close()
