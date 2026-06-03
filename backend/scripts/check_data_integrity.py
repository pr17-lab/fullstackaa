#!/usr/bin/env python3
"""
Database Integrity Checker

Runs comprehensive integrity checks on the student database to detect:
- Orphaned records (profiles without users)
- Duplicate emails in users table
- Missing foreign key relationships
- Data consistency issues

Usage:
    python backend/scripts/check_data_integrity.py
"""

import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models import User, StudentProfile


def check_integrity():
    """Run comprehensive data integrity checks."""
    
    # Create database session
    engine = create_engine(settings.DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    print(f"\n{'='*70}")
    print("DATABASE INTEGRITY CHECK")
    print(f"{'='*70}\n")
    
    issues_found = False
    
    try:
        # 1. Check for orphaned student profiles
        print("[CHECK] Checking for orphaned student profiles...")
        orphaned_profiles = session.execute(text('''
            SELECT COUNT(*) FROM student_profiles sp 
            LEFT JOIN users u ON sp.user_id = u.id 
            WHERE u.id IS NULL
        ''')).scalar()
        
        if orphaned_profiles > 0:
            issues_found = True
            print(f"   [FAIL] Found {orphaned_profiles} student profiles without users")
            
            # Show sample orphaned profiles
            sample = session.execute(text('''
                SELECT sp.id, sp.name, sp.user_id 
                FROM student_profiles sp 
                LEFT JOIN users u ON sp.user_id = u.id 
                WHERE u.id IS NULL
                LIMIT 5
            ''')).fetchall()
            
            print("   Sample orphaned profiles:")
            for row in sample:
                print(f"      Profile ID: {row[0]}, Name: {row[1]}, Invalid User ID: {row[2]}")
        else:
            print("   [PASS] No orphaned student profiles")
        

        # 4. Check for duplicate emails
        print("\n[CHECK] Checking for duplicate emails...")
        duplicate_emails = session.execute(text('''
            SELECT email, COUNT(*) as count 
            FROM users 
            GROUP BY email 
            HAVING COUNT(*) > 1
        ''')).fetchall()
        
        if len(duplicate_emails) > 0:
            issues_found = True
            print(f"   [FAIL] Found {len(duplicate_emails)} duplicate email addresses")
            print("   Sample duplicates:")
            for row in duplicate_emails[:5]:
                print(f"      {row[0]} (appears {row[1]} times)")
        else:
            print("   [PASS] No duplicate emails")
        
        # 5. Check for duplicate student IDs
        print("\n[CHECK] Checking for duplicate student IDs...")
        duplicate_student_ids = session.execute(text('''
            SELECT student_id, COUNT(*) as count 
            FROM users 
            WHERE student_id IS NOT NULL
            GROUP BY student_id 
            HAVING COUNT(*) > 1
        ''')).fetchall()
        
        if len(duplicate_student_ids) > 0:
            issues_found = True
            print(f"   [FAIL] Found {len(duplicate_student_ids)} duplicate student IDs")
            print("   Sample duplicates:")
            for row in duplicate_student_ids[:5]:
                print(f"      {row[0]} (appears {row[1]} times)")
        else:
            print("   [PASS] No duplicate student IDs")
        
        # 6. Check for users without profiles
        print("\n[CHECK] Checking for users without student profiles...")
        users_without_profiles = session.execute(text('''
            SELECT COUNT(*) FROM users u 
            LEFT JOIN student_profiles sp ON u.id = sp.user_id 
            WHERE sp.id IS NULL
        ''')).scalar()
        
        if users_without_profiles > 0:
            issues_found = True
            print(f"   [WARN] Found {users_without_profiles} users without student profiles")
            
            # Show sample users without profiles
            sample = session.execute(text('''
                SELECT u.id, u.email, u.student_id 
                FROM users u 
                LEFT JOIN student_profiles sp ON u.id = sp.user_id 
                WHERE sp.id IS NULL
                LIMIT 5
            ''')).fetchall()
            
            print("   Sample users without profiles:")
            for row in sample:
                print(f"      User ID: {row[0]}, Email: {row[1]}, Student ID: {row[2]}")
        else:
            print("   [PASS] All users have student profiles")
        
        # 7. Check for null password hashes
        print("\n[CHECK] Checking for users with null password hashes...")
        null_passwords = session.execute(text('''
            SELECT COUNT(*) FROM users 
            WHERE password_hash IS NULL OR password_hash = ''
        ''')).scalar()
        
        if null_passwords > 0:
            issues_found = True
            print(f"   [WARN] Found {null_passwords} users with null/empty password hashes")
        else:
            print("   [PASS] All users have password hashes")
        
        # Summary
        print(f"\n{'='*70}")
        print("INTEGRITY CHECK SUMMARY")
        print(f"{'='*70}\n")
        
        total_users = session.query(User).count()
        total_profiles = session.query(StudentProfile).count()
        
        print(f"Database Counts:")
        print(f"   Users:            {total_users}")
        print(f"   Student Profiles: {total_profiles}")
        
        print(f"\nIntegrity Issues:")
        print(f"   Orphaned Profiles: {orphaned_profiles}")
        print(f"   Duplicate Emails:  {len(duplicate_emails)}")
        print(f"   Duplicate IDs:     {len(duplicate_student_ids)}")
        print(f"   Users w/o Profile: {users_without_profiles}")
        print(f"   Null Passwords:    {null_passwords}")
        
        if issues_found:
            print(f"\n[FAIL] INTEGRITY CHECK FAILED - Issues found")
            print(f"{'='*70}\n")
            return False
        else:
            print(f"\n[PASS] INTEGRITY CHECK PASSED - Database is clean")
            print(f"{'='*70}\n")
            return True
        
    except Exception as e:
        print(f"\n[ERROR] Error during integrity check: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        session.close()


def main():
    """Main function."""
    is_clean = check_integrity()
    sys.exit(0 if is_clean else 1)


if __name__ == "__main__":
    main()
