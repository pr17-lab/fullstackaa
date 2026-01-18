import sys
sys.path.insert(0, '.')
from app.models import User
from app.core.database import SessionLocal

session = SessionLocal()

# Get all student IDs
all_student_ids = [u.student_id for u in session.query(User).all()]
print(f'Total users in database: {len(all_student_ids)}')
print(f'\nFirst 10 student IDs: {sorted(all_student_ids)[:10]}')
print(f'\nLast 10 student IDs: {sorted(all_student_ids)[-10:]}')

# Check the range
numeric_ids = [int(sid.replace('S', '')) for sid in all_student_ids if sid and sid.startswith('S')]
if numeric_ids:
    print(f'\nNumeric ID range: {min(numeric_ids)} to {max(numeric_ids)}')
    print(f'Expected 10,000 students: S00001 to S10000')
    
    # Check for gaps
    expected_ids = set(range(1, 10001))
    actual_ids = set(numeric_ids)
    missing = expected_ids - actual_ids
    extra = actual_ids - expected_ids
    
    if missing:
        print(f'\nMissing {len(missing)} student IDs')
        print(f'First 20 missing: {sorted(list(missing))[:20]}')
    if extra:
        print(f'\nExtra {len(extra)} student IDs not in expected range')

session.close()
