"""Test login with new random password from CSV."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import csv
from app.core.database import engine
from sqlalchemy import text
from app.core.security import verify_password

# Load first user from CSV
csv_path = Path(__file__).parent.parent / "student_passwords.csv"
with open(csv_path, 'r') as f:
    reader = csv.DictReader(f)
    test_user = next(reader)

print("=" * 80)
print("TESTING NEW PASSWORD")
print("=" * 80)

print(f"\nTest User:")
print(f"  Student ID: {test_user['student_id']}")
print(f"  Password: {test_user['password']}")
print(f"  Email: {test_user['email']}")

# Get user from database
with engine.connect() as conn:
    result = conn.execute(
        text("SELECT student_id, email, password_hash FROM users WHERE student_id = :sid"),
        {"sid": test_user['student_id']}
    )
    user = result.fetchone()
    
    if not user:
        print(f"\n[X] User {test_user['student_id']} not found in database!")
        sys.exit(1)
    
    print(f"\n[OK] User found in database")
    print(f"  Student ID: {user[0]}")
    print(f"  Email: {user[1]}")
    
    # Test password verification
    password_valid = verify_password(test_user['password'], user[2])
    
    if password_valid:
        print(f"\n[OK] Password verification SUCCESSFUL!")
        print(f"  Password '{test_user['password']}' is correct for {test_user['student_id']}")
    else:
        print(f"\n[X] Password verification FAILED!")
        print(f"  Password '{test_user['password']}' does not match hash in database")
        sys.exit(1)
    
    conn.close()

print("\n" + "=" * 80)
print("TEST PASSED - Random passwords are working correctly!")
print("=" * 80)
