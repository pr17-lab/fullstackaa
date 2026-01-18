#!/usr/bin/env python3
"""
Import IEEE CSV with duplicate email handling.
This script deduplicates the CSV first, then imports all unique records.
"""

import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import User, StudentProfile

DATABASE_URL = "postgresql://studentadmin:studentpass123@localhost:5432/student_tracker"
IEEE_CSV_PATH = backend_dir / "data" / "SATA_student_main_info_10k_IEEE.csv"


def main():
    print("=" * 80)
    print("IMPORTING IEEE CSV (DEDUPLICATED)")
    print("=" * 80)
    
    # Read CSV
    print(f"\n[*] Reading CSV: {IEEE_CSV_PATH}")
    df = pd.read_csv(IEEE_CSV_PATH)
    print(f"    Total rows: {len(df):,}")
    
    # Deduplicate by email (keep first occurrence)
    original_count = len(df)
    df_deduped = df.drop_duplicates(subset=['email'], keep='first')
    duplicates_removed = original_count - len(df_deduped)
    
    print(f"\n[*] Deduplication:")
    print(f"    Original rows: {original_count:,}")
    print(f"    Duplicates removed: {duplicates_removed:,}")
    print(f"    Unique rows to import: {len(df_deduped):,}")
    
    # Create session
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    print(f"\n[*] Importing {len(df_deduped):,} unique students...")
    
    users_created = 0
    profiles_created = 0
    
    for idx, row in df_deduped.iterrows():
        try:
            # Create User
            user = User(
                student_id=row['student_id'],
                email=row['email'],
                password_hash='',
                is_active=True
            )
            session.add(user)
            session.flush()
            users_created += 1
            
            # Create Profile
            profile = StudentProfile(
                user_id=user.id,
                name=row['name'],
                branch=row['department'],
                semester=int(row['current_semester']),
                interests=None
            )
            session.add(profile)
            profiles_created += 1
            
            if (users_created) % 1000 == 0:
                session.commit()
                print(f"    Progress: {users_created:,}/{len(df_deduped):,}...")
                
        except Exception as e:
            print(f"    [!] Error on row {idx}: {str(e)[:100]}")
            session.rollback()
    
    # Final commit
    session.commit()
    
    print(f"\n[+] Import complete!")
    print(f"    Users created: {users_created:,}")
    print(f"    Profiles created: {profiles_created:,}")
    
    # Verify
    total_users = session.query(User).count()
    total_profiles = session.query(StudentProfile).count()
    
    print(f"\n[*] Database totals:")
    print(f"    Users: {total_users:,}")
    print(f"    Profiles: {total_profiles:,}")
    
    session.close()


if __name__ == "__main__":
    main()
