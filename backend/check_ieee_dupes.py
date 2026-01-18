import pandas as pd

df = pd.read_csv('backend/data/SATA_student_main_info_10k_IEEE.csv')

print(f'Total rows in CSV: {len(df)}')
print(f'Unique student_ids: {df["student_id"].nunique()}')
print(f'Unique emails: {df["email"].nunique()}')

dup_students = df["student_id"].duplicated().sum()
dup_emails = df["email"].duplicated().sum()

print(f'\nDuplicate student_ids: {dup_students}')
print(f'Duplicate emails: {dup_emails}')

if dup_emails > 0:
    print(f'\n=== First 10 duplicate emails ===')
    dupes = df[df["email"].duplicated(keep=False)].sort_values("email")
    print(dupes[["student_id", "email", "name"]].head(10).to_string())
