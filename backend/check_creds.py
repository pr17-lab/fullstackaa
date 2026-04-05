from app.models.user import User
from app.core.database import SessionLocal
from passlib.context import CryptContext

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

db = SessionLocal()
u = db.query(User).first()
cols = [c.name for c in User.__table__.columns]
print("Columns:", cols)
print("student_id:", u.student_id)

# Try to verify with known password
for pw in ["password123", "Password123", "student123", "test123", "admin123", u.student_id]:
    # Find the password column
    for col in cols:
        if 'password' in col.lower():
            stored = getattr(u, col, None)
            if stored:
                try:
                    if pwd_ctx.verify(pw, stored):
                        print(f"Password '{pw}' matches column '{col}'!")
                        break
                except:
                    pass
print("Password col value prefix:", getattr(u, 'password_hash', None) or getattr(u, 'hashed_password', None) or "not found")
db.close()
