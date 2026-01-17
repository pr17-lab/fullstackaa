"""Check CSV file statistics."""
import pandas as pd

csv_path = "data/SATA_academic_records_10k.csv"
df = pd.read_csv(csv_path)

print(f"CSV Statistics:")
print(f"  Total rows: {len(df):,}")
print(f"  Unique students: {df['student_id'].nunique():,}")
print(f"  Unique semesters: {df['semester'].nunique()}")
print(f"  Unique student-semester combinations: {df.groupby(['student_id', 'semester']).ngroups:,}")
print(f"  Total subjects (expected in DB): {len(df):,}")
