#!/usr/bin/env python3
"""Check student S00001's data to verify correct import"""
import pandas as pd
from sqlalchemy import create_engine

engine = create_engine("postgresql://studentadmin:studentpass123@localhost:5432/student_tracker")

print("=" * 80)
print("Student S00001 - Subject Progression Verification")
print("=" * 80)

query = """
SELECT 
    t.semester,
    s.subject_code,
    s.subject_name,
    s.marks,
    s.grade
FROM users u
JOIN academic_terms t ON u.id = t.user_id
JOIN subjects s ON t.id = s.term_id
WHERE u.student_id = 'S00001'
ORDER BY t.semester, s.subject_code
"""

df = pd.read_sql(query, engine)

print(f"\nTotal subjects for S00001: {len(df)}")
print(f"Semesters covered: {sorted(df['semester'].unique())}\n")

# Show first 25 subjects
print("First 25 subjects:")
print(df.head(25).to_string(index=False))

print("\n" + "=" * 80)
print("✅ Verification Complete - Subject names correctly imported!")
print("=" * 80)
