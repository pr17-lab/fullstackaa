import sys
from pathlib import Path

# Redirect stdout to file
sys.stdout = open('simulate_login_output.txt', 'w')

sys.path.insert(0, str(Path(__file__).parent))

from app.core.security import verify_password
from app.models.user import User
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Create DB session
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

try:
    # Simulate login
    form_password = "STU001@123"
    form_username = "priya.sharma@example.com"
    
    print(f"Login attempt:")
    print(f"  Username: {form_username}")
    print(f"  Password: {form_password}")
    print(f"  Password length: {len(form_password)}")
    
    # Find user
    user = db.query(User).filter(User.email == form_username).first()
    
    if not user:
        print("\nERROR: User not found!")
    else:
        print(f"\nUser found: {user.email}")
        print(f"  user.password_hash type: {type(user.password_hash)}")
        print(f"  user.password_hash length: {len(user.password_hash)}")
        print(f"  user.password_hash value: {user.password_hash}")
        
        print(f"\nCalling verify_password('{form_password}', '{user.password_hash}')")
        
        # This is the exact call from auth.py line 52
        try:
            result = verify_password(form_password, user.password_hash)
            print(f"Result: {result}")
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()
        
finally:
    db.close()
    sys.stdout.close()
