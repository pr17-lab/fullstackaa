#!/usr/bin/env python3
"""
Import academic records from CSV into PostgreSQL database.
Maps student_ids to database users and creates academic terms and subjects.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import User, AcademicTerm, Subject
from app.core.database import Base

# Database connection
DATABASE_URL = "postgresql://studentadmin:studentpass123@localhost:5432/student_tracker"

def get_db_session():
    """Create database session."""
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()

def build_student_id_to_user_map(session):
    """Build mapping from student_id to user database ID."""
    print("\n[*] Building student_id to user mapping...")
    
    # Load credentials CSV to get student_id to username mapping
    credentials_df = pd.read_csv("data/user_credentials_10k_common_password.csv")
    
    # Create student_id -> username mapping
    student_to_username = dict(zip(credentials_df['student_id'], credentials_df['username']))
    
    # Get all users from database
    users = session.query(User).all()
    
    # Build username -> user mapping  
    # Database emails are: username@student.edu
    username_to_user = {}
    for user in users:
        username = user.email.replace('@student.edu', '')
        username_to_user[username] = user
    
    # Build final student_id -> user mapping
    student_id_to_user = {}
    for student_id, username in student_to_username.items():
        if username in username_to_user:
            student_id_to_user[student_id] = username_to_user[username]
    
    print(f"    Mapped {len(student_id_to_user):,} student IDs to database users")
    return student_id_to_user

def import_academic_records(session, csv_path: str, student_id_to_user: dict):
    """Import academic records from CSV."""
    print(f"\n[*] Reading academic records from {csv_path}...")
    df = pd.read_csv(csv_path)
    print(f"    Found {len(df):,} academic record entries in CSV")
    
    terms_created = 0
    subjects_created = 0
    terms_skipped = 0
    students_skipped = 0
    
    # Group by student_id and semester to create academic terms
    grouped = df.groupby(['student_id', 'semester'])
    total_groups = len(grouped)
    
    print(f"    Processing {total_groups:,} student-semester combinations...")
    
    processed_count = 0
    for (student_id, semester), group in grouped:
        processed_count += 1
        
        # Progress indicator every 1000 groups
        if processed_count % 1000 == 0:
            print(f"    Progress: {processed_count:,}/{total_groups:,} groups processed...")
        
        # Get user from mapping
        user = student_id_to_user.get(student_id)
        if not user:
            students_skipped += 1
            continue
        
        # Calculate GPA from marks
        total_marks = group['Total_marks'].mean()
        gpa = min(round(total_marks / 10, 2), 9.99)  # Convert to 10-point scale
        
        # Use 2024 as default year
        year = 2024
        semester_int = int(semester)
        year_int = int(year)
        
        # Check if academic term already exists
        existing_term = session.query(AcademicTerm).filter(
            AcademicTerm.user_id == user.id,
            AcademicTerm.semester == semester_int,
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
            # Check if subject already exists
            existing_subject = session.query(Subject).filter(
                Subject.term_id == term.id,
                Subject.subject_code == subject_row['subject_code']
            ).first()
            
            if not existing_subject:
                # Map pass_fail to grade
                grade_map = {'Pass': 'P', 'Fail': 'F'}
                grade = grade_map.get(subject_row['pass_fail'], 'P')
                
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
        
        # Commit in batches of 100 for performance
        if processed_count % 100 == 0:
            session.commit()
    
    # Final commit
    session.commit()
    
    print(f"\n[+] Academic Records Import Complete:")
    print(f"    - Academic terms created: {terms_created:,}")
    print(f"    - Subjects created: {subjects_created:,}")
    print(f"    - Academic terms skipped (already exist): {terms_skipped:,}")
    print(f"    - Students skipped (not in DB): {students_skipped:,}")

def print_final_counts(session):
    """Print final counts of all records."""
    print("\n" + "="*80)
    print("FINAL DATABASE COUNTS")
    print("="*80)
    
    user_count = session.query(User).count()
    term_count = session.query(AcademicTerm).count()
    subject_count = session.query(Subject).count()
    
    print(f"\n    Users: {user_count:,}")
    print(f"    Academic Terms: {term_count:,}")
    print(f"    Subjects: {subject_count:,}")
    print("\n" + "="*80)

def main():
    """Main import function."""
    print("="*80)
    print("IMPORTING ACADEMIC RECORDS TO DATABASE")
    print("="*80)
    
    csv_path = Path(__file__).parent.parent / "data" / "SATA_academic_records_10k.csv"
    
    if not csv_path.exists():
        print(f"[!] Error: CSV file not found at {csv_path}")
        sys.exit(1)
    
    try:
        session = get_db_session()
        
        # Build student ID mapping
        student_id_to_user = build_student_id_to_user_map(session)
        
        # Import academic records
        import_academic_records(session, str(csv_path), student_id_to_user)
        
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
