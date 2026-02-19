#!/usr/bin/env python3
"""Verify subject names after import"""

from sqlalchemy import create_engine
import pandas as pd

DATABASE_URL = "postgresql://studentadmin:studentpass123@localhost:5432/student_tracker"
engine = create_engine(DATABASE_URL)

print("=" * 80)
print("VERIFICATION: Subject Names After Import")
print("=" * 80)

# Check specific subject codes
query = """
SELECT DISTINCT subject_code, subject_name 
FROM subjects 
WHERE subject_code IN ('CS301', 'CS302', 'IT301', 'AI301', 'EC301')
ORDER BY subject_code
"""
df = pd.read_sql(query, engine)
print("\n[Sample Subject Names]")
print(df.to_string(index=False))

# Get counts
counts_query = """
SELECT 
    (SELECT COUNT(*) FROM academic_terms) as terms,
    (SELECT COUNT(*) FROM subjects) as subjects
"""
counts = pd.read_sql(counts_query, engine)
print(f"\n[Database Counts]")
print(f"  Academic Terms: {counts.iloc[0]['terms']:,}")
print(f"  Subjects: {counts.iloc[0]['subjects']:,}")

print("\n" + "=" * 80)
print("Expected vs Actual:")
print("  CS301 → Should be 'Design and Analysis of Algorithms'")
print("  CS302 → Should be 'Operating Systems'")
print("  IT301 → Should be 'Database Systems'")
print("=" * 80)
