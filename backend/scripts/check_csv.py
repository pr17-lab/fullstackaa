"""Check CSV structure and password format."""
import csv
from pathlib import Path

csv_path = Path(__file__).parent.parent / "data" / "user_credentials_10k_common_password.csv"

with open(csv_path, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    print("CSV Columns:", reader.fieldnames)
    print("\nFirst 3 rows:")
    for i, row in enumerate(reader):
        if i >= 3:
            break
        print(f"\nRow {i+1}:")
        for key, value in row.items():
            if len(str(value)) > 60:
                print(f"  {key}: {value[:60]}... (length: {len(value)})")
            else:
                print(f"  {key}: {value}")
