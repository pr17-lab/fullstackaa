"""
Update student profiles with real data from SATA_student_main_info_10k.csv.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import User, StudentProfile
from app.core.database import Base

# Database connection
DATABASE_URL = "postgresql://studentadmin:studentpass123@localhost:5432/student_tracker"

def get_db_session():
    """Create database session."""
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()

def update_profiles():
    print("="*80)
    print("UPDATING STUDENT PROFILES WITH REAL DATA")
    print("="*80)
    
    session = get_db_session()
    
    # 1. Build student_id -> username mapping from credentials file (Source of Truth for User accounts)
    print("\n[*] Loading credentials to map Student ID -> User...")
    creds_path = "data/user_credentials_10k_common_password.csv"
    creds_df = pd.read_csv(creds_path)
    student_id_to_username = dict(zip(creds_df['student_id'], creds_df['username']))
    print(f"    Loaded {len(student_id_to_username):,} student ID mappings")
    
    # 2. Load the MAIN INFO file with the real profile data
    print("\n[*] Loading real student info from SATA_student_main_info_10k.csv...")
    main_info_path = "data/SATA_student_main_info_10k.csv"
    main_df = pd.read_csv(main_info_path)
    print(f"    Loaded {len(main_df):,} student records")
    
    # 3. Pre-fetch all users to minimize queries
    print("\n[*] Fetching existing users from database...")
    users = session.query(User).all()
    # Map email -> user_id
    email_to_user_id = {u.email: u.id for u in users}
    
    # Pre-fetch existing profiles to update efficiently
    print("[*] Fetching existing profiles...")
    profiles = session.query(StudentProfile).all()
    user_id_to_profile = {p.user_id: p for p in profiles}
    
    print(f"    Found {len(profiles):,} existing profiles to potentially update")
    
    updated_count = 0
    skipped_count = 0
    not_found_count = 0
    
    print("\n[*] Starting update process...")
    
    # Iterate through the REAL info
    total_rows = len(main_df)
    
    for idx, row in main_df.iterrows():
        student_id = row['student_id']
        real_name = row['name']
        real_dept = row['department']
        # Handle semester - CSV might have it as int or string
        try:
            real_semester = int(row['current_semester'])
        except (ValueError, TypeError):
             # Fallback or skip if semester is invalid
             real_semester = 1

        # 1. Find the username for this student ID
        username = student_id_to_username.get(student_id)
        if not username:
            # This student ID wasn't in the credentials file we imported
            skipped_count += 1
            continue
            
        # 2. specific email format used in import
        email = f"{username}@student.edu"
        
        # 3. Find the user_id
        user_id = email_to_user_id.get(email)
        if not user_id:
            not_found_count += 1
            continue
            
        # 4. Get the profile
        profile = user_id_to_profile.get(user_id)
        
        if profile:
            # Update fields
            profile.name = real_name
            profile.branch = real_dept
            profile.semester = real_semester
            updated_count += 1
        else:
            # Should not happen if data is consistent, but safety check
            not_found_count += 1
            
        # Batch commit every 1000
        if updated_count % 1000 == 0:
            session.commit()
            print(f"    Progress: Updated {updated_count:,} profiles...")
            
    # Final Commit
    session.commit()
    session.close()
    
    print("\n" + "="*80)
    print("UPDATE COMPLETE")
    print("="*80)
    print(f"Total Records in CSV: {total_rows:,}")
    print(f"Profiles Updated:     {updated_count:,}")
    print(f"Skipped (No Creds):   {skipped_count:,}")
    print(f"User Not Found:       {not_found_count:,}")
    print("="*80)

if __name__ == "__main__":
    update_profiles()
