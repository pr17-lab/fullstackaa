#!/usr/bin/env python3
"""
One-time CSV import script to load student data into PostgreSQL database.
Imports user profiles and academic records from CSV files.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path to import app modules
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import bcrypt

from app.models import User, StudentProfile, AcademicTerm, Subject
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
    # Hash the password with bcrypt
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')

def import_students(session, csv_path: str):
    """Import students from CSV into User and StudentProfile tables."""
    print(f"\n[*] Reading student data from {csv_path}...")
    df = pd.read_csv(csv_path)
    print(f"    Found {len(df)} student records in CSV")
    
    users_created = 0
    profiles_created = 0
    users_skipped = 0
    
    # Create mapping from student_id to email for later use
    student_id_to_email = {}
    
    for idx, row in df.iterrows():
        email = row['email']
        student_id = row['student_id']
        
        # Store mapping for academic records import
        student_id_to_email[student_id] = email
        
        # Check if user already exists
        existing_user = session.query(User).filter(User.email == email).first()
        
        if existing_user:
            users_skipped += 1
            continue
        
        # Create User record
        user = User(
            email=email,
            password_hash=hash_password("student123"),  # Default password
            is_active=row['status'].lower() == 'active' if pd.notna(row['status']) else True
        )
        session.add(user)
        session.flush()  # Flush to get user.id
        users_created += 1
        
        # Create StudentProfile record
        profile = StudentProfile(
            user_id=user.id,
            name=row['name'],
            branch=row['department'],
            semester=int(row['current_semester']),
            interests=None  # interests column not in CSV
        )
        session.add(profile)
        profiles_created += 1
    
    session.commit()
    
    print(f"\n[+] Student Import Complete:")
    print(f"    - Users created: {users_created}")
    print(f"    - Student profiles created: {profiles_created}")
    print(f"    - Users skipped (already exist): {users_skipped}")
    
    return student_id_to_email

def import_academic_records(session, csv_path: str, student_id_to_email: dict):
    """Import academic records from CSV into AcademicTerm and Subject tables."""
    print(f"\n[*] Reading academic records from {csv_path}...")
    df = pd.read_csv(csv_path)
    print(f"    Found {len(df)} academic record entries in CSV")
    
    terms_created = 0
    subjects_created = 0
    terms_skipped = 0
    
    # Group by student_id and semester to create academic terms
    grouped = df.groupby(['student_id', 'semester'])
    
    for (student_id, semester), group in grouped:
        # Find the user by email using our mapping
        email = student_id_to_email.get(student_id)
        if not email:
            print(f"    [!] Warning: Student ID {student_id} not found in student data, skipping...")
            continue
        
        user = session.query(User).filter(User.email == email).first()
        if not user:
            print(f"    [!] Warning: User with email {email} not found, skipping...")
            continue
        
        # Calculate GPA from marks (since gpa column doesn't exist in academic records CSV)
        # Average marks / 10 to get approximate GPA (scaled from 0-100 to 0-10)
        # Cap at 9.99 to fit Numeric(3,2) database constraint
        total_marks = group['Total_marks'].mean()
        gpa = min(round(total_marks / 10, 2), 9.99)  # Convert to 10-point scale, cap at 9.99
        
        # Get year from student main info
        # We need to infer year from the data. Let's use current year as default
        year = 2024  # Default year, could be enhanced with actual data
        
        # Convert semester to int to avoid binding issues
        semester_int = int(semester)
        year_int = int(year)
        
        # Check if academic term already exists
        existing_term = session.query(AcademicTerm).filter(
            AcademicTerm.user_id == user.id
        ).filter(
            AcademicTerm.semester == semester_int
        ).filter(
            AcademicTerm.year == year_int
        ).first()
        
        if existing_term:
            terms_skipped += 1
            term = existing_term
        else:
            # Create AcademicTerm record
            term = AcademicTerm(
                user_id=user.id,
                semester=semester_int,
                year=year_int,
                gpa=float(gpa)
            )
            session.add(term)
            session.flush()  # Flush to get term.id
            terms_created += 1
        
        # Create Subject records for this term
        for _, subject_row in group.iterrows():
            # Check if subject already exists (by subject_code in the term)
            existing_subject = session.query(Subject).filter(
                Subject.term_id == term.id
            ).filter(
                Subject.subject_code == subject_row['subject_code']
            ).first()
            
            if not existing_subject:
                # Map pass_fail to 2-character grade code
                grade_map = {
                    'Pass': 'P',
                    'Fail': 'F'
                }
                grade = grade_map.get(subject_row['pass_fail'], 'P')  # Default to 'P' if unknown
                
                subject = Subject(
                    term_id=term.id,
                    subject_name=subject_row['subject_name'],
                    subject_code=subject_row['subject_code'],
                    credits=int(subject_row['credits']),
                    marks=float(subject_row['Total_marks']),
                    grade=grade
                )
                session.add(subject)
                subjects_created += 1
    
    session.commit()
    
    print(f"\n[+] Academic Records Import Complete:")
    print(f"    - Academic terms created: {terms_created}")
    print(f"    - Subjects created: {subjects_created}")
    print(f"    - Academic terms skipped (already exist): {terms_skipped}")

def print_sample_data(session):
    """Print sample rows from each table for verification."""
    print("\n" + "="*80)
    print("SAMPLE DATA VERIFICATION")
    print("="*80)
    
    # Sample users
    print("\n[USERS] Sample 3 rows:")
    users = session.query(User).limit(3).all()
    for user in users:
        print(f"    Email: {user.email}, Active: {user.is_active}, Created: {user.created_at}")
    
    # Sample student profiles
    print("\n[STUDENT PROFILES] Sample 3 rows:")
    profiles = session.query(StudentProfile).limit(3).all()
    for profile in profiles:
        print(f"    Name: {profile.name}, Branch: {profile.branch}, Semester: {profile.semester}")
    
    # Sample academic terms
    print("\n[ACADEMIC TERMS] Sample 3 rows:")
    terms = session.query(AcademicTerm).limit(3).all()
    for term in terms:
        print(f"    Semester: {term.semester}, Year: {term.year}, GPA: {term.gpa}")
    
    # Sample subjects
    print("\n[SUBJECTS] Sample 3 rows:")
    subjects = session.query(Subject).limit(3).all()
    for subject in subjects:
        print(f"    Code: {subject.subject_code}, Name: {subject.subject_name}, Marks: {subject.marks}, Grade: {subject.grade}")

def print_final_counts(session):
    """Print final counts of all records."""
    print("\n" + "="*80)
    print("FINAL DATABASE COUNTS")
    print("="*80)
    
    user_count = session.query(User).count()
    profile_count = session.query(StudentProfile).count()
    term_count = session.query(AcademicTerm).count()
    subject_count = session.query(Subject).count()
    
    print(f"\n    Users: {user_count}")
    print(f"    Student Profiles: {profile_count}")
    print(f"    Academic Terms: {term_count}")
    print(f"    Subjects: {subject_count}")
    print("\n" + "="*80)

def main():
    """Main import function."""
    print("="*80)
    print("STARTING CSV IMPORT TO DATABASE")
    print("="*80)
    
    # Paths to CSV files
    student_csv = backend_dir / "data" / "SATA_student_main_info_10k.csv"
    academic_csv = backend_dir / "data" / "SATA_academic_records_10k.csv"
    
    # Validate CSV files exist
    if not student_csv.exists():
        print(f"[!] Error: Student CSV file not found at {student_csv}")
        sys.exit(1)
    
    if not academic_csv.exists():
        print(f"[!] Error: Academic records CSV file not found at {academic_csv}")
        sys.exit(1)
    
    try:
        # Create database session
        session = get_db_session()
        
        # Import students first (creates users and profiles)
        student_id_to_email = import_students(session, str(student_csv))
        
        # Import academic records (creates terms and subjects)
        import_academic_records(session, str(academic_csv), student_id_to_email)
        
        # Print sample data for verification
        print_sample_data(session)
        
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
