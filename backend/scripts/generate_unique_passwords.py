#!/usr/bin/env python3
"""
Generate unique random passwords for all users.
Exports to CSV and updates database with hashed versions.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import secrets
import string
import csv
import bcrypt
from sqlalchemy.orm import sessionmaker
from app.core.database import engine
from app.models.user import User

def generate_password(length=12):
    """Generate a secure random password."""
    alphabet = string.ascii_letters + string.digits
    # Ensure at least one letter and one number
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    return password

def main():
    print("=" * 80)
    print("GENERATING UNIQUE PASSWORDS")
    print("=" * 80)
    
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    try:
        # Get all users with student_id
        users = session.query(User).filter(User.student_id.isnot(None)).all()
        print(f"\n[*] Found {len(users):,} users to update")
        
        # Prepare CSV data
        csv_data = []
        updated_count = 0
        
        print("\n[*] Generating passwords and updating database...")
        
        for idx, user in enumerate(users, 1):
            # Generate random password
            password = generate_password(12)
            
            # Hash password
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            # Update user
            user.password_hash = password_hash
            
            # Add to CSV data
            csv_data.append({
                'student_id': user.student_id,
                'password': password,
                'email': user.email
            })
            
            updated_count += 1
            
            # Progress indicator
            if idx % 1000 == 0:
                print(f"    Progress: {idx:,}/{len(users):,} ({100*idx/len(users):.1f}%)")
                session.commit()
        
        # Final commit
        session.commit()
        print(f"\n[+] Updated {updated_count:,} user passwords in database")
        
        # Export to CSV
        csv_path = Path(__file__).parent.parent / "student_passwords.csv"
        print(f"\n[*] Exporting passwords to: {csv_path}")
        
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['student_id', 'password', 'email']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            writer.writerows(csv_data)
        
        print(f"[+] Exported {len(csv_data):,} passwords to CSV")
        
        # Show sample passwords
        print("\n[*] Sample passwords (first 5 users):")
        for i, row in enumerate(csv_data[:5]):
            print(f"    {row['student_id']}: {row['password']}")
        
        print("\n" + "=" * 80)
        print("PASSWORD GENERATION COMPLETE")
        print("=" * 80)
        print(f"\n[!] IMPORTANT: CSV file contains plaintext passwords!")
        print(f"    Location: {csv_path}")
        print(f"    - Store securely")
        print(f"    - Distribute to students via secure channel")
        print(f"    - Delete after distribution")
        print("\n" + "=" * 80)
        
    except Exception as e:
        print(f"\n[!] Error: {e}")
        import traceback
        traceback.print_exc()
        session.rollback()
        sys.exit(1)
    finally:
        session.close()

if __name__ == "__main__":
    main()
