"""Display exact row counts for all PostgreSQL tables."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import engine
from sqlalchemy import text

try:
    with engine.connect() as conn:
        # Get all table names
        result = conn.execute(text(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'public' ORDER BY table_name"
        ))
        tables = [row[0] for row in result]
        
        print("\nPostgreSQL Database: student_tracker")
        print("=" * 80)
        
        table_counts = []
        total_rows = 0
        
        for table in tables:
            count_result = conn.execute(text(f'SELECT COUNT(*) FROM "{table}"'))
            count = count_result.scalar()
            total_rows += count
            table_counts.append((table, count))
            print(f"  {table:40s} {count:>15,} rows")
        
        print("=" * 80)
        print(f"  {'TOTAL':40s} {total_rows:>15,} rows")
        print("=" * 80)
        print()
        
except Exception as e:
    print(f"\nERROR connecting to database: {e}")
    print("\nPlease ensure PostgreSQL is running on localhost:5432")
    sys.exit(1)
