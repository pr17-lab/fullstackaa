#!/usr/bin/env python3
"""Compare subject names in CSV vs Database"""

import pandas as pd
from sqlalchemy import create_engine

DATABASE_URL = "postgresql://studentadmin:studentpass123@localhost:5432/student_tracker"
CSV_PATH = "data/SATA_academic_records_10k_IEEE_progressive (1).csv"

print("=" * 100)
print("SUBJECT NAME COMPARISON: CSV vs DATABASE")
print("=" * 100)

# Read CSV
print("\n[CSV] Sample subject names from source file:")
print("-" * 100)
df_csv = pd.read_csv(CSV_PATH)
csv_subjects = df_csv[['subject_code', 'subject_name']].drop_duplicates().sort_values('subject_code').head(20)
print(csv_subjects.to_string(index=False))

# Read Database
print("\n\n[DATABASE] Sample subject names from database:")
print("-" * 100)
engine = create_engine(DATABASE_URL)
query = """
SELECT DISTINCT subject_code, subject_name 
FROM subjects 
ORDER BY subject_code 
LIMIT 20
"""
df_db = pd.read_sql(query, engine)
print(df_db.to_string(index=False))

# Check for specific examples
print("\n\n[COMPARISON] Looking for discrepancies:")
print("-" * 100)

# Get all unique subject code-name pairs from both sources
csv_pairs = set(df_csv[['subject_code', 'subject_name']].apply(tuple, axis=1))
db_pairs = set(pd.read_sql("SELECT DISTINCT subject_code, subject_name FROM subjects", engine).apply(tuple, axis=1))

# Find differences
in_csv_not_db = csv_pairs - db_pairs
in_db_not_csv = db_pairs - csv_pairs

if in_db_not_csv:
    print(f"\n⚠️  Found {len(in_db_not_csv)} subject name(s) in DATABASE that differ from CSV:")
    for code, name in sorted(list(in_db_not_csv))[:10]:
        # Find what it should be in CSV
        csv_version = df_csv[df_csv['subject_code'] == code]['subject_name'].unique()
        if len(csv_version) > 0:
            print(f"  Code: {code}")
            print(f"    DB:  '{name}'")
            print(f"    CSV: '{csv_version[0]}'")
            print()
else:
    print("\n✅ All subject names in database match the CSV source!")

print("\n" + "=" * 100)
