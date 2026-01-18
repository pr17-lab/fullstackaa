#!/usr/bin/env python3
"""
Rollback student data from backup files.
Use this script to restore data if the refresh operation fails or needs to be reversed.
"""

import sys
from pathlib import Path
from datetime import datetime
import re

# Add parent directory to path to import app modules
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.models import User, StudentProfile

# Database connection
DATABASE_URL = "postgresql://studentadmin:studentpass123@localhost:5432/student_tracker"

# Backup directory
BACKUP_DIR = backend_dir / "backups"


def get_db_session():
    """Create database session."""
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal(), engine


def list_available_backups():
    """List all available backup timestamps."""
    if not BACKUP_DIR.exists():
        print(f"[!] Backup directory not found: {BACKUP_DIR}")
        return []
    
    # Find all backup info files
    info_files = list(BACKUP_DIR.glob("backup_info_*.txt"))
    
    if not info_files:
        print(f"[!] No backup info files found in {BACKUP_DIR}")
        return []
    
    backups = []
    for info_file in sorted(info_files, reverse=True):
        # Extract timestamp from filename
        match = re.search(r'backup_info_(\d{8}_\d{6})\.txt', info_file.name)
        if match:
            timestamp = match.group(1)
            backups.append({
                'timestamp': timestamp,
                'info_file': info_file
            })
    
    return backups


def display_backup_info(info_file):
    """Display contents of backup info file."""
    with open(info_file, 'r') as f:
        print(f.read())


def verify_backup_files(timestamp):
    """Verify that all required backup files exist."""
    users_sql = BACKUP_DIR / f"users_backup_{timestamp}.sql"
    profiles_sql = BACKUP_DIR / f"student_profiles_backup_{timestamp}.sql"
    
    missing_files = []
    if not users_sql.exists():
        missing_files.append(users_sql.name)
    if not profiles_sql.exists():
        missing_files.append(profiles_sql.name)
    
    if missing_files:
        print(f"[!] ERROR: Missing backup files:")
        for file in missing_files:
            print(f"    - {file}")
        return False
    
    return True


def truncate_current_data(session):
    """Delete all current data from tables."""
    print("\n[*] Deleting current data from tables...")
    
    try:
        # Delete student_profiles first (has FK to users)
        result = session.execute(text('DELETE FROM student_profiles'))
        profiles_deleted = result.rowcount
        session.commit()
        print(f"    [+] Deleted {profiles_deleted} student profile records")
        
        # Delete users
        result = session.execute(text('DELETE FROM users'))
        users_deleted = result.rowcount
        session.commit()
        print(f"    [+] Deleted {users_deleted} user records")
        
        # Verify tables are empty
        user_count = session.query(User).count()
        profile_count = session.query(StudentProfile).count()
        
        if user_count == 0 and profile_count == 0:
            print(f"    [+] Tables successfully cleared")
            return True
        else:
            print(f"    [!] ERROR: Tables not empty after deletion!")
            return False
            
    except Exception as e:
        print(f"[!] ERROR during truncation: {e}")
        session.rollback()
        return False


def restore_from_sql(engine, sql_file, table_name):
    """Restore data from SQL backup file."""
    print(f"\n[*] Restoring {table_name} from {sql_file.name}...")
    
    try:
        # Read SQL file
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # Count INSERT statements
        insert_count = sql_content.count('INSERT INTO')
        print(f"    [*] Found {insert_count} INSERT statements")
        
        # Execute SQL statements
        with engine.begin() as conn:
            # Split by semicolon and execute each statement
            statements = [s.strip() for s in sql_content.split(';') if s.strip() and 'INSERT INTO' in s]
            
            for i, statement in enumerate(statements):
                try:
                    conn.execute(text(statement + ';'))
                    if (i + 1) % 1000 == 0:
                        print(f"    Progress: {i + 1}/{len(statements)} records restored...")
                except Exception as e:
                    print(f"    [!] Error executing statement {i + 1}: {e}")
                    # Continue with next statement
        
        print(f"    [+] Restoration complete for {table_name}")
        return True
        
    except Exception as e:
        print(f"[!] ERROR restoring {table_name}: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_restoration(session, expected_users, expected_profiles):
    """Verify restored data."""
    print("\n" + "=" * 80)
    print("VERIFYING RESTORATION")
    print("=" * 80)
    
    user_count = session.query(User).count()
    profile_count = session.query(StudentProfile).count()
    
    print(f"\n[*] Restored Row Counts:")
    print(f"    - Users: {user_count:,} (expected: {expected_users:,})")
    print(f"    - Student Profiles: {profile_count:,} (expected: {expected_profiles:,})")
    
    # Display sample records
    print(f"\n[*] Sample Restored Records (First 3):")
    sample_users = session.query(User).limit(3).all()
    for user in sample_users:
        profile = user.profile
        print(f"    - {user.student_id} | {user.email} | {profile.name if profile else 'NO PROFILE'}")
    
    if user_count == expected_users and profile_count == expected_profiles:
        print(f"\n[+] ✓ Rollback verification PASSED")
        return True
    else:
        print(f"\n[!] ✗ Rollback verification FAILED - count mismatch")
        return False


def main():
    """Main rollback function."""
    print("=" * 80)
    print("ROLLBACK STUDENT DATA FROM BACKUP")
    print("=" * 80)
    
    # List available backups
    print("\n[*] Searching for available backups...")
    backups = list_available_backups()
    
    if not backups:
        print("[!] No backups found. Cannot proceed with rollback.")
        sys.exit(1)
    
    print(f"\n[*] Found {len(backups)} backup(s):")
    for i, backup in enumerate(backups, 1):
        print(f"    {i}. Timestamp: {backup['timestamp']}")
    
    # Allow user to specify backup timestamp or use most recent
    if len(sys.argv) > 1:
        timestamp = sys.argv[1]
        print(f"\n[*] Using specified backup timestamp: {timestamp}")
    else:
        # Use most recent backup
        timestamp = backups[0]['timestamp']
        print(f"\n[*] Using most recent backup: {timestamp}")
    
    # Display backup info
    info_file = BACKUP_DIR / f"backup_info_{timestamp}.txt"
    if info_file.exists():
        print("\n" + "=" * 80)
        print("BACKUP INFORMATION")
        print("=" * 80)
        display_backup_info(info_file)
    
    # Verify backup files exist
    if not verify_backup_files(timestamp):
        sys.exit(1)
    
    users_sql = BACKUP_DIR / f"users_backup_{timestamp}.sql"
    profiles_sql = BACKUP_DIR / f"student_profiles_backup_{timestamp}.sql"
    
    # Get expected counts from backup info
    expected_users = 0
    expected_profiles = 0
    if info_file.exists():
        with open(info_file, 'r') as f:
            content = f.read()
            match = re.search(r'Users: (\d+)', content)
            if match:
                expected_users = int(match.group(1))
            match = re.search(r'Student Profiles: (\d+)', content)
            if match:
                expected_profiles = int(match.group(1))
    
    print("\n" + "=" * 80)
    print("STARTING ROLLBACK PROCESS")
    print("=" * 80)
    print(f"\n[!] WARNING: This will DELETE all current data and restore from backup")
    print(f"[!] Backup timestamp: {timestamp}")
    
    try:
        # Create database session
        session, engine = get_db_session()
        
        # Step 1: Truncate current data
        print("\n" + "=" * 80)
        print("STEP 1: CLEARING CURRENT DATA")
        print("=" * 80)
        if not truncate_current_data(session):
            print("[!] Failed to clear current data")
            sys.exit(1)
        
        # Step 2: Restore users table
        print("\n" + "=" * 80)
        print("STEP 2: RESTORING USERS TABLE")
        print("=" * 80)
        if not restore_from_sql(engine, users_sql, "users"):
            print("[!] Failed to restore users table")
            sys.exit(1)
        
        # Step 3: Restore student_profiles table
        print("\n" + "=" * 80)
        print("STEP 3: RESTORING STUDENT_PROFILES TABLE")
        print("=" * 80)
        if not restore_from_sql(engine, profiles_sql, "student_profiles"):
            print("[!] Failed to restore student_profiles table")
            sys.exit(1)
        
        # Step 4: Verify restoration
        verification_passed = verify_restoration(session, expected_users, expected_profiles)
        
        # Final summary
        print("\n" + "=" * 80)
        print("ROLLBACK COMPLETE")
        print("=" * 80)
        
        if verification_passed:
            print(f"\n[+] ✓ Rollback completed successfully!")
            print(f"    Data has been restored from backup: {timestamp}")
        else:
            print(f"\n[!] Rollback completed with warnings")
            print(f"    Please verify the data manually")
        
        session.close()
        
    except Exception as e:
        print(f"\n[!] FATAL ERROR during rollback: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    print("\nUsage: python rollback_student_data.py [timestamp]")
    print("       If timestamp is not provided, most recent backup will be used\n")
    main()
