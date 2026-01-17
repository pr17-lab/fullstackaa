#!/usr/bin/env python3
"""
Quick test to debug the password verification issue.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from passlib.context import CryptContext
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.user import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Create database session
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

try:
    # Get the user
    user = db.query(User).filter(User.email == "priya.sharma@example.com").first()
    
    if user:
        print(f"User found: {user.email}")
        print(f"Password hash type: {type(user.password_hash)}")
        print(f"Password hash length: {len(user.password_hash)}")
        print(f"Password hash first 70 chars: {user.password_hash[:70]}")
        print(f"Password hash repr: {repr(user.password_hash[:100])}")
        
        # Test password
        test_password = "STU001@123"
        print(f"\nTest password: {test_password}")
        print(f"Test password length: {len(test_password)}")
        
        # Try verification
        print("\nAttempting verification...")
        try:
            result = pwd_context.verify(test_password, user.password_hash)
            print(f"Verification result: {result}")
        except Exception as e:
            print(f"ERROR during verification: {e}")
            print(f"Error type: {type(e)}")
            import traceback
            traceback.print_exc()
    else:
        print("User not found!")
        
finally:
    db.close()
