from sqlalchemy import create_engine, text

# Connect to database
engine = create_engine('postgresql://studentadmin:studentpass123@localhost:5432/student_tracker')

with engine.connect() as conn:
    # Get all table names
    result = conn.execute(text(
        "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name"
    ))
    tables = [row[0] for row in result]
    
    print("Database: PostgreSQL (student_tracker)")
    print("=" * 60)
    print()
    
    total_rows = 0
    for table in tables:
        count_result = conn.execute(text(f'SELECT COUNT(*) FROM "{table}"'))
        count = count_result.scalar()
        total_rows += count
        print(f"{table:30s}: {count:,} rows")
    
    print()
    print("=" * 60)
    print(f"{'TOTAL':30s}: {total_rows:,} rows")
