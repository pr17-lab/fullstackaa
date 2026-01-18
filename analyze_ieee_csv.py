import pandas as pd

df = pd.read_csv('backend/data/SATA_student_main_info_10k_IEEE.csv')

print(f'Total rows in CSV: {len(df)}')
print(f'\nUnique student_ids: {df["student_id"].nunique()}')
print(f'Unique emails: {df["email"].nunique()}')

print(f'\nDuplicate student_ids: {df["student_id"].duplicated().sum()}')
print(f'Duplicate emails: {df["email"].duplicated().sum()}')

# Check for nulls
print(f'\nNull student_ids: {df["student_id"].isnull().sum()}')
print(f'Null emails: {df["email"].isnull().sum()}')

# Show some sample duplicate emails if they exist
if df["email"].duplicated().sum() > 0:
    print('\n=== DUPLICATE EMAILS FOUND ===')
    dupes = df[df["email"].duplicated(keep=False)].sort_values("email")
    print(dupes[["student_id", "email", "name"]].head(20))
    
# Show some sample duplicate student_ids if they exist
if df["student_id"].duplicated().sum() > 0:
    print('\n=== DUPLICATE STUDENT IDs FOUND ===')
    dupes = df[df["student_id"].duplicated(keep=False)].sort_values("student_id")
    print(dupes[["student_id", "email", "name"]].head(20))
