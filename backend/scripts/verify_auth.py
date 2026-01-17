"""
Comprehensive authentication verification script.
Tests student_id lookup, password verification, and login flow.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import engine
from sqlalchemy import text

print("=" * 80)
print("AUTHENTICATION VERIFICATION")
print("=" * 80)

with engine.connect() as conn:
    # Test 1: Check if demo user exists by student_id
    print("\n[Test 1] Looking up demo user by student_id...")
    result = conn.execute(
        text("SELECT id, email, student_id, password_hash FROM users WHERE student_id = :sid"),
        {"sid": "S00001"}
    )
    user = result.fetchone()
    
    if not user:
        print("  [X] Demo user S00001 not found!")
        print("\n  Checking first few users in database...")
        result = conn.execute(text("SELECT student_id, email FROM users LIMIT 5"))
        for row in result:
            print(f"    - {row[0]}: {row[1]}")
    else:
        print(f"  [OK] User found:")
        print(f"    - ID: {user[0]}")
        print(f"    - Email: {user[1]}")
        print(f"    - Student ID: {user[2]}")
        print(f"    - Has password hash: {'Yes' if user[3] else 'No'}")
        
        # Test 2: Verify password using passlib (as backend does)
        if user[3]:
            print(f"\n[Test 2] Testing password verification...")
            test_password = f"{user[2]}@123"  # Expected format: S00001@123
            print(f"  Testing password: {test_password}")
            
            try:
                from app.core.security import verify_password
                is_valid = verify_password(test_password, user[3])
                if is_valid:
                    print(f"  [OK] Password verified successfully!")
                else:
                    print(f"  [X] Password verification failed")
                    print(f"  Hash preview: {user[3][:60]}...")
                    
            except Exception as e:
                print(f"  [X] Error during verification: {e}")
        else:
            print(f"\n[Test 2] SKIPPED - User has no password hash")
    
    # Test 3: Check overall user statistics
    print(f"\n[Test 3] User statistics...")
    result = conn.execute(text("""
        SELECT 
            COUNT(*) as total_users,
            COUNT(student_id) as with_student_id,
            COUNT(password_hash) as with_password,
            COUNT(CASE WHEN is_active = true THEN 1 END) as active_users
        FROM users
    """))
    stats = result.fetchone()
    print(f"  Total users: {stats[0]:,}")
    print(f"  With student_id: {stats[1]:,}")
    print(f"  With password_hash: {stats[2]:,}")
    print(f"  Active users: {stats[3]:,}")
    
    # Test 4: Sample of student IDs
    print(f"\n[Test 4] Sample student IDs...")
    result = conn.execute(text("SELECT student_id FROM users WHERE student_id IS NOT NULL ORDER BY student_id LIMIT 10"))
    print(f"  First 10 student IDs:")
    for row in result:
        print(f"    - {row[0]}")
    
    conn.close()

print("\n" + "=" * 80)
print("VERIFICATION COMPLETE")
print("=" * 80)
