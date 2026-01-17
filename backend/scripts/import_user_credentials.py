"""
Script to import user credentials from CSV and hash passwords.

Usage:
    python backend/scripts/import_user_credentials.py

This script:
1. Reads user_credentials_10k_common_password.csv
2. Finds users by email
3. Hashes passwords with bcrypt
4. Updates users.password_hash in database
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

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)

def import_credentials(csv_path: str):
    """Import credentials from CSV and update user passwords."""
    
    # Create database session
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    updated_count = 0
    skipped_count = 0
    error_count = 0
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            # Check columns
            fieldnames = reader.fieldnames or []
            print(f"CSV Columns: {fieldnames}")
            
            # Detect column format
            if 'email' in fieldnames and 'password' in fieldnames:
                print("\n✓ Detected format: email, password (will hash passwords)")
                use_email_password = True
            elif 'student_id' in fieldnames and 'password_hash' in fieldnames:
                print("\n✓ Detected format: student_id, password_hash (pre-hashed)")
                use_email_password = False
                
                # Load student info to map student_id -> email
                backend_dir = Path(csv_path).parent.parent
                student_info_csv = backend_dir / "data" / "SATA_student_main_info_10k.csv"
                
                print(f"Loading student info from: {student_info_csv}")
                student_id_to_email = {}
                
                try:
                    with open(student_info_csv, 'r', encoding='utf-8') as f:
                        info_reader = csv.DictReader(f)
                        for row in info_reader:
                            student_id = row.get('student_id', '').strip()
                            email = row.get('email', '').strip()
                            if student_id and email:
                                student_id_to_email[student_id] = email
                    
                    print(f"Loaded {len(student_id_to_email)} student ID to email mappings\n")
                    
                except FileNotFoundError:
                    print(f"❌ Error: Student info CSV not found: {student_info_csv}")
                    print("This file is required to map student IDs to emails.")
                    db.close()
                    return
            else:
                print(f"\n❌ Error: Unexpected CSV format")
                print(f"Expected columns: 'email' and 'password' OR 'student_id' and 'password_hash'")
                print(f"Found columns: {fieldnames}")
                db.close()
                return
            
            print("Processing credentials...\n")
            
            for idx, row in enumerate(reader, start=2):  # Start at 2 (1 is header)
                try:
                    if use_email_password:
                        # Format: email, password
                        email = row.get('email', '').strip()
                        password = row.get('password', '').strip()
                        
                        if not email or not password:
                            skipped_count += 1
                            continue
                        
                        # Find user by email
                        user = db.query(User).filter(User.email == email).first()
                        
                        if user:
                            # Hash the password and update
                            user.password_hash = hash_password(password)
                            updated_count += 1
                            
                            if updated_count % 100 == 0:
                                print(f"Processed {updated_count} users...")
                        else:
                            skipped_count += 1
                    
                    else:
                        # Format: student_id, password_hash
                        student_id = row.get('student_id', '').strip()
                        password_hash = row.get('password_hash', '').strip()
                        
                        if not student_id or not password_hash:
                            skipped_count += 1
                            continue
                        
                        # Map student_id to email
                        email = student_id_to_email.get(student_id)
                        if not email:
                            skipped_count += 1
                            continue
                        
                        # Find user by email
                        user = db.query(User).filter(User.email == email).first()
                        
                        if user:
                            # Use the password_hash from CSV directly (already hashed)
                            user.password_hash = password_hash
                            updated_count += 1
                            
                            if updated_count % 100 == 0:
                                print(f"Processed {updated_count} users...")
                        else:
                            skipped_count += 1
                
                except Exception as e:
                    error_count += 1
                    if error_count <= 5:  # Only show first 5 errors
                        print(f"Warning: Error processing row {idx}: {str(e)[:100]}")
            
            # Commit all changes
            db.commit()
            print(f"\n{'='*50}")
            print(f"✅ Import complete!")
            print(f"{'='*50}")
            print(f"   Updated: {updated_count} users")
            print(f"   Skipped: {skipped_count} rows")
            if error_count > 0:
                print(f"   Errors:  {error_count} rows")
            print(f"{'='*50}\n")
            
    except FileNotFoundError:
        print(f"❌ Error: File not found: {csv_path}")
        print("\nPlease ensure the CSV file exists at:")
        print(f"   {Path(csv_path).absolute()}")
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    # CSV path - relative to backend directory
    backend_dir = Path(__file__).parent.parent
    csv_path = backend_dir / "data" / "user_credentials_10k_common_password.csv"
    
    if not csv_path.exists():
        print(f"❌ Credentials CSV not found: {csv_path}")
        print("\nExpected columns: email, password")
        print("(Passwords will be hashed using bcrypt)")
        print("\nPlease place the CSV file at:")
        print(f"   {csv_path.absolute()}")
        sys.exit(1)
    
    import_credentials(str(csv_path))
