"""
Test Login Verification After Migration

Purpose: Verify bcrypt.checkpw works correctly after migration
Tests authentication with real credentials from CSV

Usage:
    python backend/scripts/test_login_verification.py
"""

import csv
import sys
import random
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.core.security import verify_password
from app.models.user import User

def test_login_authentication():
    """Test bcrypt verification with sample credentials from CSV."""
    
    print(f"\n{'='*60}")
    print(f"LOGIN AUTHENTICATION VERIFICATION")
    print(f"{'='*60}\n")
    
    # Database setup
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    # CSV path
    backend_dir = Path(__file__).parent.parent
    csv_path = backend_dir / "data" / "user_credentials_10k_final (1).csv"
    
    if not csv_path.exists():
        print(f"❌ CSV file not found: {csv_path}")
        db.close()
        return
    
    try:
        # Read CSV and sample random students
        with open(csv_path, 'r', encoding='utf-8') as file:
            reader = list(csv.DictReader(file))
            
            # Sample 10 random students (or all if less than 10)
            sample_size = min(10, len(reader))
            samples = random.sample(reader, sample_size)
            
            print(f"Testing {sample_size} random login attempts...\n")
            
            success_count = 0
            fail_count = 0
            
            for idx, row in enumerate(samples, 1):
                student_id = row.get('student_id', '').strip()
                plain_password = row.get('password', '').strip()
                
                if not student_id or not plain_password:
                    continue
                
                # Find user in database
                user = db.query(User).filter(User.student_id == student_id).first()
                
                if not user:
                    print(f"{idx}. ❌ Student {student_id}: NOT FOUND in database")
                    fail_count += 1
                    continue
                
                if not user.password_hash:
                    print(f"{idx}. ❌ Student {student_id}: NULL password hash")
                    fail_count += 1
                    continue
                
                # Verify password with bcrypt
                try:
                    is_valid = verify_password(plain_password, user.password_hash)
                    
                    if is_valid:
                        print(f"{idx}. ✅ Student {student_id} ({user.email[:20]}...): Login SUCCESS")
                        success_count += 1
                    else:
                        print(f"{idx}. ❌ Student {student_id}: Password verification FAILED")
                        fail_count += 1
                        
                except Exception as e:
                    print(f"{idx}. ❌ Student {student_id}: bcrypt error - {str(e)[:50]}")
                    fail_count += 1
            
            # Summary
            print(f"\n{'='*60}")
            print(f"TEST SUMMARY")
            print(f"{'='*60}")
            print(f"Total Tests:     {sample_size}")
            print(f"✅ Successful:   {success_count}")
            print(f"❌ Failed:       {fail_count}")
            print(f"Success Rate:    {100 * success_count / sample_size:.1f}%")
            print(f"{'='*60}\n")
            
            if success_count == sample_size:
                print(f"✅ ALL TESTS PASSED - Authentication is working correctly!\n")
                return True
            else:
                print(f"⚠️  SOME TESTS FAILED - Please review errors above\n")
                return False
                
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        db.close()

def test_specific_student(student_id: str, password: str):
    """Test login for a specific student."""
    
    print(f"\n{'='*60}")
    print(f"TESTING SPECIFIC STUDENT LOGIN")
    print(f"{'='*60}\n")
    
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        user = db.query(User).filter(User.student_id == student_id).first()
        
        if not user:
            print(f"❌ Student {student_id} not found in database")
            return False
        
        print(f"Student: {user.profile.name if user.profile else 'No profile'}")
        print(f"Email: {user.email}")
        print(f"Student ID: {user.student_id}")
        print(f"Hash preview: {user.password_hash[:30] if user.password_hash else 'NULL'}...")
        
        if not user.password_hash:
            print(f"\n❌ Password hash is NULL")
            return False
        
        # Test password verification
        is_valid = verify_password(password, user.password_hash)
        
        if is_valid:
            print(f"\n✅ PASSWORD CORRECT - Login would succeed")
            return True
        else:
            print(f"\n❌ PASSWORD INCORRECT - Login would fail")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        db.close()

if __name__ == "__main__":
    # Run random sample tests
    print("\n" + "="*60)
    print("PART 1: Random Sample Testing")
    print("="*60)
    test_login_authentication()
    
    # Test specific demo student
    print("\n" + "="*60)
    print("PART 2: Demo Student Testing")
    print("="*60)
    test_specific_student("S01968", "S01968@123")
