from app.core.database import SessionLocal
from app.modules.skills.engine import compute_skills_for_student, compute_gaps_for_student
from app.models.user import User

db = SessionLocal()
try:
    user = db.query(User).first()
    if user:
        print(f"Testing for user {user.email} (ID: {user.id})")
        compute_skills_for_student(db, str(user.id))
        compute_gaps_for_student(db, str(user.id))
        print("Success")
    else:
        print("No user found")
except Exception as e:
    import traceback
    traceback.print_exc()
finally:
    db.close()
