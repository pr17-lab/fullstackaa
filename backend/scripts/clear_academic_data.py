#!/usr/bin/env python3
"""Clear academic data (subjects and academic_terms) from database."""

import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql://studentadmin:studentpass123@localhost:5432/student_tracker"

def main():
    print("=" * 80)
    print("CLEARING ACADEMIC DATA")
    print("=" * 80)
    
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    # Get counts before deletion
    from app.models.subject import Subject
    from app.models.academic_term import AcademicTerm
    
    subjects_count = session.query(Subject).count()
    terms_count = session.query(AcademicTerm).count()
    
    print(f"\n[Before Deletion]")
    print(f"  Subjects: {subjects_count:,}")
    print(f"  Academic Terms: {terms_count:,}")
    
    # Delete in correct order (subjects first due to foreign key)
    print(f"\n[Deleting Data...]")
    deleted_subjects = session.query(Subject).delete()
    print(f"  Deleted {deleted_subjects:,} subjects")
    
    deleted_terms = session.query(AcademicTerm).delete()
    print(f"  Deleted {deleted_terms:,} academic terms")
    
    session.commit()
    
    # Verify deletion
    subjects_after = session.query(Subject).count()
    terms_after = session.query(AcademicTerm).count()
    
    print(f"\n[After Deletion]")
    print(f"  Subjects: {subjects_after:,}")
    print(f"  Academic Terms: {terms_after:,}")
    
    session.close()
    
    if subjects_after == 0 and terms_after == 0:
        print(f"\n✅ Academic data cleared successfully!")
    else:
        print(f"\n⚠️ Warning: Some data remains in database")
    
    print("=" * 80)

if __name__ == "__main__":
    main()
