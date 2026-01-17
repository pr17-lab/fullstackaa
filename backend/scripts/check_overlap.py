"""Check student_id mapping between CSVs."""
import csv
from pathlib import Path

backend_dir = Path(__file__).parent.parent

# Load credentials CSV
cred_csv = backend_dir / "data" / "user_credentials_10k_common_password.csv"
student_info_csv = backend_dir / "data" / "SATA_student_main_info_10k.csv"

print("Credentials CSV - First 5 student_ids:")
with open(cred_csv, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for i,  row in enumerate(reader):
        if i >= 5:
            break
        print(f"  {row.get('student_id')}")

print("\nStudent Info CSV - First 5 student_ids:")
with open(student_info_csv, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for i, row in enumerate(reader):
        if i >= 5:
            break
        print(f"  {row.get('student_id')} -> {row.get('email')}")

# Check for overlap
print("\nChecking for overlap...")
with open(cred_csv, 'r', encoding='utf-8') as f:
    cred_ids = {row['student_id'] for row in csv.DictReader(f)}

with open(student_info_csv, 'r', encoding='utf-8') as f:
    info_ids = {row['student_id'] for row in csv.DictReader(f)}

overlap = cred_ids & info_ids
print(f"Credentials CSV has {len(cred_ids)} student IDs")
print(f"Student Info CSV has {len(info_ids)} student IDs")
print(f"Overlap: {len(overlap)} matching IDs")
