#!/usr/bin/env python3
"""
Generate deterministic passwords for synthetic users.

This script generates passwords using the pattern: student_id + "@123"
and updates the password_hash field in the users table.

Example logins after running this script:
    Email: priya.sharma@example.com
    Password: STU001@123

SAFETY: Requires environment variable ALLOW_PASSWORD_RESET=true to run.

Usage:
    # Windows
    $env:ALLOW_PASSWORD_RESET="true"; python backend/scripts/generate_passwords_from_student_id.py

    # Linux/Mac
    ALLOW_PASSWORD_RESET=true python backend/scripts/generate_passwords_from_student_id.py

NOTE: student_id is NOT stored in the database schema. This script reads
the student_id from SATA_student_main_info_10k.csv and maps it to users
via their email addresses.
"""

import csv
import os
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from passlib.context import CryptContext
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.user import User

# Password hashing context (matches auth configuration)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def generate_passwords():
    """Generate and update passwords for all users based on student_id."""
    
    # Safety check: require environment variable
    if os.getenv("ALLOW_PASSWORD_RESET") != "true":
        print("=" * 70)
        print("❌ SAFETY CHECK FAILED")
        print("=" * 70)
        print("\nThis script will reset ALL user passwords in the database.")
        print("To proceed, set the environment variable ALLOW_PASSWORD_RESET=true\n")
        print("Windows PowerShell:")
        print('  $env:ALLOW_PASSWORD_RESET="true"; python backend/scripts/generate_passwords_from_student_id.py\n')
        print("Linux/Mac:")
        print('  ALLOW_PASSWORD_RESET=true python backend/scripts/generate_passwords_from_student_id.py\n')
        print("=" * 70)
        sys.exit(1)
    
    # Paths
    backend_dir = Path(__file__).parent.parent
    csv_path = backend_dir / "data" / "SATA_student_main_info_10k.csv"
    
    # Validate CSV exists
    if not csv_path.exists():
        print(f"❌ Error: Student info CSV not found: {csv_path}")
        print("\nThis file is required to map student IDs to email addresses.")
        sys.exit(1)
    
    # Create database session
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    updated_count = 0
    skipped_count = 0
    error_count = 0
    
    print("=" * 70)
    print("GENERATING DETERMINISTIC PASSWORDS")
    print("=" * 70)
    print(f"\nReading student data from: {csv_path.name}")
    
    try:
        # Read CSV and build student_id -> email mapping
        student_data = []
        with open(csv_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            # Validate columns
            fieldnames = reader.fieldnames or []
            if 'student_id' not in fieldnames or 'email' not in fieldnames:
                print(f"❌ Error: CSV must contain 'student_id' and 'email' columns")
                print(f"Found columns: {fieldnames}")
                db.close()
                sys.exit(1)
            
            for row in reader:
                student_id = row.get('student_id', '').strip()
                email = row.get('email', '').strip()
                
                if student_id and email:
                    student_data.append({
                        'student_id': student_id,
                        'email': email
                    })
        
        print(f"Loaded {len(student_data)} student records from CSV\n")
        print("Processing passwords...\n")
        
        # Process each student
        for idx, student in enumerate(student_data, start=1):
            try:
                student_id = student['student_id']
                email = student['email']
                
                # Generate deterministic password: student_id + "@123"
                raw_password = f"{student_id}@123"
                
                # Find user by email
                user = db.query(User).filter(User.email == email).first()
                
                if user:
                    # Hash password and update
                    user.password_hash = hash_password(raw_password)
                    updated_count += 1
                    
                    # Progress update every 100 users
                    if updated_count % 100 == 0:
                        print(f"  Processed {updated_count} users...")
                else:
                    skipped_count += 1
                    
            except Exception as e:
                error_count += 1
                if error_count <= 5:  # Only show first 5 errors
                    print(f"  Warning: Error processing student {student_id}: {str(e)[:100]}")
        
        # Commit all changes in one batch
        db.commit()
        
        # Print results
        print("\n" + "=" * 70)
        print("✅ PASSWORD GENERATION COMPLETE")
        print("=" * 70)
        print(f"\n  Updated:  {updated_count} users")
        print(f"  Skipped:  {skipped_count} users (not found in database)")
        if error_count > 0:
            print(f"  Errors:   {error_count} records")
        print("\n" + "=" * 70)
        print("\nLogin Format:")
        print("  Email:    [user email from database]")
        print("  Password: [student_id]@123")
        print("\nExample:")
        print("  Email:    priya.sharma@example.com")
        print("  Password: STU001@123")
        print("=" * 70 + "\n")
        
        # Verify password hash format
        sample_user = db.query(User).first()
        if sample_user and sample_user.password_hash.startswith("$2b$"):
            print("✅ Verification: Password hashes use bcrypt format ($2b$)\n")
        else:
            print("⚠️  Warning: Password hash format may be incorrect\n")
        
    except FileNotFoundError:
        print(f"❌ Error: File not found: {csv_path}")
        db.close()
        sys.exit(1)
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.close()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    generate_passwords()
