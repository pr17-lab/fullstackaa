"""
Import missing students - simplified version with better error handling.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from sqlalchemy.orm import sessionmaker
from app.core.database import engine
from app.models.user import User
from app.models.student_profile import StudentProfile
import bcrypt

print("=" * 80)
print("IMPORTING MISSING STUDENTS")
print("=" * 80)

# Find missing student IDs
print("\n[Step 1] Identifying missing students...")

academic_df = pd.read_csv("data/SATA_academic_records_10k.csv")
csv_students = set(academic_df['student_id'].unique())

SessionLocal = sessionmaker(bind=engine)
session = SessionLocal()

try:
    db_students = set(u.student_id for u in session.query(User.student_id).filter(User.student_id.isnot(None)).all())
    missing_students = sorted(list(csv_students - db_students))
    
    print(f"  Academic CSV students: {len(csv_students):,}")
    print(f"  Database students: {len(db_students):,}")
    print(f"  Missing: {len(missing_students)}")

    if not missing_students:
        print("\n[OK] No missing students!")
        sys.exit(0)

    # Load student profiles
    print("\n[Step 2] Loading profiles...")
    students_df = pd.read_csv("data/SATA_student_main_info_10k.csv")
    missing_df = students_df[students_df['student_id'].isin(missing_students)].copy()
    
    print(f"  Students found in CSV: {len(missing_df)}")

    # Import
    print("\n[Step 3] Importing...")
    created = 0
    
    for idx, row in missing_df.iterrows():
        try:
            # Create user
            password_hash = bcrypt.hashpw(f"{row['student_id']}@123".encode(), bcrypt.gensalt()).decode()
            
            user = User(
                student_id=row['student_id'],
                email=row['email'],
                password_hash=password_hash,
                is_active=True
            )
            session.add(user)
            session.flush()
            
            # Create profile
            profile = StudentProfile(
                user_id=user.id,
                name=row['name'],
                branch=row['department'],
                semester=int(row['current_semester']),
                interests=None
            )
            session.add(profile)
            created += 1
            
            if created % 50 == 0:
                print(f"    Created {created}/{len(missing_df)}...")
                session.commit()
                
        except Exception as e:
            print(f"    ERROR on {row['student_id']}: {e}")
            session.rollback()
            continue
    
    session.commit()
    print(f"\n[OK] Created {created} users")
    
    # Verify
    total = session.query(User).filter(User.student_id.isnot(None)).count()
    print(f"    Total students now: {total:,}")
    
finally:
    session.close()

print("\n" + "=" * 80)
