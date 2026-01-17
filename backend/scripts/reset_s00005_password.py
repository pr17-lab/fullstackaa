"""Reset password for S00005 using the app's hashing function"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import User
from app.core.security import get_password_hash

DATABASE_URL = "postgresql://studentadmin:studentpass123@localhost:5432/student_tracker"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

try:
    user = db.query(User).filter(User.student_id == 'S00005').first()
    
    if user:
        # Set new password using app's hash function
        new_password = "S00005@123"
        user.password_hash = get_password_hash(new_password)
        
        db.commit()
        print(f"✓ Password reset for {user.student_id}")
        print(f"  New password: {new_password}")
        print(f"  Hash (first 50 chars): {user.password_hash[:50]}...")
    else:
        print("User not found!")
        
finally:
    db.close()
