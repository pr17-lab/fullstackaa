#!/usr/bin/env python3
"""
Regenerate passwords for all users based on their student_id in the database.

This script reads student_id directly from the users table and generates
passwords using the pattern: student_id + "@123"
"""
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from passlib.context import CryptContext
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.user import User

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)

def regenerate_all_passwords():
    """Regenerate passwords for all users with student_id."""
    
    print("=" * 70)
    print("REGENERATING PASSWORDS FROM DATABASE STUDENT_IDs")
    print("=" * 70)
    
    # Create database session
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # Get all users with student_id
        users = db.query(User).filter(User.student_id.isnot(None)).all()
        
        print(f"\n[*] Found {len(users):,} users with student_id")
        print("[*] Regenerating passwords...\n")
        
        updated_count = 0
        
        for idx, user in enumerate(users, start=1):
            try:
                # Generate password: student_id@123
                raw_password = f"{user.student_id}@123"
                
                # Hash password
                user.password_hash = hash_password(raw_password)
                updated_count += 1
                
                # Progress update every 1000 users
                if updated_count % 1000 == 0:
                    print(f"  Processed {updated_count:,} users...")
                    
            except Exception as e:
                print(f"  Error processing user {user.student_id}: {str(e)[:100]}")
        
        # Commit all changes
        db.commit()
        
        # Print results
        print("\n" + "=" * 70)
        print("✅ PASSWORD REGENERATION COMPLETE")
        print("=" * 70)
        print(f"\n  Updated:  {updated_count:,} users")
        print("\n" + "=" * 70)
        print("\nLogin Format:")
        print("  Student ID: [student_id from database]")
        print("  Password:   [student_id]@123")
        print("\nExample:")
        print("  Student ID: S00001")
        print("  Password:   S00001@123")
        print("=" * 70 + "\n")
        
        # Verify password hash format
        sample_user = db.query(User).filter(User.student_id.isnot(None)).first()
        if sample_user and sample_user.password_hash.startswith("$2b$"):
            print("✅ Verification: Password hashes use bcrypt format ($2b$)\n")
        else:
            print("⚠️  Warning: Password hash format may be incorrect\n")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.close()
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    regenerate_all_passwords()
