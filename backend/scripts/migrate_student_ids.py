#!/usr/bin/env python3
"""
Migrate student_id data to users table.

This script reads the CSV file to get the email -> student_id mapping
and populates the student_id column in the users table.
"""
import sys
import csv
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

def migrate_student_ids():
    """Populate student_id column from CSV data."""
    
    print("=" * 70)
    print("MIGRATING STUDENT IDs TO USERS TABLE")
    print("=" * 70)
    
    # Paths
    backend_dir = Path(__file__).parent.parent
    csv_path = backend_dir / "data" / "user_credentials_10k_common_password.csv"
    
    if not csv_path.exists():
        print(f"\n❌ Error: CSV file not found: {csv_path}")
        print("This file is required to map emails to student IDs.")
        sys.exit(1)
    
    # Create database session
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # Read CSV and build username -> student_id mapping
        print(f"\n[*] Reading student data from: {csv_path.name}")
        username_to_student_id = {}
        
        with open(csv_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                student_id = row.get('student_id', '').strip()
                username = row.get('username', '').strip()
                
                if student_id and username:
                    username_to_student_id[username] = student_id
        
        print(f"    Loaded {len(username_to_student_id):,} student ID mappings from CSV")
        
        # Get all users from database
        print("\n[*] Updating users...")
        result = db.execute(text("SELECT id, email FROM users"))
        users = result.fetchall()
        
        updated_count = 0
        not_found_count = 0
        
        for user_id, email in users:
            # Extract username from email (format: username@student.edu)
            username = email.replace('@student.edu', '')
            student_id = username_to_student_id.get(username)
            
            if student_id:
                db.execute(
                    text("UPDATE users SET student_id = :student_id WHERE id = :user_id"),
                    {"student_id": student_id, "user_id": user_id}
                )
                updated_count += 1
            else:
                not_found_count += 1
                print(f"    Warning: No student_id found for email: {email}")
        
        # Commit changes
        db.commit()
        
        # Print results
        print("\n" + "=" * 70)
        print("✅ MIGRATION COMPLETE")
        print("=" * 70)
        print(f"\n  Updated:   {updated_count} users")
        print(f"  Not found: {not_found_count} users (no matching student_id in CSV)")
        print("\n" + "=" * 70)
        
        # Verify
        result = db.execute(text("SELECT COUNT(*) FROM users WHERE student_id IS NOT NULL"))
        count = result.scalar()
        print(f"\n✅ Verification: {count} users have student_id populated")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    migrate_student_ids()
