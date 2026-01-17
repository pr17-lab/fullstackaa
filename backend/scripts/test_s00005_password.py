"""Test password for S00005"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import User
from app.core.security import verify_password

DATABASE_URL = "postgresql://studentadmin:studentpass123@localhost:5432/student_tracker"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

try:
    user = db.query(User).filter(User.student_id == 'S00005').first()
    
    if user:
        print(f"Found user: {user.student_id}")
        print(f"Email: {user.email}")
        print(f"Has password hash: {bool(user.password_hash)}")
        print()
        
        # Test password
        test_pwd = "S00005@123"
        is_valid = verify_password(test_pwd, user.password_hash)
        print(f"Testing password '{test_pwd}': {is_valid}")
        
        if not is_valid:
            print("\nPassword doesn't match! Let's check what the password should be...")
            # Check alternate formats
            for pwd in ["S00005@123", "default_password", "password123", user.student_id]:
                if verify_password(pwd, user.password_hash):
                    print(f"  ✓ Password is: {pwd}")
                    break
            else:
                print("  ✗ None of the common passwords work!")
    else:
        print("User not found!")
        
finally:
    db.close()
