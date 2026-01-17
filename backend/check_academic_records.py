"""
Analyze academic records CSV and check if student IDs match database users.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd
from app.core.database import engine
from sqlalchemy import text

print("="*80)
print("ACADEMIC RECORDS CSV ANALYSIS")
print("="*80)

# Load academic records CSV
csv_path = "data/SATA_academic_records_10k.csv"
print(f"\nLoading {csv_path}...")
df = pd.read_csv(csv_path)

print(f"\nCSV File Stats:")
print(f"  Total rows: {len(df):,}")
print(f"  Columns: {list(df.columns)}")
print(f"\nFirst few rows:")
print(df.head(3))

# Get unique student IDs from CSV
unique_students_csv = df['student_id'].nunique()
print(f"\n\nUnique students in CSV: {unique_students_csv:,}")

# Get unique semesters
unique_semesters = df['semester'].nunique()
print(f"Unique semesters: {unique_semesters}")

# Get unique subjects
unique_subjects = df['subject_code'].nunique()
print(f"Unique subjects: {unique_subjects}")

# Records per student
records_per_student = len(df) / unique_students_csv
print(f"Average records per student: {records_per_student:.1f}")

# Get database users
with engine.connect() as conn:
    db_users = pd.read_sql(text("SELECT email FROM users"), conn)
    db_profiles = pd.read_sql(text("SELECT user_id FROM student_profiles"), conn)
    
    print(f"\n\nDatabase Stats:")
    print(f"  Total users in DB: {len(db_users):,}")
    print(f"  Total profiles in DB: {len(db_profiles):,}")

# Check student ID format from CSV
sample_ids = df['student_id'].head(10).tolist()
print(f"\n\nSample student IDs from CSV:")
for sid in sample_ids:
    print(f"  {sid}")

# Get student IDs range
print(f"\n\nStudent ID Range in CSV:")
print(f"  First: {df['student_id'].min()}")
print(f"  Last: {df['student_id'].max()}")

# Check if we can match student IDs to database
print(f"\n\n{'='*80}")
print("MATCHING ANALYSIS")
print('='*80)

# Get sample of usernames from database
with engine.connect() as conn:
    sample_emails = pd.read_sql(text("SELECT email FROM users LIMIT 10"), conn)
    print(f"\n\nSample emails from database:")
    for email in sample_emails['email']:
        print(f"  {email}")

# Try to extract student IDs from emails or check mapping
print(f"\n\nChecking if CSV student IDs can map to database users...")
print(f"CSV has students: S00001 to {df['student_id'].max()}")
print(f"Database has {len(db_users):,} users with email format: username@student.edu")

# Count how many CSV student IDs would match
csv_student_ids = set(df['student_id'].unique())
print(f"\n\nTotal unique student IDs in CSV: {len(csv_student_ids):,}")

# We need to check the import mapping
print(f"\n\nNOTE: The database was imported from user_credentials CSV.")
print(f"Need to check if academic records CSV student IDs match user_credentials student IDs.")

print(f"\n{'='*80}\n")
