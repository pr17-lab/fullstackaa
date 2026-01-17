import pandas as pd

academic = pd.read_csv("data/SATA_academic_records_10k.csv")
credentials = pd.read_csv("data/user_credentials_10k_common_password.csv")

academic_ids = set(academic['student_id'].unique())
credentials_ids = set(credentials['student_id'].unique())
matching = academic_ids.intersection(credentials_ids)

print(f"Academic CSV students: {len(academic_ids)}")
print(f"Credentials CSV students: {len(credentials_ids)}")
print(f"Matching students: {len(matching)}")
print(f"Coverage: {(len(matching)/len(credentials_ids)*100):.1f}%")
print(f"\nTotal academic records: {len(academic):,}")
print(f"Records per student: {len(academic)/len(academic_ids):.1f}")
