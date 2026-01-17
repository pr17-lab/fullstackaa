"""
Check if student IDs from academic records CSV match user_credentials CSV.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd

print("="*80)
print("STUDENT ID MATCHING CHECK")
print("="*80)

# Load both CSVs
print("\nLoading CSV files...")
academic_df = pd.read_csv("data/SATA_academic_records_10k.csv")
credentials_df = pd.read_csv("data/user_credentials_10k_common_password.csv")

print(f"\nAcademic Records CSV:")
print(f"  Total rows: {len(academic_df):,}")
print(f"  Unique student IDs: {academic_df['student_id'].nunique():,}")
print(f"  Student ID range: {academic_df['student_id'].min()} to {academic_df['student_id'].max()}")

print(f"\nUser Credentials CSV:")
print(f"  Total rows: {len(credentials_df):,}")
print(f"  Unique student IDs: {credentials_df['student_id'].nunique():,}")
print(f"  Student ID range: {credentials_df['student_id'].min()} to {credentials_df['student_id'].max()}")

# Get unique student IDs from both
academic_ids = set(academic_df['student_id'].unique())
credentials_ids = set(credentials_df['student_id'].unique())

# Find matches
matching_ids = academic_ids.intersection(credentials_ids)
academic_only = academic_ids - credentials_ids
credentials_only = credentials_ids - academic_ids

print(f"\n{'='*80}")
print("MATCHING RESULTS")
print('='*80)

print(f"\nStudent IDs in BOTH CSVs: {len(matching_ids):,}")
print(f"Student IDs ONLY in academic records: {len(academic_only):,}")
print(f"Student IDs ONLY in credentials: {len(credentials_only):,}")

if len(academic_only) > 0:
    print(f"\nSample IDs only in academic records (first 10):")
    for sid in list(academic_only)[:10]:
        print(f"  {sid}")

if len(credentials_only) > 0:
    print(f"\nSample IDs only in credentials (first 10):")
    for sid in list(credentials_only)[:10]:
        print(f"  {sid}")

# Calculate coverage
coverage = (len(matching_ids) / len(credentials_ids)) * 100
print(f"\n\nCOVERAGE:")
print(f"  {len(matching_ids):,} out of {len(credentials_ids):,} students ({coverage:.1f}%) have academic records")

# Check academic records distribution
print(f"\n\nACADEMIC RECORDS DISTRIBUTION:")
records_per_student = academic_df.groupby('student_id').size()
print(f"  Average records per student: {records_per_student.mean():.1f}")
print(f"  Min records: {records_per_student.min()}")
print(f"  Max records: {records_per_student.max()}")

# Sample breakdown
print(f"\n\nSample student academic data:")
sample_student = academic_df['student_id'].iloc[0]
sample_data = academic_df[academic_df['student_id'] == sample_student]
print(f"\nStudent {sample_student}:")
print(f"  Total subjects: {len(sample_data)}")
print(f"  Semesters: {sorted(sample_data['semester'].unique())}")
print(f"  Subjects per semester: {len(sample_data) / sample_data['semester'].nunique():.1f}")

print(f"\n{'='*80}\n")
