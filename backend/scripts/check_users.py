"""Check if usernames in CSV match emails in database."""
import csv
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import engine
from sqlalchemy import text

csv_path = Path(__file__).parent.parent / "data" / "user_credentials_10k_common_password.csv"

# Get first username from CSV
with open(csv_path, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    first_row = next(reader)
    print(f"First CSV row:")
    print(f"  student_id: {first_row.get('student_id')}")
    print(f"  username: {first_row.get('username')}")
    print(f"  password: {first_row.get('password')[:10]}...")
    
    # Check if username exists as email
    username = first_row.get('username')
    email_from_username = f"{username}@example.com"  # Try adding @example.com
    
# Check both in database
with engine.connect() as conn:
    # Check direct username
    result = conn.execute(text("SELECT email FROM users WHERE email = :email"), {"email": username})
    match1 = result.fetchone()
    if match1:
        print(f"\nDirect username match: {match1[0]}")
    else:
        print(f"\nDirect username match: Not found")
    
    # Check with @example.com
    result = conn.execute(text("SELECT email FROM users WHERE email = :email"), {"email": email_from_username})
    match2 = result.fetchone()
    if match2:
        print(f"Username@example.com match: {match2[0]}")
    else:
        print(f"Username@example.com match: Not found")
    
    # Check if users table has username column  
    result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'users'"))
    print(f"\nUsers table columns:")
    for row in result:
        print(f"  - {row[0]}")
