"""Find which students are missing from database."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from app.core.database import engine
from sqlalchemy import text

# Load CSV
df = pd.read_csv("data/SATA_academic_records_10k.csv")
csv_students = set(df['student_id'].unique())

# Get DB students
with engine.connect() as conn:
    result = conn.execute(text("SELECT student_id FROM users WHERE student_id IS NOT NULL"))
    db_students = set(row[0] for row in result)

missing = csv_students - db_students

print(f"Students in CSV: {len(csv_students)}")
print(f"Students in DB: {len(db_students)}")
print(f"Missing from DB: {len(missing)}")

if missing:
    print(f"\nFirst 20 missing student IDs:")
    for sid in sorted(list(missing))[:20]:
        record_count = len(df[df['student_id'] == sid])
        print(f"  {sid}: {record_count} academic records")
    
    # Total records for missing students
    total_missing_records = len(df[df['student_id'].isin(missing)])
    print(f"\nTotal academic records for missing students: {total_missing_records:,}")
