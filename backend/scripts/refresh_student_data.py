#!/usr/bin/env python3
"""
Refresh student data by replacing existing records with IEEE CSV dataset.
This script:
1. Backs up existing data
2. Truncates users and student_profiles tables
3. Imports data from SATA_student_main_info_10k_IEEE.csv
4. Verifies the import
"""

import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path to import app modules
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import subprocess

from app.models import User, StudentProfile
from app.core.database import Base

# Database connection
DATABASE_URL = "postgresql://studentadmin:studentpass123@localhost:5432/student_tracker"

# CSV file path
IEEE_CSV_PATH = backend_dir / "data" / "SATA_student_main_info_10k_IEEE.csv"


def get_db_session():
    """Create database session."""
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal(), engine


def verify_csv_exists():
    """Verify IEEE CSV file exists and is readable."""
    print(f"\n[*] Verifying CSV file: {IEEE_CSV_PATH}")
    
    if not IEEE_CSV_PATH.exists():
        print(f"[!] ERROR: CSV file not found at {IEEE_CSV_PATH}")
        sys.exit(1)
    
    print(f"    [+] CSV file found: {IEEE_CSV_PATH.name}")
    
    # Read and validate CSV structure
    try:
        df = pd.read_csv(IEEE_CSV_PATH)
        print(f"    [+] CSV contains {len(df):,} records")
        
        expected_columns = ['student_id', 'name', 'email', 'department', 'year_of_passout', 'current_semester', 'cgpa', 'status']
        missing_columns = set(expected_columns) - set(df.columns)
        
        if missing_columns:
            print(f"[!] ERROR: CSV missing required columns: {missing_columns}")
            sys.exit(1)
        
        print(f"    [+] CSV schema validated")
        return df
        
    except Exception as e:
        print(f"[!] ERROR reading CSV: {e}")
        sys.exit(1)


def show_current_counts(session):
    """Display current database row counts."""
    user_count = session.query(User).count()
    profile_count = session.query(StudentProfile).count()
    
    print(f"\n[*] Current Database Counts (Before Refresh):")
    print(f"    - Users: {user_count:,}")
    print(f"    - Student Profiles: {profile_count:,}")
    
    return user_count, profile_count


def run_backup():
    """Execute backup script."""
    print("\n" + "=" * 80)
    print("STEP 1: BACKING UP EXISTING DATA")
    print("=" * 80)
    
    backup_script = backend_dir / "scripts" / "backup_student_data.py"
    
    if not backup_script.exists():
        print(f"[!] ERROR: Backup script not found at {backup_script}")
        sys.exit(1)
    
    try:
        # Run backup script
        result = subprocess.run(
            [sys.executable, str(backup_script)],
            cwd=str(backend_dir),
            capture_output=True,
            text=True
        )
        
        # Print backup script output
        print(result.stdout)
        
        if result.returncode != 0:
            print(f"[!] ERROR: Backup failed with exit code {result.returncode}")
            print(result.stderr)
            sys.exit(1)
        
        print("[+] Backup completed successfully")
        
    except Exception as e:
        print(f"[!] ERROR running backup: {e}")
        sys.exit(1)


def truncate_tables(session, engine):
    """Truncate student_profiles and users tables."""
    print("\n" + "=" * 80)
    print("STEP 2: TRUNCATING EXISTING DATA")
    print("=" * 80)
    
    print("\n[*] WARNING: About to delete ALL data from users and student_profiles tables")
    print("[*] Backup has been created. Proceeding with truncation...")
    
    try:
        # Delete in reverse FK dependency order: subjects -> academic_terms -> student_profiles -> users
        
        # Delete subjects first (has FK to academic_terms)
        print("\n[*] Deleting all records from subjects...")
        try:
            result = session.execute(text('DELETE FROM subjects'))
            session.commit()
            print(f"    [+] Deleted {result.rowcount} subject records")
        except Exception as e:
            # Table might not exist or be empty
            print(f"    [*] Subjects deletion: {e}")
            session.rollback()
        
        # Delete academic_terms (has FK to users)
        print("\n[*] Deleting all records from academic_terms...")
        try:
            result = session.execute(text('DELETE FROM academic_terms'))
            session.commit()
            print(f"    [+] Deleted {result.rowcount} academic term records")
        except Exception as e:
            # Table might not exist or be empty
            print(f"    [*] Academic terms deletion: {e}")
            session.rollback()
        
        # Delete student_profiles (has FK to users)
        print("\n[*] Deleting all records from student_profiles...")
        result = session.execute(text('DELETE FROM student_profiles'))
        session.commit()
        print(f"    [+] Deleted {result.rowcount} student profile records")
        
        # Delete users
        print("\n[*] Deleting all records from users...")
        result = session.execute(text('DELETE FROM users'))
        session.commit()
        print(f"    [+] Deleted {result.rowcount} user records")
        
        # Verify tables are empty
        user_count = session.query(User).count()
        profile_count = session.query(StudentProfile).count()
        
        if user_count == 0 and profile_count == 0:
            print(f"\n[+] Tables successfully truncated")
            print(f"    - Users: {user_count}")
            print(f"    - Student Profiles: {profile_count}")
        else:
            print(f"[!] ERROR: Tables not empty after truncation!")
            print(f"    - Users: {user_count}")
            print(f"    - Student Profiles: {profile_count}")
            sys.exit(1)
        
    except Exception as e:
        print(f"[!] ERROR during truncation: {e}")
        session.rollback()
        sys.exit(1)


def import_ieee_csv(session, df):
    """Import IEEE CSV data into users and student_profiles tables."""
    print("\n" + "=" * 80)
    print("STEP 3: IMPORTING IEEE CSV DATA")
    print("=" * 80)
    
    print(f"\n[*] Importing {len(df):,} records from IEEE CSV...")
    
    users_created = 0
    profiles_created = 0
    errors = []
    
    try:
        for idx, row in df.iterrows():
            try:
                # Create User record
                user = User(
                    student_id=row['student_id'],
                    email=row['email'],
                    password_hash='',  # Empty - to be regenerated later
                    is_active=True
                )
                session.add(user)
                session.flush()  # Flush to get user.id
                users_created += 1
                
                # Create StudentProfile record
                profile = StudentProfile(
                    user_id=user.id,
                    name=row['name'],
                    branch=row['department'],  # IEEE CSV uses 'department'
                    semester=int(row['current_semester']),  # IEEE CSV uses 'current_semester'
                    interests=None
                )
                session.add(profile)
                profiles_created += 1
                
                # Commit in batches of 1000 for performance
                if (idx + 1) % 1000 == 0:
                    session.commit()
                    print(f"    Progress: {idx + 1:,}/{len(df):,} records imported...")
                    
            except Exception as e:
                errors.append(f"Row {idx + 1}: {str(e)}")
                session.rollback()
                if len(errors) >= 10:
                    print(f"[!] Too many errors ({len(errors)}), stopping import")
                    break
        
        # Final commit
        session.commit()
        
        print(f"\n[+] Import Summary:")
        print(f"    - Users created: {users_created:,}")
        print(f"    - Student profiles created: {profiles_created:,}")
        
        if errors:
            print(f"\n[!] Errors encountered: {len(errors)}")
            for error in errors[:5]:
                print(f"    - {error}")
        
        if users_created != len(df):
            print(f"\n[!] WARNING: Expected {len(df)} users but created {users_created}")
        
    except Exception as e:
        print(f"\n[!] ERROR during import: {e}")
        session.rollback()
        import traceback
        traceback.print_exc()
        sys.exit(1)


def verify_import(session, expected_count):
    """Verify imported data."""
    print("\n" + "=" * 80)
    print("STEP 4: VERIFYING IMPORTED DATA")
    print("=" * 80)
    
    user_count = session.query(User).count()
    profile_count = session.query(StudentProfile).count()
    
    print(f"\n[*] Final Database Counts (After Refresh):")
    print(f"    - Users: {user_count:,}")
    print(f"    - Student Profiles: {profile_count:,}")
    print(f"    - Expected: {expected_count:,}")
    
    # Check for orphaned records
    orphaned_profiles = session.execute(text('''
        SELECT COUNT(*) FROM student_profiles sp 
        LEFT JOIN users u ON sp.user_id = u.id 
        WHERE u.id IS NULL
    ''')).scalar()
    
    orphaned_users = session.execute(text('''
        SELECT COUNT(*) FROM users u 
        LEFT JOIN student_profiles sp ON u.id = sp.user_id 
        WHERE sp.id IS NULL
    ''')).scalar()
    
    print(f"\n[*] Data Integrity Checks:")
    print(f"    - Orphaned profiles (no user): {orphaned_profiles}")
    print(f"    - Users without profile: {orphaned_users}")
    
    # Display sample records
    print(f"\n[*] Sample Records (First 3):")
    sample_users = session.query(User).limit(3).all()
    for user in sample_users:
        profile = user.profile
        print(f"    - {user.student_id} | {user.email} | {profile.name if profile else 'NO PROFILE'} | {profile.branch if profile else 'N/A'}")
    
    print(f"\n[*] Sample Records (Last 3):")
    total_users = session.query(User).count()
    last_users = session.query(User).offset(total_users - 3).limit(3).all()
    for user in last_users:
        profile = user.profile
        print(f"    - {user.student_id} | {user.email} | {profile.name if profile else 'NO PROFILE'} | {profile.branch if profile else 'N/A'}")
    
    # Verification status
    if user_count == expected_count and profile_count == expected_count and orphaned_profiles == 0 and orphaned_users == 0:
        print(f"\n[+] [OK] Data refresh verification PASSED")
        return True
    else:
        print(f"\n[!] [FAILED] Data refresh verification FAILED")
        if user_count != expected_count:
            print(f"    - User count mismatch: expected {expected_count}, got {user_count}")
        if profile_count != expected_count:
            print(f"    - Profile count mismatch: expected {expected_count}, got {profile_count}")
        if orphaned_profiles > 0:
            print(f"    - Found {orphaned_profiles} orphaned profiles")
        if orphaned_users > 0:
            print(f"    - Found {orphaned_users} users without profiles")
        return False


def main():
    """Main data refresh function."""
    print("=" * 80)
    print("DATA REFRESH: Replace Student Data with IEEE CSV")
    print("=" * 80)
    print(f"\nStarted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Verify CSV file
        df = verify_csv_exists()
        expected_count = len(df)
        
        # Create database session
        session, engine = get_db_session()
        
        # Show current counts
        current_users, current_profiles = show_current_counts(session)
        
        # Step 1: Backup existing data
        if current_users > 0 or current_profiles > 0:
            run_backup()
        else:
            print("\n[*] Database is empty, skipping backup")
        
        # Step 2: Truncate tables
        truncate_tables(session, engine)
        
        # Step 3: Import IEEE CSV
        import_ieee_csv(session, df)
        
        # Step 4: Verify import
        verification_passed = verify_import(session, expected_count)
        
        # Final summary
        print("\n" + "=" * 80)
        print("DATA REFRESH COMPLETE")
        print("=" * 80)
        
        if verification_passed:
            print(f"\n[+] [SUCCESS] Data refresh completed successfully!")
            print(f"\n[!] IMPORTANT NEXT STEPS:")
            print(f"    1. Regenerate password hashes:")
            print(f"       cd backend")
            print(f"       python scripts\\generate_passwords_from_student_id.py")
            print(f"    2. Test authentication with a sample student_id")
            print(f"    3. Verify backend API endpoints are functional")
        else:
            print(f"\n[!] Data refresh completed with warnings")
            print(f"    Please review the verification results above")
        
        print(f"\n[+] Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        session.close()
        
    except Exception as e:
        print(f"\n[!] FATAL ERROR during data refresh: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
