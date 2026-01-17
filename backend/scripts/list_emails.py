"""Simple check of user emails in database."""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    result = conn.execute(text("SELECT email FROM users ORDER BY email LIMIT 10"))
    print("First 10 user emails in database:")
    for row in result:
        print(f"  {row[0]}")
    conn.close()
