import pandas as pd

df = pd.read_csv('backend/data/SATA_student_main_info_10k_IEEE.csv')

print(f'Total rows in CSV: {len(df)}')
print(f'Unique student_ids: {df["student_id"].nunique()}')
print(f'Unique emails: {df["email"].nunique()}')
print(f'Duplicate student_ids: {df["student_id"].duplicated().sum()}')
print(f'Duplicate emails: {df["email"].duplicated().sum()}')

# Check for duplicates
if df["email"].duplicated().sum() > 0:
    print('\nSample duplicate emails:')
    dupes = df[df["email"].duplicated(keep=False)].sort_values("email")
    print(dupes[["student_id", "email", "name"]].head(10))
