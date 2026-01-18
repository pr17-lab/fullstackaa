#!/usr/bin/env python3
"""
Apply Database Performance Indexes

Executes the SQL migration to add performance indexes to the database.
Alternative to using psql command.

Usage:
    python scripts/apply_indexes.py
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from app.core.config import settings


def apply_indexes():
    """Apply performance indexes using SQLAlchemy."""
    
    print("=" * 70)
    print("APPLYING DATABASE PERFORMANCE INDEXES")
    print("=" * 70)
    print()
    
    # Create database connection
    print(f"🔌 Connecting to database...")
    engine = create_engine(settings.DATABASE_URL)
    
    try:
        with engine.connect() as conn:
            print(f"\n🚀 Creating indexes...\n")
            
            # Define indexes as individual statements
            indexes = [
                ("idx_users_student_id", "CREATE INDEX IF NOT EXISTS idx_users_student_id ON users(student_id);"),
                ("idx_users_email", "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);"),
                ("idx_academic_terms_user_semester", "CREATE INDEX IF NOT EXISTS idx_academic_terms_user_semester ON academic_terms(user_id, semester);"),
                ("idx_academic_terms_user_id", "CREATE INDEX IF NOT EXISTS idx_academic_terms_user_id ON academic_terms(user_id);"),
                ("idx_academic_terms_year", "CREATE INDEX IF NOT EXISTS idx_academic_terms_year ON academic_terms(year);"),
                ("idx_subjects_term_id", "CREATE INDEX IF NOT EXISTS idx_subjects_term_id ON subjects(term_id);"),
                ("idx_subjects_code", "CREATE INDEX IF NOT EXISTS idx_subjects_code ON subjects(subject_code);"),
                ("idx_student_profiles_user_branch", "CREATE INDEX IF NOT EXISTS idx_student_profiles_user_branch ON student_profiles(user_id, branch);"),
                ("idx_student_profiles_branch", "CREATE INDEX IF NOT EXISTS idx_student_profiles_branch ON student_profiles(branch);"),
                ("idx_student_profiles_semester", "CREATE INDEX IF NOT EXISTS idx_student_profiles_semester ON student_profiles(semester);"),
            ]
            
            # Create each index
            for i, (name, sql) in enumerate(indexes, 1):
                print(f"   [{i}/{len(indexes)}] Creating index: {name}")
                conn.execute(text(sql))
                conn.commit()
            
            # Analyze tables
            print(f"\n📊 Analyzing tables for query optimizer...\n")
            tables = ["users", "student_profiles", "academic_terms", "subjects"]
            for table in tables:
                print(f"   Analyzing: {table}")
                conn.execute(text(f"ANALYZE {table};"))
                conn.commit()
            
            print(f"\n✅ All indexes created successfully!")
            print()
            
            # Query index information
            print("=" * 70)
            print("CREATED INDEXES")
            print("=" * 70)
            print()
            
            result = conn.execute(text("""
                SELECT 
                    tablename,
                    indexname,
                    pg_size_pretty(pg_relation_size(schemaname||'.'||indexname)) as size
                FROM pg_indexes
                WHERE schemaname = 'public'
                    AND indexname LIKE 'idx_%'
                ORDER BY tablename, indexname
            """))
            
            current_table = None
            for row in result:
                if row[0] != current_table:
                    if current_table is not None:
                        print()
                    current_table = row[0]
                    print(f"📊 {row[0]}:")
                print(f"   ✓ {row[1]} ({row[2]})")
            
            print()
            print("=" * 70)
            print()
            
    except Exception as e:
        print(f"\n❌ Error applying indexes: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        engine.dispose()


if __name__ == "__main__":
    apply_indexes()

