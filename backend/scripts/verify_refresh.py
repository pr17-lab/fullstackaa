import sys
sys.path.insert(0, '.')
from app.models import User, StudentProfile, AcademicTerm
from app.core.database import SessionLocal

session = SessionLocal()

print(f'Users: {session.query(User).count()}')
print(f'Profiles: {session.query(StudentProfile).count()}')
print(f'Academic Terms: {session.query(AcademicTerm).count()}')

print('\nFirst 3 students:')
users = session.query(User).limit(3).all()
for u in users:
    if u.profile:
        print(f'  {u.student_id} | {u.email} | {u.profile.name} | {u.profile.branch}')
    else:
        print(f'  {u.student_id} | {u.email} | NO PROFILE')

print('\nLast 3 students:')
total = session.query(User).count()
last_users = session.query(User).offset(total - 3).limit(3).all()
for u in last_users:
    if u.profile:
        print(f'  {u.student_id} | {u.email} | {u.profile.name} | {u.profile.branch}')
    else:
        print(f'  {u.student_id} | {u.email} | NO PROFILE')

session.close()
