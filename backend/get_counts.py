"""Count rows in all database tables."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import engine
from sqlalchemy import text

try:
    print("=" * 70)
    print("PostgreSQL Database: student_tracker")
    print("=" * 70)
    print()

    with engine.connect() as conn:
        result = conn.execute(text(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name"
        ))
        tables = [row[0] for row in result]
        
        total_rows = 0
        for table in tables:
            count_result = conn.execute(text(f'SELECT COUNT(*) FROM "{table}"'))
            count = count_result.scalar()
            total_rows += count
            print(f"{table:35s}: {count:>10,} rows")
        
        print()
        print("=" * 70)
        print(f"{'TOTAL ROWS ACROSS ALL TABLES':35s}: {total_rows:>10,} rows")
        print("=" * 70)
        print()
        print("SUCCESS: Database connection established and row counts retrieved!")
        
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)
