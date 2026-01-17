"""Test if S00005 student can be found by user_id"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import models - but don't use app.core.config
from app.models import User, StudentProfile

# Use database URL directly
DATABASE_URL = "postgresql://studentadmin:studentpass123@localhost:5432/student_tracker"

# Create database session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

try:
    # Find user with student_id S00005
    user = db.query(User).filter(User.student_id == 'S00005').first()
    
    if user:
        print(f"✓ Found user S00005:")
        print(f"  - User ID: {user.id}")
        print(f"  - Email: {user.email}")
        print(f"  - Student ID: {user.student_id}")
        print()
        
        # Try to find StudentProfile by user_id
        profile_by_user_id = db.query(StudentProfile).filter(StudentProfile.user_id == user.id).first()
        
        if profile_by_user_id:
            print(f"✓ Found StudentProfile by user_id:")
            print(f"  - Profile ID: {profile_by_user_id.id}")
            print(f"  - Name: {profile_by_user_id.name}")
            print(f"  - Branch: {profile_by_user_id.branch}")
            print(f"  - Semester: {profile_by_user_id.semester}")
        else:
            print(f"✗ NO StudentProfile found for user_id: {user.id}")
            print()
            print("Checking if ANY StudentProfile exists for this student...")
            all_profiles = db.query(StudentProfile).all()
            print(f"Total StudentProfiles in database: {len(all_profiles)}")
    else:
        print("✗ User with student_id S00005 not found!")
        
finally:
    db.close()
