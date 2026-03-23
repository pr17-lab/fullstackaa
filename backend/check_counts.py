import sys
sys.path.insert(0, '.')
from app.core.config import settings
from sqlalchemy import create_engine, text

engine = create_engine(settings.DATABASE_URL)
with engine.connect() as conn:
    users = conn.execute(text('SELECT COUNT(*) FROM users')).scalar()
    profiles = conn.execute(text('SELECT COUNT(*) FROM student_profiles')).scalar()
    terms = conn.execute(text('SELECT COUNT(*) FROM academic_terms')).scalar()
    subjects = conn.execute(text('SELECT COUNT(*) FROM subjects')).scalar()
    sample = conn.execute(text('SELECT student_id FROM users LIMIT 5')).fetchall()

print(f'users:            {users}')
print(f'student_profiles: {profiles}')
print(f'academic_terms:   {terms}')
print(f'subjects:         {subjects}')
print(f'Sample IDs:       {[r[0] for r in sample]}')
