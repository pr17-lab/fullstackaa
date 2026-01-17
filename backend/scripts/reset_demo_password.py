"""
Script to reset a demo student's password to a known value for testing.

Usage:
    python backend/scripts/reset_demo_password.py
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.core.security import get_password_hash
from app.models.user import User

def reset_password(student_id: str, new_password: str):
    """Reset a student's password."""
    
    # Create database session
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # Find user by student_id
        user = db.query(User).filter(User.student_id == student_id).first()
        
        if not user:
            print(f"❌ Error: Student ID '{student_id}' not found")
            return False
        
        # Hash the new password
        hashed_password = get_password_hash(new_password)
        
        # Update the user's password
        user.password_hash = hashed_password
        db.commit()
        
        print(f"✅ Password reset successful!")
        print(f"   Student ID: {student_id}")
        print(f"   Email: {user.email}")
        print(f"   New Password: {new_password}")
        print(f"\nYou can now login with:")
        print(f"   Username (Student ID): {student_id}")
        print(f"   Password: {new_password}")
        
        return True
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    # Reset password for student S01968
    student_id = "S01968"
    new_password = "demo123"
    
    print(f"Resetting password for student {student_id}...\n")
    reset_password(student_id, new_password)
