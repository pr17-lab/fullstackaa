import sys
sys.path.insert(0, '.')
from app.core.config import settings
from sqlalchemy import create_engine, text

engine = create_engine(settings.DATABASE_URL)
with engine.connect() as conn:
    print('Checking unique constraints...')
    
    # Check subjects constraint
    res = conn.execute(text("""
        SELECT conname, pg_get_constraintdef(oid)
        FROM pg_constraint 
        WHERE conrelid = 'subjects'::regclass 
        AND contype = 'u'
    """)).fetchall()
    print(f'Subjects unique constraints: {res}')

    # Check academic_terms constraint
    res2 = conn.execute(text("""
        SELECT conname, pg_get_constraintdef(oid)
        FROM pg_constraint 
        WHERE conrelid = 'academic_terms'::regclass 
        AND contype = 'u'
    """)).fetchall()
    print(f'Academic terms unique constraints: {res2}')
