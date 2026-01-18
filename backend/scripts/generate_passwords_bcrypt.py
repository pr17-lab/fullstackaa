#!/usr/bin/env python3
"""
Generate passwords for all users based on their student_id in the database.
Password format: {student_id}@123
Example: S00001@123
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import bcrypt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.user import User

DATABASE_URL = "postgresql://studentadmin:studentpass123@localhost:5432/student_tracker"


def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def main():
    print("=" * 80)
    print("GENERATING PASSWORDS FROM STUDENT_ID")
    print("=" * 80)
    
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    # Get all users with student_id
    print(f"\n[*] Loading users from database...")
    users = session.query(User).all()
    print(f"    Found {len(users):,} total users")
    
    users_with_student_id = [u for u in users if u.student_id and u.student_id.strip()]
    print(f"    Users with valid student_id: {len(users_with_student_id):,}")
    
    print(f"\n[*] Generating passwords...")
    updated = 0
    
    for user in users_with_student_id:
        # Generate password: student_id + "@123"
        password = f"{user.student_id}@123"
        
        # Hash and update
        user.password_hash = hash_password(password)
        updated += 1
        
        if updated % 1000 == 0:
            session.commit()
            print(f"    Progress: {updated:,}/{len(users_with_student_id):,}...")
    
    # Final commit
    session.commit()
    
    print(f"\n[+] Password generation complete!")
    print(f"    Updated: {updated:,} users")
    
    print(f"\n[*] Login format:")
    print(f"    Username: [student_id]")
    print(f"    Password: [student_id]@123")
    print(f"\n[*] Example:")
    print(f"    Username: S00001")
    print(f"    Password: S00001@123")
    
    # Verify
    sample = session.query(User).filter(User.student_id != None).first()
    if sample and sample.password_hash and sample.password_hash.startswith("$2b$"):
        print(f"\n[+] Verification: Passwords use bcrypt format ($2b$)")
    
    session.close()
    print(f"\n" + "=" * 80)


if __name__ == "__main__":
    main()
