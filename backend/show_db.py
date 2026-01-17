"""Simple script to query and display PostgreSQL database sample records."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import engine
from sqlalchemy import text

print("\n" + "="*80)
print("POSTGRESQL DATABASE: student_tracker")
print("="*80 + "\n")

with engine.connect() as conn:
    # Table counts
    print("TABLE ROW COUNTS:")
    print("-"*80)
    tables = ['users', 'student_profiles', 'academic_terms', 'subjects']
    total = 0
    for table in tables:
        count = conn.execute(text(f'SELECT COUNT(*) FROM {table}')).scalar()
        total += count
        print(f"  {table:25s} {count:>10,} rows")
    print("-"*80)
    print(f"  {'TOTAL':25s} {total:>10,} rows")
    
    # Sample users
    print("\n\nSAMPLE USERS (first 5):")
    print("-"*80)
    users = conn.execute(text('SELECT id, email, is_active FROM users LIMIT 5'))
    print(f"  {'ID':40s} {'Email':40s} Active")
    print("  " + "-"*78)
    for row in users:
        print(f"  {str(row[0]):40s} {row[1]:40s} {row[2]}")
    
    # Sample profiles
    print("\n\nSAMPLE STUDENT PROFILES (first 5):")
    print("-"*80)
    profiles = conn.execute(text('SELECT name, branch, semester FROM student_profiles LIMIT 5'))
    print(f"  {'Name':30s} {'Department':30s} Semester")
    print("  " + "-"*78)
    for row in profiles:
        print(f"  {row[0]:30s} {row[1]:30s} {row[2]}")
    
    # Department distribution
    print("\n\nSTUDENTS BY DEPARTMENT:")
    print("-"*80)
    depts = conn.execute(text('SELECT branch, COUNT(*) FROM student_profiles GROUP BY branch ORDER BY COUNT(*) DESC'))
    for row in depts:
        bar = "*" * (row[1] // 100)
        print(f"  {row[0]:35s} {row[1]:>6,} {bar}")
    
    # Semester distribution
    print("\n\nSTUDENTS BY SEMESTER:")
    print("-"*80)
    sems = conn.execute(text('SELECT semester, COUNT(*) FROM student_profiles GROUP BY semester ORDER BY semester'))
    for row in sems:
        bar = "*" * (row[1] // 100)
        print(f"  Semester {row[0]:2d} {row[1]:>10,} {bar}")
    
print("\n" + "="*80 + "\n")
