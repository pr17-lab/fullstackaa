"""Check if username without numbers matches database emails."""
import csv
import sys
import re
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import engine
from sqlalchemy import text

csv_path = Path(__file__).parent.parent / "data" / "user_credentials_10k_common_password.csv"

def remove_trailing_numbers(username):
    """Remove trailing numbers from username."""
    return re.sub(r'\d+$', '', username)

with open(csv_path, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    rows = list(reader)
    
    # Test first 5 usernames
    print("Testing username to email mapping (removing numbers):\n")
    with engine.connect() as conn:
        for i, row in enumerate(rows[:5]):
            username = row.get('username', '')
            # Remove numbers and add @example.com
            username_no_nums = remove_trailing_numbers(username)
            email = f"{username_no_nums}@example.com"
            
            result = conn.execute(text("SELECT email FROM users WHERE email = :email"), {"email": email})
            match = result.fetchone()
            
            if match:
                print(f"✓ {username} → {email} FOUND")
            else:
                print(f"✗ {username} → {email} NOT FOUND")
        
        conn.close()
