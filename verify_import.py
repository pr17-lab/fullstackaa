#!/usr/bin/env python3
"""Quick verification script to check imported subject names"""

import pandas as pd
from sqlalchemy import create_engine

DATABASE_URL = "postgresql://studentadmin:studentpass123@localhost:5432/student_tracker"
engine = create_engine(DATABASE_URL)

print("=" * 80)
print("VERIFICATION: Subject Names for Student S00001")
print("=" * 80)

# Query student S00001's subjects
query = """
SELECT 
    u.student_id,
    t.semester,
    s.subject_code,
    s.subject_name,
    s.marks
FROM users u
JOIN academic_terms t ON u.id = t.user_id
JOIN subjects s ON t.id = s.term_id
WHERE u.student_id = 'S00001'
ORDER BY t.semester, s.subject_code
LIMIT 30
"""

df = pd.read_sql(query, engine)
print(f"\nFirst 30 subjects for student S00001:\n")
print(df.to_string(index=False))

print("\n" + "=" * 80)
print("ALL UNIQUE SUBJECTS IN DATABASE")
print("=" * 80)

# Get all unique subjects
unique_query = "SELECT DISTINCT subject_name FROM subjects ORDER BY subject_name"
unique_df = pd.read_sql(unique_query, engine)
print(f"\nTotal unique subjects: {len(unique_df)}\n")
for idx, subject in enumerate(unique_df['subject_name'], 1):
    print(f"{idx}. {subject}")

print("\n" + "=" * 80)
print("SEMESTER COVERAGE")
print("=" * 80)

semester_query = "SELECT semester, COUNT(*) as term_count FROM academic_terms GROUP BY semester ORDER BY semester"
semester_df = pd.read_sql(semester_query, engine)
print("\nSemesters imported:\n")
print(semester_df.to_string(index=False))
