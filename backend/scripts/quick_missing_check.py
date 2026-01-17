"""Quick check of missing records."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from app.core.database import engine
from sqlalchemy import text

# Load CSV
df = pd.read_csv("data/SATA_academic_records_10k.csv")
csv_total = len(df)

# Get DB count
with engine.connect() as conn:
    result = conn.execute(text("SELECT COUNT(*) FROM subjects"))
    db_total = result.scalar()
    
    # Check duplicates
    duplicates = df.groupby(['student_id', 'semester', 'subject_code']).size()
    dup_count = (duplicates[duplicates > 1].sum() - len(duplicates[duplicates > 1]))
    
    # Check missing students
    csv_students = set(df['student_id'].unique())
    result = conn.execute(text("SELECT student_id FROM users WHERE student_id IS NOT NULL"))
    db_students = set(row[0] for row in result)
    missing_students = csv_students - db_students
    
    missing_student_records = 0
    if missing_students:
        missing_student_records = df[df['student_id'].isin(missing_students)].shape[0]

print(f"CSV Total: {csv_total:,}")
print(f"DB Total: {db_total:,}")
print(f"Missing: {csv_total - db_total:,}")
print(f"\nBreakdown:")
print(f"  Duplicate subject codes (skipped by import): {dup_count}")
print(f"  Missing students (not in DB): {len(missing_students)} students = {missing_student_records:,} records")
print(f"  Other/Unknown: {csv_total - db_total - dup_count - missing_student_records:,}")
