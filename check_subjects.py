#!/usr/bin/env python3
import pandas as pd
from sqlalchemy import create_engine

engine = create_engine("postgresql://studentadmin:studentpass123@localhost:5432/student_tracker")

# Get unique subjects
df = pd.read_sql("SELECT DISTINCT subject_name FROM subjects ORDER BY subject_name", engine)
subjects = df["subject_name"].tolist()

print("=" * 80)
print(f"VERIFICATION COMPLETE - {len(subjects)} Unique Subjects Imported")
print("=" * 80)
print()
for idx, subject in enumerate(subjects, 1):
    print(f"{idx:2d}. {subject}")
