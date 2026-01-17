#!/usr/bin/env python3
"""
OPTIMIZED academic records import - uses bulk operations and caching.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from collections import defaultdict

from app.models import User, AcademicTerm, Subject

# Database connection
DATABASE_URL = "postgresql://studentadmin:studentpass123@localhost:5432/student_tracker"

def get_db_session():
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()

def build_student_id_to_user_map(session):
    """Build mapping from student_id to user ID."""
    print("\n[*] Building student_id to user mapping...")
    
    # Load all users with student_id in ONE query
    users = session.query(User.id, User.student_id).filter(User.student_id.isnot(None)).all()
    student_id_to_user_id = {user.student_id: user.id for user in users}
    
    print(f"    Mapped {len(student_id_to_user_id):,} student IDs to user IDs")
    return student_id_to_user_id

def load_existing_data(session):
    """Load existing terms and subjects to avoid duplicates."""
    print("\n[*] Loading existing academic data...")
    
    # Load ALL existing terms in ONE query
    existing_terms = session.query(
        AcademicTerm.user_id, 
        AcademicTerm.semester, 
        AcademicTerm.year,
        AcademicTerm.id
    ).all()
    
    # Create lookup: (user_id, semester, year) -> term_id
    term_lookup = {(t.user_id, t.semester, t.year): t.id for t in existing_terms}
    print(f"    Found {len(term_lookup):,} existing academic terms")
    
    # Load ALL existing subjects in ONE query
    existing_subjects = session.query(
        Subject.term_id,
        Subject.subject_code
    ).all()
    
    # Create lookup: (term_id, subject_code) -> exists
    subject_lookup = {(s.term_id, s.subject_code) for s in existing_subjects}
    print(f"    Found {len(subject_lookup):,} existing subjects")
    
    return term_lookup, subject_lookup

def import_academic_records_optimized(session, csv_path: str, student_id_to_user_id: dict):
    """Optimized import using bulk inserts and minimal queries."""
    print(f"\n[*] Reading academic records from {csv_path}...")
    df = pd.read_csv(csv_path)
    print(f"    Found {len(df):,} academic record entries in CSV")
    
    # Load existing data ONCE
    term_lookup, subject_lookup = load_existing_data(session)
    
    # Group by student_id and semester
    grouped = df.groupby(['student_id', 'semester'])
    total_groups = len(grouped)
    print(f"    Processing {total_groups:,} student-semester combinations...")
    
    # Prepare bulk insert lists
    new_terms = []
    new_subjects = []
    
    terms_created = 0
    terms_skipped = 0
    subjects_created = 0
    subjects_skipped = 0
    students_skipped = 0
    
    processed = 0
    
    for (student_id, semester), group in grouped:
        processed += 1
        
        if processed % 5000 == 0:
            print(f"    Progress: {processed:,}/{total_groups:,} ({100*processed/total_groups:.1f}%)")
        
        # Get user_id
        user_id = student_id_to_user_id.get(student_id)
        if not user_id:
            students_skipped += 1
            continue
        
        # Check if term exists
        year = 2024
        semester_int = int(semester)
        term_key = (user_id, semester_int, year)
        
        if term_key in term_lookup:
            # Term already exists
            term_id = term_lookup[term_key]
            terms_skipped += 1
        else:
            # Calculate GPA
            total_marks = group['Total_marks'].mean()
            gpa = min(round(total_marks / 10, 2), 9.99)
            
            # Add to bulk insert list
            term_obj = AcademicTerm(
                user_id=user_id,
                semester=semester_int,
                year=year,
                gpa=float(gpa)
            )
            new_terms.append(term_obj)
            
            # We'll need to flush to get term_id, so do mini-batches
            if len(new_terms) >= 500:
                session.bulk_save_objects(new_terms, return_defaults=True)
                session.flush()
                # Add to lookup
                for term in new_terms:
                    term_lookup[(term.user_id, term.semester, term.year)] = term.id
                terms_created += len(new_terms)
                new_terms = []
            
            # For now, use a placeholder - we'll handle this specially
            term_id = None
        
        # Process subjects for this term
        if term_id:  # If term already existed
            grade_map = {'Pass': 'P', 'Fail': 'F'}
            
            for _, subject_row in group.iterrows():
                subject_key = (term_id, subject_row['subject_code'])
                
                if subject_key not in subject_lookup:
                    grade = grade_map.get(subject_row['pass_fail'], 'P')
                    
                    subject_obj = Subject(
                        term_id=term_id,
                        subject_name=subject_row['subject_name'],
                        subject_code=subject_row['subject_code'],
                        credits=int(subject_row['credits']),
                        marks=float(subject_row['Total_marks']),
                        grade=grade
                    )
                    new_subjects.append(subject_obj)
                    subject_lookup.add(subject_key)
                    subjects_created += 1
                else:
                    subjects_skipped += 1
            
            # Bulk insert subjects every 1000
            if len(new_subjects) >= 1000:
                session.bulk_save_objects(new_subjects)
                session.commit()
                new_subjects = []
    
    # Final flush for remaining terms
    if new_terms:
        session.bulk_save_objects(new_terms, return_defaults=True)
        session.flush()
        for term in new_terms:
            term_lookup[(term.user_id, term.semester, term.year)] = term.id
        terms_created += len(new_terms)
        
        # Now process subjects for these new terms
        print(f"\n[*] Processing subjects for {len(new_terms)} new terms...")
        
        # Re-iterate to add subjects for new terms
        processed = 0
        for (student_id, semester), group in grouped:
            processed += 1
            
            user_id = student_id_to_user_id.get(student_id)
            if not user_id:
                continue
            
            term_key = (user_id, int(semester), 2024)
            if term_key not in term_lookup:
                continue
                
            term_id = term_lookup[term_key]
            grade_map = {'Pass': 'P', 'Fail': 'F'}
            
            for _, subject_row in group.iterrows():
                subject_key = (term_id, subject_row['subject_code'])
                
                if subject_key not in subject_lookup:
                    grade = grade_map.get(subject_row['pass_fail'], 'P')
                    
                    subject_obj = Subject(
                        term_id=term_id,
                        subject_name=subject_row['subject_name'],
                        subject_code=subject_row['subject_code'],
                        credits=int(subject_row['credits']),
                        marks=float(subject_row['Total_marks']),
                        grade=grade
                    )
                    new_subjects.append(subject_obj)
                    subject_lookup.add(subject_key)
                    subjects_created += 1
                    
                    if len(new_subjects) >= 1000:
                        session.bulk_save_objects(new_subjects)
                        session.commit()
                        new_subjects = []
    
    # Final commit
    if new_subjects:
        session.bulk_save_objects(new_subjects)
    session.commit()
    
    print(f"\n[+] Academic Records Import Complete:")
    print(f"    - Academic terms created: {terms_created:,}")
    print(f"    - Academic terms skipped: {terms_skipped:,}")
    print(f"    - Subjects created: {subjects_created:,}")
    print(f"    - Subjects skipped: {subjects_skipped:,}")
    print(f"    - Students not found: {students_skipped:,}")

def main():
    print("=" * 80)
    print("OPTIMIZED ACADEMIC RECORDS IMPORT")
    print("=" * 80)
    
    csv_path = Path(__file__).parent.parent / "data" / "SATA_academic_records_10k.csv"
    
    if not csv_path.exists():
        print(f"[!] Error: CSV file not found at {csv_path}")
        sys.exit(1)
    
    try:
        session = get_db_session()
        
        # Build mappings
        student_id_to_user_id = build_student_id_to_user_map(session)
        
        # Import records
        import_academic_records_optimized(session, str(csv_path), student_id_to_user_id)
        
        print("\n[+] Import completed successfully!")
        session.close()
        
    except Exception as e:
        print(f"\n[!] Error during import: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
