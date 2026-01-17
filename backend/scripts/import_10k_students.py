#!/usr/bin/env python3
"""
Import 10,000 students from user_credentials CSV into PostgreSQL database.
This script imports from the actual 10K dataset file.
"""

import sys
from pathlib import Path

# Add parent directory to path to import app modules
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import bcrypt

from app.models import User, StudentProfile
from app.core.database import Base

# Database connection
DATABASE_URL = "postgresql://studentadmin:studentpass123@localhost:5432/student_tracker"

def get_db_session():
    """Create database session."""
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()

def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')

def import_10k_students(session, csv_path: str):
    """Import 10,000 students from user credentials CSV."""
    print(f"\n[*] Reading student data from {csv_path}...")
    df = pd.read_csv(csv_path)
    print(f"    Found {len(df)} student records in CSV")
    
    users_created = 0
    profiles_created = 0
    users_skipped = 0
    
    # Extract unique departments from student IDs (example mapping)
    departments = ['Computer Science', 'Electrical Engineering', 'Mechanical Engineering', 
                   'Civil Engineering', 'Electronics', 'Information Technology']
    
    for idx, row in df.iterrows():
        student_id = row['student_id']
        username = row['username']
        password_hash = row['password_hash']  # Use pre-hashed password from CSV
        
        # Create email from username
        email = f"{username}@student.edu"
        
        # Check if user already exists
        existing_user = session.query(User).filter(User.email == email).first()
        
        if existing_user:
            users_skipped += 1
            continue
        
        # Create User record with pre-hashed password from CSV
        user = User(
            email=email,
            password_hash=password_hash,  # Already hashed in CSV
            is_active=True
        )
        session.add(user)
        session.flush()  # Flush to get user.id
        users_created += 1
        
        # Generate student profile data
        # Extract name from username (capitalize first letter)
        name_parts = username.replace('.', ' ').split()
        name = ' '.join([part.capitalize() for part in name_parts])
        
        # Assign department based on student ID pattern
        dept_index = int(student_id[1:]) % len(departments)
        department = departments[dept_index]
        
        # Assign semester (1-8) based on student ID
        semester = (int(student_id[1:]) % 8) + 1
        
        # Create StudentProfile record
        profile = StudentProfile(
            user_id=user.id,
            name=name,
            branch=department,
            semester=semester,
            interests=None
        )
        session.add(profile)
        profiles_created += 1
        
        # Commit in batches of 1000 for performance
        if (idx + 1) % 1000 == 0:
            session.commit()
            print(f"    Progress: {idx + 1}/{len(df)} students imported...")
    
    # Final commit
    session.commit()
    
    print(f"\n[+] Student Import Complete:")
    print(f"    - Users created: {users_created}")
    print(f"    - Student profiles created: {profiles_created}")
    print(f"    - Users skipped (already exist): {users_skipped}")

def print_final_counts(session):
    """Print final counts of all records."""
    print("\n" + "="*80)
    print("FINAL DATABASE COUNTS")
    print("="*80)
    
    user_count = session.query(User).count()
    profile_count = session.query(StudentProfile).count()
    
    print(f"\n    Users: {user_count:,}")
    print(f"    Student Profiles: {profile_count:,}")
    print("\n" + "="*80)

def main():
    """Main import function."""
    print("="*80)
    print("IMPORTING 10,000 STUDENTS FROM CSV TO DATABASE")
    print("="*80)
    
    # Path to the 10K CSV file
    student_csv = backend_dir / "data" / "user_credentials_10k_common_password.csv"
    
    # Validate CSV file exists
    if not student_csv.exists():
        print(f"[!] Error: CSV file not found at {student_csv}")
        sys.exit(1)
    
    try:
        # Create database session
        session = get_db_session()
        
        # Import all 10,000 students
        import_10k_students(session, str(student_csv))
        
        # Print final counts
        print_final_counts(session)
        
        print("\n[+] Import completed successfully!")
        
        session.close()
        
    except Exception as e:
        print(f"\n[!] Error during import: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
