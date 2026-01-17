"""Investigate missing academic records."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from app.core.database import engine
from sqlalchemy import text

print("=" * 80)
print("MISSING ACADEMIC RECORDS INVESTIGATION")
print("=" * 80)

# Load CSV
csv_path = "data/SATA_academic_records_10k.csv"
print(f"\nLoading CSV: {csv_path}")
df = pd.read_csv(csv_path)
print(f"  Total CSV rows: {len(df):,}")

# Get database counts
with engine.connect() as conn:
    # Get subject count
    result = conn.execute(text("SELECT COUNT(*) FROM subjects"))
    db_subjects = result.scalar()
    print(f"  Database subjects: {db_subjects:,}")
    print(f"  Missing: {len(df) - db_subjects:,} ({100 * (len(df) - db_subjects) / len(df):.2f}%)")
    
    # Check for students in CSV but not in DB
    print("\n[Check 1] Students in CSV vs Database...")
    csv_students = set(df['student_id'].unique())
    print(f"  Unique students in CSV: {len(csv_students):,}")
    
    result = conn.execute(text("SELECT student_id FROM users WHERE student_id IS NOT NULL"))
    db_students = set(row[0] for row in result)
    print(f"  Unique students in DB: {len(db_students):,}")
    
    missing_students = csv_students - db_students
    if missing_students:
        print(f"  Students in CSV but NOT in DB: {len(missing_students)}")
        print(f"  Sample: {list(missing_students)[:5]}")
        
        # Count records for missing students
        missing_count = df[df['student_id'].isin(missing_students)].shape[0]
        print(f"  Records for missing students: {missing_count:,}")
    else:
        print(f"  All CSV students exist in database!")
    
    # Check for duplicate subject codes within same term
    print("\n[Check 2] Duplicate subjects within same term...")
    duplicates = df.groupby(['student_id', 'semester', 'subject_code']).size()
    duplicates = duplicates[duplicates > 1]
    if len(duplicates) > 0:
        print(f"  Found {len(duplicates)} duplicate subject entries")
        print(f"  Total duplicate records: {duplicates.sum() - len(duplicates)}")
        print(f"  Sample duplicates:")
        for idx, count in list(duplicates.head(3).items()):
            print(f"    {idx}: {count} occurrences")
    else:
        print(f"  No duplicates found in CSV")
    
    # Check which students have no academic records
    print("\n[Check 3] Students without academic records...")
    result = conn.execute(text("""
        SELECT COUNT(*) FROM users u
        WHERE student_id IS NOT NULL
        AND NOT EXISTS (
            SELECT 1 FROM academic_terms at WHERE at.user_id = u.id
        )
    """))
    students_without_records = result.scalar()
    print(f"  Students with no academic records: {students_without_records:,}")
    
    # Sample student check
    print("\n[Check 4] Verifying sample student S00001...")
    result = conn.execute(text("""
        SELECT 
            (SELECT COUNT(*) FROM academic_terms WHERE user_id = u.id) as term_count,
            (SELECT COUNT(*) FROM subjects s 
             JOIN academic_terms at ON s.term_id = at.id 
             WHERE at.user_id = u.id) as subject_count
        FROM users u
        WHERE student_id = 'S00001'
    """))
    row = result.fetchone()
    if row:
        print(f"  S00001 has {row[0]} terms and {row[1]} subjects")
        
        # Check CSV
        csv_records = df[df['student_id'] == 'S00001']
        print(f"  CSV has {len(csv_records)} records for S00001")
        print(f"  CSV semesters: {sorted(csv_records['semester'].unique())}")
    
    conn.close()

print("\n" + "=" * 80)
print("INVESTIGATION COMPLETE")
print("=" * 80)
