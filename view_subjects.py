#!/usr/bin/env python3
"""Simple script to view subjects table"""

import pandas as pd
from sqlalchemy import create_engine

# Database connection
DATABASE_URL = "postgresql://studentadmin:studentpass123@localhost:5432/student_tracker"
engine = create_engine(DATABASE_URL)

# Query subjects table
print("=" * 100)
print("SUBJECTS TABLE - First 50 Records")
print("=" * 100)

query = """
SELECT 
    id,
    term_id,
    subject_code,
    subject_name,
    credits,
    marks,
    grade,
    created_at
FROM subjects
ORDER BY id
LIMIT 50;
"""

df = pd.read_sql(query, engine)

# Display formatted
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', 30)

print(df.to_string(index=False))

# Show statistics
print("\n" + "=" * 100)
print("STATISTICS")
print("=" * 100)

stats_query = """
SELECT 
    COUNT(*) as total_subjects,
    COUNT(DISTINCT subject_name) as unique_subjects,
    ROUND(AVG(marks), 2) as avg_marks,
    MIN(marks) as min_marks,
    MAX(marks) as max_marks
FROM subjects;
"""

stats = pd.read_sql(stats_query, engine)
print(stats.to_string(index=False))

# Show subject distribution
print("\n" + "=" * 100)
print("TOP 10 MOST COMMON SUBJECTS")
print("=" * 100)

dist_query = """
SELECT 
    subject_name,
    COUNT(*) as count
FROM subjects
GROUP BY subject_name
ORDER BY count DESC
LIMIT 10;
"""

dist = pd.read_sql(dist_query, engine)
print(dist.to_string(index=False))

print("\n✅ Done! Want to see more? Edit the LIMIT in the query.")
