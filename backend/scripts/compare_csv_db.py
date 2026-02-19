#!/usr/bin/env python3
"""
Compare CSV data with database to verify import completeness.
"""

import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from collections import defaultdict

from app.models.user import User
from app.models.academic_term import AcademicTerm
from app.models.subject import Subject

DATABASE_URL = "postgresql://studentadmin:studentpass123@localhost:5432/student_tracker"
CSV_PATH = backend_dir / "data" / "SATA_academic_records_10k_IEEE_progressive (1).csv"


def main():
    print("=" * 80)
    print("CSV vs DATABASE COMPARISON")
    print("=" * 80)
    
    # Read CSV
    print(f"\n[*] Reading CSV: {CSV_PATH.name}")
    df = pd.read_csv(CSV_PATH)
    
    print(f"\n[CSV STATISTICS]")
    print(f"  Total subject records: {len(df):,}")
    print(f"  Unique students: {df['student_id'].nunique():,}")
    print(f"  Unique semesters: {sorted(df['semester'].unique())}")
    print(f"  Columns: {list(df.columns)}")
    
    # Group by student-semester
    csv_student_semesters = defaultdict(set)
    for _, row in df.iterrows():
        csv_student_semesters[row['student_id']].add(int(row['semester']))
    
    csv_unique_combinations = sum(len(sems) for sems in csv_student_semesters.values())
    print(f"  Unique student-semester combinations: {csv_unique_combinations:,}")
    
    # Sample data
    print(f"\n[CSV SAMPLE DATA]")
    print(df.head(10).to_string())
    
    # Database query
    print(f"\n[*] Querying database...")
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    # Get database counts
    total_users = session.query(User).count()
    total_terms = session.query(AcademicTerm).count()
    total_subjects = session.query(Subject).count()
    
    print(f"\n[DATABASE STATISTICS]")
    print(f"  Total users: {total_users:,}")
    print(f"  Total academic terms: {total_terms:,}")
    print(f"  Total subjects: {total_subjects:,}")
    
    # Get students with academic records
    users_with_terms = session.query(User).join(AcademicTerm).distinct().count()
    print(f"  Users with academic records: {users_with_terms:,}")
    
    # Sample database data
    print(f"\n[DATABASE SAMPLE DATA]")
    sample_terms = session.query(AcademicTerm).limit(5).all()
    for term in sample_terms:
        subjects_count = session.query(Subject).filter(Subject.term_id == term.id).count()
        user = session.query(User).filter(User.id == term.user_id).first()
        print(f"  Student {user.student_id} | Sem {term.semester} | Year {term.year} | GPA {term.gpa} | Subjects: {subjects_count}")
    
    # Compare
    print(f"\n[COMPARISON]")
    print(f"  CSV student-semester combinations: {csv_unique_combinations:,}")
    print(f"  Database academic terms:           {total_terms:,}")
    print(f"  Difference:                        {csv_unique_combinations - total_terms:,}")
    
    print(f"\n  CSV total subject records:         {len(df):,}")
    print(f"  Database total subjects:           {total_subjects:,}")
    print(f"  Difference:                        {len(df) - total_subjects:,}")
    
    # Check for students in CSV but not in DB
    db_student_ids = {u.student_id for u in session.query(User.student_id).all()}
    csv_student_ids = set(df['student_id'].unique())
    
    missing_in_db = csv_student_ids - db_student_ids
    print(f"\n  Students in CSV not in DB:         {len(missing_in_db):,}")
    if len(missing_in_db) > 0 and len(missing_in_db) <= 10:
        print(f"    Missing student IDs: {list(missing_in_db)}")
    
    session.close()
    print(f"\n{'=' * 80}")


if __name__ == "__main__":
    main()
