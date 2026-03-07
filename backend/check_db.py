"""DB state verifier for Phase 2 hardening."""
import sys
sys.path.insert(0, r'C:\Users\Admin\Desktop\fullstack\backend')

from app.core.database import engine
from sqlalchemy import inspect, text
import subprocess

insp = inspect(engine)

# --- interview_sessions indexes ---
print("=== interview_sessions indexes ===")
for i in sorted(insp.get_indexes('interview_sessions'), key=lambda x: x['name']):
    print(f"  {i['name']}: columns={i['column_names']}")

# --- interview_questions indexes ---
print("\n=== interview_questions indexes ===")
for i in sorted(insp.get_indexes('interview_questions'), key=lambda x: x['name']):
    print(f"  {i['name']}: columns={i['column_names']}")

# --- CHECK constraints ---
print("\n=== interview_sessions CHECK constraints ===")
with engine.connect() as conn:
    rows = conn.execute(text(
        "SELECT conname, contype, pg_get_constraintdef(oid) "
        "FROM pg_constraint WHERE conrelid='interview_sessions'::regclass"
    )).fetchall()
    for r in rows:
        print(f"  [{r[1]}] {r[0]}: {r[2]}")

# --- Alembic current ---
print("\n=== Alembic current revision ===")
r = subprocess.run(
    [sys.executable, '-m', 'alembic', 'current'],
    capture_output=True, text=True,
    cwd=r'C:\Users\Admin\Desktop\fullstack\backend'
)
print(" ", r.stderr.strip())
print("Done.")
