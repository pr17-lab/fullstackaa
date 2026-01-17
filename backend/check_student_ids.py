import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import engine
from sqlalchemy import text

conn = engine.connect()

# Check total counts
result = conn.execute(text("SELECT COUNT(*) FROM users WHERE student_id IS NOT NULL"))
with_ids = result.scalar()
result2 = conn.execute(text("SELECT COUNT(*) FROM users"))
total = result2.scalar()

print(f"Users with student_id: {with_ids}/{total}")

# Get a few sample student_ids
result3 = conn.execute(text("SELECT student_id, email FROM users WHERE student_id IS NOT NULL LIMIT 5"))
print("\nSample student IDs:")
for row in result3:
    print(f"  {row[0]} - {row[1]}")

conn.close()
