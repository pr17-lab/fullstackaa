#!/usr/bin/env python3
"""
Display PostgreSQL database contents with sample data from each table.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import engine
from sqlalchemy import text
import pandas as pd

def print_table_data(table_name, limit=5):
    """Print formatted data from a table."""
    print(f"\n{'='*100}")
    print(f"TABLE: {table_name.upper()}")
    print('='*100)
    
    with engine.connect() as conn:
        # Get total count
        count = conn.execute(text(f'SELECT COUNT(*) FROM "{table_name}"')).scalar()
        print(f"Total rows: {count:,}")
        
        # Get sample data
        print(f"\nSample Data (first {limit} rows):")
        print('-'*100)
        
        df = pd.read_sql(text(f'SELECT * FROM "{table_name}" LIMIT {limit}'), conn)
        
        if len(df) > 0:
            pd.set_option('display.max_columns', None)
            pd.set_option('display.width', 200)
            pd.set_option('display.max_colwidth', 40)
            
            print(df.to_string(index=False))
        else:
            print("  (no data)")

def main():
    print("="*100)
    print("POSTGRESQL DATABASE VIEWER - student_tracker")
    print("="*100)
    
    with engine.connect() as conn:
        # Get all tables
        result = conn.execute(text(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'public' ORDER BY table_name"
        ))
        tables = [row[0] for row in result]
        
        print(f"\nFound {len(tables)} tables: {', '.join(tables)}")
        
        # Display each table
        for table in tables:
            if table != 'alembic_version':
                print_table_data(table)
        
        # Summary statistics
        print(f"\n\n{'='*100}")
        print("DATABASE SUMMARY")
        print('='*100)
        
        user_count = conn.execute(text('SELECT COUNT(*) FROM users')).scalar()
        profile_count = conn.execute(text('SELECT COUNT(*) FROM student_profiles')).scalar()
        term_count = conn.execute(text('SELECT COUNT(*) FROM academic_terms')).scalar()
        subject_count = conn.execute(text('SELECT COUNT(*) FROM subjects')).scalar()
        
        print(f"\nTotal Records:")
        print(f"   Users:            {user_count:>10,}")
        print(f"   Student Profiles: {profile_count:>10,}")
        print(f"   Academic Terms:   {term_count:>10,}")
        print(f"   Subjects:         {subject_count:>10,}")
        print(f"   {'-'*40}")
        print(f"   TOTAL:            {user_count + profile_count + term_count + subject_count:>10,}")
        
        # Department breakdown
        print(f"\nStudents by Department:")
        dept_result = conn.execute(text(
            'SELECT branch, COUNT(*) as count FROM student_profiles '
            'GROUP BY branch ORDER BY count DESC'
        ))
        for row in dept_result:
            print(f"   {row[0]:35s} {row[1]:>6,} students")
        
        # Semester breakdown
        print(f"\nStudents by Semester:")
        sem_result = conn.execute(text(
            'SELECT semester, COUNT(*) as count FROM student_profiles '
            'GROUP BY semester ORDER BY semester'
        ))
        for row in sem_result:
            print(f"   Semester {row[0]:2d} {row[1]:>10,} students")
        
        print(f"\n{'='*100}\n")

if __name__ == "__main__":
    main()
