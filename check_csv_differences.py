#!/usr/bin/env python3
"""Quick script to compare CSV files and show subject name differences"""

import pandas as pd

print("=" * 100)
print("COMPARING CSV FILES - SUBJECT NAMES")
print("=" * 100)

# Load both CSVs
progressive = pd.read_csv('backend/data/SATA_academic_records_10k_IEEE_progressive (1).csv')
regular = pd.read_csv('backend/data/SATA_academic_records_10k_IEEE.csv')

print("\n1. CSV FILE COLUMNS:")
print("-" * 100)
print("Progressive CSV columns:", progressive.columns.tolist())
print("\nRegular CSV columns:", regular.columns.tolist())

print("\n\n2. SUBJECT NAMES - PROGRESSIVE CSV (First 30 rows):")
print("-" * 100)
print(progressive[['student_id', 'semester', 'subject_code', 'subject_name', 'Total_marks']].head(30).to_string(index=False))

print("\n\n3. SUBJECT NAMES - REGULAR CSV (First 30 rows):")
print("-" * 100)
print(regular[['student_id', 'semester', 'subject_code', 'subject_name', 'Total_marks']].head(30).to_string(index=False))

print("\n\n4. UNIQUE SUBJECTS IN EACH FILE:")
print("-" * 100)
print(f"\nProgressive CSV unique subjects: {progressive['subject_name'].nunique()}")
print("Sample subjects:")
print(progressive['subject_name'].unique()[:15])

print(f"\n\nRegular CSV unique subjects: {regular['subject_name'].nunique()}")
print("Sample subjects:")
print(regular['subject_name'].unique()[:15])

print("\n\n5. KEY DIFFERENCE:")
print("-" * 100)
# Check if 'subject_cc' column exists
if 'subject_cc' in progressive.columns:
    print("✓ Progressive CSV has 'subject_cc' column")
    print(f"  Sample values: {progressive['subject_cc'].head(10).tolist()}")
else:
    print("✗ Progressive CSV does NOT have 'subject_cc' column")

if 'subject_cc' in regular.columns:
    print("✓ Regular CSV has 'subject_cc' column")
else:
    print("✗ Regular CSV does NOT have 'subject_cc' column")

# Check which has 'subject_code'
if 'subject_code' in progressive.columns:
    print("\n✓ Progressive CSV has 'subject_code' column")
else:
    print("\n✗ Progressive CSV does NOT have 'subject_code' column")

if 'subject_code' in regular.columns:
    print("✓ Regular CSV has 'subject_code' column")
else:
    print("✗ Regular CSV does NOT have 'subject_code' column")
