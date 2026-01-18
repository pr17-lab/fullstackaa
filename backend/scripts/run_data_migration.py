#!/usr/bin/env python3
"""
Data Migration Runner

Execute data migrations with version control and tracking.

Usage:
    # Run a migration
    python scripts/run_data_migration.py --version 002 --direction upgrade
    
    # Rollback a migration
    python scripts/run_data_migration.py --version 002 --direction downgrade
    
    # List all migrations
    python scripts/run_data_migration.py --list
    
    # Show migration status
    python scripts/run_data_migration.py --status
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import Type, Optional

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from migrations.data.base import DataMigration


def create_migration_table(session):
    """Create the migration tracking table if it doesn't exist."""
    session.execute(text("""
        CREATE TABLE IF NOT EXISTS data_migrations (
            id SERIAL PRIMARY KEY,
            version VARCHAR(50) NOT NULL UNIQUE,
            description TEXT,
            applied_at TIMESTAMP NOT NULL DEFAULT NOW(),
            direction VARCHAR(10) NOT NULL
        )
    """))
    session.commit()


def get_migration_class(version: str) -> Type[DataMigration]:
    """
    Load a migration class by version number.
    
    Args:
        version: Migration version (e.g., "002")
        
    Returns:
        Migration class
        
    Raises:
        ImportError: If migration file not found
        AttributeError: If migration class not found in file
    """
    # Import the migration module
    module_name = f"migrations.data.{version.zfill(3)}_*"
    
    # Find the migration file (must start with 'm_' to be Python module compliant)
    migrations_dir = Path(__file__).parent.parent / "migrations" / "data"
    # Use string pattern to find migration files
    migration_files = [f for f in migrations_dir.glob("*.py") 
                       if f.stem.startswith("m_" + version.zfill(3) + "_")]
    
    if not migration_files:
        raise ImportError(f"Migration file for version {version} not found")
    
    migration_file = migration_files[0]
    module_name = f"migrations.data.{migration_file.stem}"
    
    # Import the module
    import importlib
    module = importlib.import_module(module_name)
    
    # Find the migration class (should be the only DataMigration subclass)
    for attr_name in dir(module):
        attr = getattr(module, attr_name)
        if (isinstance(attr, type) and 
            issubclass(attr, DataMigration) and 
            attr is not DataMigration):
            return attr
    
    raise AttributeError(f"No DataMigration class found in {module_name}")


def list_migrations():
    """List all available migrations."""
    migrations_dir = Path(__file__).parent.parent / "migrations" / "data"
    migration_files = sorted(migrations_dir.glob("*.py"))
    # Filter out __init__.py and base.py, only keep m_XXX_*.py files
    migration_files = [f for f in migration_files if f.stem.startswith('m_') and f.stem[2].isdigit()]
    
    print(f"\n{'='*70}")
    print("AVAILABLE DATA MIGRATIONS")
    print(f"{'='*70}\n")
    
    if not migration_files:
        print("No migrations found")
        return
    
    for migration_file in migration_files:
        # Extract version (skip 'm_' prefix)
        version = migration_file.stem[2:5]
        name = migration_file.stem[6:].replace('_', ' ').title()
        print(f"  {version}: {name}")
    
    print(f"\n{'='*70}\n")


def show_migration_status(session):
    """Show status of applied migrations."""
    create_migration_table(session)
    
    results = session.execute(text("""
        SELECT version, description, applied_at, direction 
        FROM data_migrations 
        ORDER BY applied_at DESC
    """)).fetchall()
    
    print(f"\n{'='*70}")
    print("MIGRATION STATUS")
    print(f"{'='*70}\n")
    
    if not results:
        print("No migrations have been applied")
    else:
        print(f"{'Version':<10} {'Direction':<12} {'Applied At':<20} {'Description'}")
        print(f"{'-'*70}")
        for row in results:
            version, description, applied_at, direction = row
            applied_str = applied_at.strftime("%Y-%m-%d %H:%M:%S")
            desc_short = (description[:30] + '...') if len(description) > 30 else description
            print(f"{version:<10} {direction:<12} {applied_str:<20} {desc_short}")
    
    print(f"\n{'='*70}\n")


def run_migration(version: str, direction: str = 'upgrade'):
    """
    Run a specific data migration.
    
    Args:
        version: Migration version to run
        direction: 'upgrade' or 'downgrade'
    """
    if direction not in ['upgrade', 'downgrade']:
        print(f"❌ Invalid direction: {direction}")
        print("   Must be 'upgrade' or 'downgrade'")
        sys.exit(1)
    
    print(f"\n{'='*70}")
    print(f"RUNNING MIGRATION: {version} ({direction.upper()})")
    print(f"{'='*70}\n")
    
    # Create database session
    engine = create_engine(settings.DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Ensure migration tracking table exists
        create_migration_table(session)
        
        # Load migration class
        print(f"📦 Loading migration class...")
        migration_class = get_migration_class(version)
        migration = migration_class(session)
        
        print(f"   Version:     {migration.version}")
        print(f"   Description: {migration.description}")
        print(f"   Direction:   {direction}")
        print()
        
        # Check if already applied
        existing = session.execute(text("""
            SELECT direction FROM data_migrations 
            WHERE version = :version 
            ORDER BY applied_at DESC 
            LIMIT 1
        """), {"version": version}).fetchone()
        
        if existing:
            last_direction = existing[0]
            if direction == 'upgrade' and last_direction == 'upgrade':
                print(f"⚠️  Warning: Migration {version} already applied (upgrade)")
                response = input("   Continue anyway? (y/N): ")
                if response.lower() != 'y':
                    print("   Aborted")
                    return
            elif direction == 'downgrade' and last_direction == 'downgrade':
                print(f"⚠️  Warning: Migration {version} already rolled back")
                response = input("   Continue anyway? (y/N): ")
                if response.lower() != 'y':
                    print("   Aborted")
                    return
        
        # Execute migration
        print(f"🚀 Executing migration...\n")
        
        if direction == 'upgrade':
            migration.upgrade()
        else:
            migration.downgrade()
        
        # Record migration
        session.execute(text("""
            INSERT INTO data_migrations (version, description, direction)
            VALUES (:version, :description, :direction)
        """), {
            "version": version,
            "description": migration.description,
            "direction": direction
        })
        
        session.commit()
        
        print(f"\n{'='*70}")
        print(f"✅ MIGRATION {direction.upper()} COMPLETE")
        print(f"{'='*70}\n")
        
    except Exception as e:
        session.rollback()
        print(f"\n{'='*70}")
        print(f"❌ MIGRATION FAILED")
        print(f"{'='*70}")
        print(f"\nError: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        session.close()


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Data migration runner with version control"
    )
    parser.add_argument(
        '--version',
        type=str,
        help='Migration version to run (e.g., 002)'
    )
    parser.add_argument(
        '--direction',
        type=str,
        choices=['upgrade', 'downgrade'],
        default='upgrade',
        help='Direction to run migration (default: upgrade)'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='List all available migrations'
    )
    parser.add_argument(
        '--status',
        action='store_true',
        help='Show migration status'
    )
    
    args = parser.parse_args()
    
    if args.list:
        list_migrations()
        return
    
    if args.status:
        engine = create_engine(settings.DATABASE_URL)
        Session = sessionmaker(bind=engine)
        session = Session()
        try:
            show_migration_status(session)
        finally:
            session.close()
        return
    
    if not args.version:
        parser.print_help()
        print("\nError: --version is required unless using --list or --status")
        sys.exit(1)
    
    run_migration(args.version, args.direction)


if __name__ == "__main__":
    main()
