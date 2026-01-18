import pandas as pd
import sys

csv_path = 'data/SATA_student_main_info_10k_IEEE.csv'

print(f'Reading CSV: {csv_path}')
df = pd.read_csv(csv_path)

print(f'\nTotal rows: {len(df)}')
print(f'\nColumns: {list(df.columns)}')

# Check rows 995-1005 for any issues
print(f'\n=== Rows 995-1005 ===')
sample = df.iloc[995:1005]
print(sample[[' student_id', 'name', 'email', 'department']].to_string())

# Check for nulls around row 1000
print(f'\n=== Checking for nulls around row 1000 ===')
print(df.iloc[995:1005].isnull().sum())

# Check data types
print(f'\n=== Data types ===')
print(df.dtypes)

# Check for problematic values in current_semester
print(f'\n=== Sample current_semester values ===')
print(df['current_semester'].iloc[995:1005].tolist())
