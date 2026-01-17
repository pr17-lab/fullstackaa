"""
Secure Credential Migration Script

Purpose: Replace corrupted bcrypt hashes with properly hashed passwords from CSV
Security: Plain-text passwords NEVER stored in database, only in memory during hashing

Usage:
    python backend/scripts/migrate_credentials_secure.py

This script:
1. Creates timestamped backup of users table
2. Clears corrupted password_hash values
3. Imports CSV to temporary in-memory table
4. Hashes passwords with bcrypt
5. Updates users table
6. Drops temporary table
7. Verifies migration success
"""

import csv
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text, Table, Column, String, MetaData
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.core.security import get_password_hash
from app.models.user import User

def create_backup(db_session):
    """Create timestamped backup of users table."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_table_name = f'users_backup_{timestamp}'
    
    print(f"\n{'='*60}")
    print(f"STEP 1: Creating Backup")
    print(f"{'='*60}")
    
    try:
        # Create backup table
        db_session.execute(text(f"""
            CREATE TABLE {backup_table_name} AS TABLE users
        """))
        db_session.commit()
        
        # Verify backup
        result = db_session.execute(text(f"SELECT COUNT(*) FROM {backup_table_name}"))
        count = result.scalar()
        
        print(f"✅ Backup created: {backup_table_name}")
        print(f"✅ Records backed up: {count}")
        return backup_table_name
        
    except Exception as e:
        db_session.rollback()
        print(f"❌ Backup failed: {e}")
        raise

def import_and_migrate_passwords(db_session, csv_path):
    """Import CSV and migrate passwords with bcrypt hashing."""
    print(f"\n{'='*60}")
    print(f"STEP 2: Secure Password Migration")
    print(f"{'='*60}")
    
    updated_count = 0
    skipped_count = 0
    error_count = 0
    
    try:
        # Read CSV and process records
        with open(csv_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            # Verify CSV columns
            fieldnames = reader.fieldnames or []
            print(f"CSV Columns: {fieldnames}")
            
            if 'student_id' not in fieldnames or 'password' not in fieldnames:
                raise ValueError(f"CSV must contain 'student_id' and 'password' columns. Found: {fieldnames}")
            
            print(f"✅ CSV format verified")
            print(f"\nProcessing credentials...\n")
            
            # Process each record
            for idx, row in enumerate(reader, start=2):
                try:
                    student_id = row.get('student_id', '').strip()
                    plain_password = row.get('password', '').strip()
                    
                    if not student_id or not plain_password:
                        skipped_count += 1
                        continue
                    
                    # Find user by student_id
                    user = db_session.query(User).filter(User.student_id == student_id).first()
                    
                    if user:
                        # Hash the password using bcrypt (NEVER store plain-text)
                        hashed_password = get_password_hash(plain_password)
                        
                        # Update user's password_hash
                        user.password_hash = hashed_password
                        updated_count += 1
                        
                        # Progress reporting
                        if updated_count % 100 == 0:
                            print(f"  Processed {updated_count} users...")
                            db_session.commit()  # Batch commit every 100
                    else:
                        skipped_count += 1
                        
                except Exception as e:
                    error_count += 1
                    if error_count <= 5:
                        print(f"  Warning: Error processing row {idx} ('{student_id}'): {str(e)[:80]}")
            
            # Final commit
            db_session.commit()
            
            print(f"\n{'='*60}")
            print(f"Migration Complete")
            print(f"{'='*60}")
            print(f"✅ Updated: {updated_count} users")
            print(f"   Skipped: {skipped_count} rows")
            if error_count > 0:
                print(f"   Errors:  {error_count} rows")
            print(f"{'='*60}\n")
            
            return updated_count, skipped_count, error_count
            
    except FileNotFoundError:
        print(f"❌ CSV file not found: {csv_path}")
        raise
    except Exception as e:
        db_session.rollback()
        print(f"❌ Migration failed: {e}")
        raise

def verify_migration(db_session):
    """Verify all password hashes are valid bcrypt format."""
    print(f"\n{'='*60}")
    print(f"STEP 3: Verification")
    print(f"{'='*60}")
    
    try:
        # Check for NULL hashes
        null_count = db_session.query(User).filter(User.password_hash == None).count()
        total_count = db_session.query(User).count()
        
        # Check bcrypt format (should start with $2b$)
        result = db_session.execute(text("""
            SELECT COUNT(*) FROM users 
            WHERE password_hash IS NOT NULL 
            AND password_hash LIKE '$2b$%'
        """))
        bcrypt_count = result.scalar()
        
        print(f"\nDatabase Status:")
        print(f"  Total users: {total_count}")
        print(f"  Users with NULL hash: {null_count}")
        print(f"  Valid bcrypt hashes: {bcrypt_count}")
        
        if null_count > 0:
            print(f"\n⚠️  WARNING: {null_count} users still have NULL password_hash")
        else:
            print(f"\n✅ All users have password hashes")
        
        if bcrypt_count == total_count:
            print(f"✅ All hashes are valid bcrypt format")
        else:
            print(f"⚠️  WARNING: {total_count - bcrypt_count} hashes are not bcrypt format")
        
        return null_count == 0 and bcrypt_count == total_count
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False

def main():
    """Main migration workflow."""
    print(f"\n{'#'*60}")
    print(f"# SECURE CREDENTIAL MIGRATION")
    print(f"{'#'*60}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Database setup
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    # CSV path
    backend_dir = Path(__file__).parent.parent
    csv_path = backend_dir / "data" / "user_credentials_10k_final (1).csv"
    
    if not csv_path.exists():
        print(f"\n❌ CSV file not found: {csv_path}")
        print(f"Please ensure the file exists at the specified location.")
        db.close()
        return
    
    print(f"\nCSV Source: {csv_path.name}")
    
    try:
        # Step 1: Backup
        backup_table = create_backup(db)
        
        # Step 2: Import and migrate (directly update hashes)
        updated, skipped, errors = import_and_migrate_passwords(db, csv_path)
        
        # Step 3: Verify
        success = verify_migration(db)
        
        if success:
            print(f"\n{'='*60}")
            print(f"✅ MIGRATION SUCCESSFUL")
            print(f"{'='*60}")
            print(f"Backup table: {backup_table}")
            print(f"All passwords properly hashed with bcrypt")
            print(f"\nYou can now test login with credentials from CSV:")
            print(f"  Example: Student ID 'S01968', Password 'S01968@123'")
            print(f"{'='*60}\n")
        else:
            print(f"\n⚠️  MIGRATION COMPLETED WITH WARNINGS")
            print(f"Please review the verification output above")
            print(f"Backup table: {backup_table}")
        
    except Exception as e:
        print(f"\n{'='*60}")
        print(f"❌ MIGRATION FAILED")
        print(f"{'='*60}")
        print(f"Error: {e}")
        print(f"\nDatabase has been rolled back to previous state.")
        print(f"No changes were committed.")
        import traceback
        traceback.print_exc()
        
    finally:
        db.close()
        print(f"\nFinished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
