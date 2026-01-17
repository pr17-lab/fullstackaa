import csv
import sys

csv_path = 'data/user_credentials_10k_common_password.csv'

with open(csv_path, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    print(f"Columns: {list(reader.fieldnames)}")
    print()
    
    # Show first row
    row = next(reader)
    print("First row:")
    for key, value in row.items():
        print(f"  {key}: {value[:100] if len(str(value)) > 100 else value}")
