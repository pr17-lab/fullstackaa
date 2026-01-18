#!/usr/bin/env python3
"""
Backup student data from PostgreSQL database.
Exports users and student_profiles tables to PostgreSQL SQL and CSV formats.
"""

import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path to import app modules
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import pandas as pd

from app.models import User, StudentProfile
from app.core.database import Base

# Database connection
DATABASE_URL = "postgresql://studentadmin:studentpass123@localhost:5432/student_tracker"

# Backup directory
BACKUP_DIR = backend_dir / "backups"


def get_db_session():
    """Create database session."""
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal(), engine


def create_backup_directory():
    """Ensure backup directory exists."""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[*] Backup directory: {BACKUP_DIR}")


def get_timestamp():
    """Generate timestamp for backup filenames."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def backup_table_to_sql(engine, table_name: str, output_file: Path):
    """Export table data as PostgreSQL INSERT statements."""
    print(f"\n[*] Backing up table '{table_name}' to SQL...")
    
    with engine.connect() as conn:
        # Get column names
        result = conn.execute(text(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table_name}' ORDER BY ordinal_position"))
        columns = [row[0] for row in result]
        
        # Get all rows
        result = conn.execute(text(f'SELECT * FROM "{table_name}"'))
        rows = result.fetchall()
        
        if not rows:
            print(f"    [!] Warning: Table '{table_name}' is empty, skipping SQL backup")
            return 0
        
        # Write SQL INSERT statements
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"-- PostgreSQL backup for table: {table_name}\n")
            f.write(f"-- Generated: {datetime.now().isoformat()}\n")
            f.write(f"-- Row count: {len(rows)}\n\n")
            
            for row in rows:
                # Format values for SQL INSERT
                values = []
                for i, val in enumerate(row):
                    if val is None:
                        values.append("NULL")
                    elif isinstance(val, str):
                        # Escape single quotes for SQL
                        escaped = val.replace("'", "''")
                        values.append(f"'{escaped}'")
                    elif isinstance(val, (int, float)):
                        values.append(str(val))
                    elif isinstance(val, datetime):
                        values.append(f"'{val.isoformat()}'")
                    else:
                        # For UUID and other types, convert to string
                        values.append(f"'{str(val)}'")
                
                columns_str = ', '.join([f'"{col}"' for col in columns])
                values_str = ', '.join(values)
                f.write(f'INSERT INTO "{table_name}" ({columns_str}) VALUES ({values_str});\n')
        
        print(f"    [+] Exported {len(rows)} rows to {output_file.name}")
        return len(rows)


def backup_table_to_csv(session, model, output_file: Path):
    """Export table data to CSV format."""
    table_name = model.__tablename__
    print(f"\n[*] Backing up table '{table_name}' to CSV...")
    
    # Query all records
    records = session.query(model).all()
    
    if not records:
        print(f"    [!] Warning: Table '{table_name}' is empty, skipping CSV backup")
        return 0
    
    # Convert to list of dicts
    data = []
    for record in records:
        record_dict = {}
        for column in model.__table__.columns:
            value = getattr(record, column.name)
            # Convert UUID and datetime to string for CSV
            if value is not None:
                record_dict[column.name] = str(value)
            else:
                record_dict[column.name] = None
        data.append(record_dict)
    
    # Write to CSV
    df = pd.DataFrame(data)
    df.to_csv(output_file, index=False)
    
    print(f"    [+] Exported {len(data)} rows to {output_file.name}")
    return len(data)


def create_combined_backup(session, output_file: Path):
    """Create a combined CSV backup with user and profile data."""
    print(f"\n[*] Creating combined backup CSV...")
    
    # Query users with their profiles
    users = session.query(User).all()
    
    if not users:
        print(f"    [!] Warning: No users to backup")
        return 0
    
    combined_data = []
    for user in users:
        profile = user.profile
        if profile:
            combined_data.append({
                'user_id': str(user.id),
                'student_id': user.student_id,
                'email': user.email,
                'password_hash': user.password_hash,
                'is_active': user.is_active,
                'user_created_at': str(user.created_at),
                'profile_id': str(profile.id),
                'name': profile.name,
                'branch': profile.branch,
                'semester': profile.semester,
                'interests': profile.interests,
                'profile_created_at': str(profile.created_at)
            })
    
    df = pd.DataFrame(combined_data)
    df.to_csv(output_file, index=False)
    
    print(f"    [+] Created combined backup with {len(combined_data)} records")
    return len(combined_data)


def verify_counts(session):
    """Display current row counts."""
    user_count = session.query(User).count()
    profile_count = session.query(StudentProfile).count()
    
    print(f"\n[*] Current Database Counts:")
    print(f"    - Users: {user_count:,}")
    print(f"    - Student Profiles: {profile_count:,}")
    
    return user_count, profile_count


def main():
    """Main backup function."""
    print("=" * 80)
    print("BACKUP STUDENT DATA - PostgreSQL Export")
    print("=" * 80)
    
    try:
        # Create backup directory
        create_backup_directory()
        
        # Create database session
        session, engine = get_db_session()
        
        # Verify current counts
        user_count, profile_count = verify_counts(session)
        
        if user_count == 0 and profile_count == 0:
            print("\n[!] No data to backup. Database is already empty.")
            session.close()
            return
        
        # Generate timestamp for backup files
        timestamp = get_timestamp()
        
        # Backup filenames
        users_sql_file = BACKUP_DIR / f"users_backup_{timestamp}.sql"
        profiles_sql_file = BACKUP_DIR / f"student_profiles_backup_{timestamp}.sql"
        users_csv_file = BACKUP_DIR / f"users_backup_{timestamp}.csv"
        profiles_csv_file = BACKUP_DIR / f"student_profiles_backup_{timestamp}.csv"
        combined_csv_file = BACKUP_DIR / f"student_data_backup_{timestamp}.csv"
        
        # Perform backups
        print("\n" + "=" * 80)
        print("EXPORTING TO POSTGRESQL SQL FORMAT")
        print("=" * 80)
        
        users_sql_count = backup_table_to_sql(engine, "users", users_sql_file)
        profiles_sql_count = backup_table_to_sql(engine, "student_profiles", profiles_sql_file)
        
        print("\n" + "=" * 80)
        print("EXPORTING TO CSV FORMAT")
        print("=" * 80)
        
        users_csv_count = backup_table_to_csv(session, User, users_csv_file)
        profiles_csv_count = backup_table_to_csv(session, StudentProfile, profiles_csv_file)
        combined_count = create_combined_backup(session, combined_csv_file)
        
        # Summary
        print("\n" + "=" * 80)
        print("BACKUP SUMMARY")
        print("=" * 80)
        print(f"\n[+] PostgreSQL SQL Backups:")
        print(f"    - {users_sql_file.name} ({users_sql_count:,} rows)")
        print(f"    - {profiles_sql_file.name} ({profiles_sql_count:,} rows)")
        print(f"\n[+] CSV Backups:")
        print(f"    - {users_csv_file.name} ({users_csv_count:,} rows)")
        print(f"    - {profiles_csv_file.name} ({profiles_csv_count:,} rows)")
        print(f"    - {combined_csv_file.name} ({combined_count:,} rows)")
        
        print(f"\n[+] All backups saved to: {BACKUP_DIR}")
        print(f"\n[+] Backup timestamp: {timestamp}")
        print("\n[+] Backup completed successfully!")
        
        # Save backup info for rollback reference
        info_file = BACKUP_DIR / f"backup_info_{timestamp}.txt"
        with open(info_file, 'w') as f:
            f.write(f"Backup Timestamp: {timestamp}\n")
            f.write(f"Backup Date: {datetime.now().isoformat()}\n\n")
            f.write(f"PostgreSQL SQL Files:\n")
            f.write(f"  - {users_sql_file.name}\n")
            f.write(f"  - {profiles_sql_file.name}\n\n")
            f.write(f"CSV Files:\n")
            f.write(f"  - {users_csv_file.name}\n")
            f.write(f"  - {profiles_csv_file.name}\n")
            f.write(f"  - {combined_csv_file.name}\n\n")
            f.write(f"Row Counts:\n")
            f.write(f"  - Users: {users_sql_count}\n")
            f.write(f"  - Student Profiles: {profiles_sql_count}\n")
        
        print(f"\n[+] Backup info saved to: {info_file.name}")
        
        session.close()
        
    except Exception as e:
        print(f"\n[!] Error during backup: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
