#!/usr/bin/env python3
"""
Import academic records from IEEE CSV.
Creates AcademicTerm and Subject records with proper GPA calculations.
"""

import sys
from pathlib import Path
from collections import defaultdict

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import User, AcademicTerm, Subject

DATABASE_URL = "postgresql://studentadmin:studentpass123@localhost:5432/student_tracker"
IEEE_CSV_PATH = backend_dir / "data" / "SATA_academic_records_10k_IEEE.csv"

# Grade to grade point mapping
GRADE_POINTS = {
    'A+': 4.0, 'A': 4.0, 'A-': 3.7,
    'B+': 3.3, 'B': 3.0, 'B-': 2.7,
    'C+': 2.3, 'C': 2.0, 'C-': 1.7,
    'D': 1.0, 'F': 0.0
}

def calculate_grade(marks):
    """Convert marks to grade."""
    if marks >= 90: return 'A+'
    elif marks >= 85: return 'A'
    elif marks >= 80: return 'A-'
    elif marks >= 75: return 'B+'
    elif marks >= 70: return 'B'
    elif marks >= 65: return 'B-'
    elif marks >= 60: return 'C+'
    elif marks >= 55: return 'C'
    elif marks >= 50: return 'C-'
    elif marks >= 40: return 'D'
    else: return 'F'

def calculate_gpa(subjects_data):
    """Calculate GPA from list of (credits, grade) tuples."""
    total_points = 0
    total_credits = 0
    for credits, marks in subjects_data:
        grade = calculate_grade(marks)
        grade_point = GRADE_POINTS.get(grade, 0.0)
        total_points += credits * grade_point
        total_credits += credits
    
    if total_credits == 0:
        return 0.0
    return round(total_points / total_credits, 2)


def main():
    print("=" * 80)
    print("IMPORTING ACADEMIC RECORDS FROM IEEE CSV")
    print("=" * 80)
    
    # Read CSV
    print(f"\n[*] Reading CSV: {IEEE_CSV_PATH.name}")
    df = pd.read_csv(IEEE_CSV_PATH)
    print(f"    Total subject records: {len(df):,}")
    
    # Create session
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    # Get all users and create student_id -> user_id mapping
    print(f"\n[*] Loading user mappings...")
    users = session.query(User).all()
    student_id_to_user_id = {u.student_id: u.id for u in users if u.student_id}
    print(f"    Found {len(student_id_to_user_id):,} students in database")
    
    # Group data by student and semester
    print(f"\n[*] Grouping records by student and semester...")
    student_semester_data = defaultdict(lambda: defaultdict(list))
    
    skipped_no_user = 0
    for idx, row in df.iterrows():
        student_id = row['student_id']
        
        # Skip if student doesn't exist in database
        if student_id not in student_id_to_user_id:
            skipped_no_user += 1
            continue
        
        semester = int(row['semester'])
        
        # Store subject data for this student-semester combination
        student_semester_data[student_id][semester].append({
            'subject_code': row['subject_code'],
            'subject_name': row['subject_name'],
            'credits': int(row['credits']),
            'marks': float(row['Total_marks'])
        })
    
    print(f"    Unique students with records: {len(student_semester_data):,}")
    print(f"    Records skipped (student not in DB): {skipped_no_user:,}")
    
    # Import academic terms and subjects
    print(f"\n[*] Creating academic terms and subjects...")
    
    terms_created = 0
    subjects_created = 0
    errors = []
    
    for student_id, semesters in student_semester_data.items():
        user_id = student_id_to_user_id[student_id]
        
        for semester, subjects_data in semesters.items():
            try:
                # Calculate GPA for this semester
                credits_grades = [(s['credits'], s['marks']) for s in subjects_data]
                gpa = calculate_gpa(credits_grades)
                
                # Estimate year based on semester (1-2=Year1, 3-4=Year2, etc.)
                year = 2020 + ((semester - 1) // 2)
                
                # Create AcademicTerm
                term = AcademicTerm(
                    user_id=user_id,
                    semester=semester,
                    year=year,
                    gpa=gpa
                )
                session.add(term)
                session.flush()  # Get term.id
                terms_created += 1
                
                # Create subjects for this term
                for subject_data in subjects_data:
                    grade = calculate_grade(subject_data['marks'])
                    
                    subject = Subject(
                        term_id=term.id,
                        subject_code=subject_data['subject_code'],
                        subject_name=subject_data['subject_name'],
                        credits=subject_data['credits'],
                        marks=subject_data['marks'],
                        grade=grade
                    )
                    session.add(subject)
                    subjects_created += 1
                
                # Commit in batches
                if terms_created % 500 == 0:
                    session.commit()
                    print(f"    Progress: {terms_created:,} terms, {subjects_created:,} subjects created...")
                    
            except Exception as e:
                error_msg = str(e).lower()
                if 'unique constraint' not in error_msg:
                    errors.append(f"Student {student_id}, Sem {semester}: {str(e)[:100]}")
                session.rollback()
                if len(errors) >= 20:
                    print(f"[!] Too many errors, stopping")
                    break
    
    # Final commit
    session.commit()
    
    print(f"\n[+] Import Summary:")
    print(f"    - Academic terms created: {terms_created:,}")
    print(f"    - Subjects created: {subjects_created:,}")
    print(f"    - Students processed: {len(student_semester_data):,}")
    
    if errors:
        print(f"\n[!] Errors encountered: {len(errors)}")
        for error in errors[:5]:
            print(f"    - {error}")
    
    # Verify totals
    total_terms = session.query(AcademicTerm).count()
    total_subjects = session.query(Subject).count()
    
    print(f"\n[*] Database totals:")
    print(f"    - Academic terms: {total_terms:,}")
    print(f"    - Subjects: {total_subjects:,}")
    
    session.close()
    print(f"\n[+] Import complete!")


if __name__ == "__main__":
    main()
