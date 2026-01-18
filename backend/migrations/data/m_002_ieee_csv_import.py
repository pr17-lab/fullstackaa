"""
Example Data Migration: IEEE CSV Import

This migration demonstrates how to import student data from IEEE CSV files
with proper backup and rollback capabilities.
"""

import pandas as pd
from pathlib import Path
from .base import DataMigration
from app.models import User, StudentProfile


class IEEECsvImport(DataMigration):
    """Import student data from IEEE CSV files."""
    
    version = "002"
    description = "Import students from IEEE CSV files"
    
    def upgrade(self) -> None:
        """Import IEEE CSV data with backup."""
        self.log_info("Starting IEEE CSV import")
        
        # Create backups before import
        self.log_info("Creating table backups...")
        self.backup_table("users")
        self.backup_table("student_profiles")
        
        # Determine CSV path
        backend_dir = Path(__file__).parent.parent.parent
        csv_path = backend_dir / "data" / "SATA_student_main_info_10k_IEEE.csv"
        
        if not csv_path.exists():
            self.log_error(f"CSV file not found: {csv_path}")
            raise FileNotFoundError(f"CSV file not found: {csv_path}")
        
        self.log_info(f"Reading CSV from: {csv_path.name}")
        
        # Read and import CSV
        df = pd.read_csv(csv_path)
        self.log_info(f"Found {len(df)} records in CSV")
        
        imported = 0
        skipped = 0
        
        for idx, row in df.iterrows():
            # Check if user already exists
            existing = self.session.query(User).filter(
                User.email == row['email']
            ).first()
            
            if existing:
                skipped += 1
                continue
            
            # Create user
            user = User(
                student_id=row['student_id'],
                email=row['email'],
                password_hash='',  # Will be set by password generation script
                is_active=row.get('status', 'active').lower() == 'active'
            )
            self.session.add(user)
            self.session.flush()
            
            # Create profile
            profile = StudentProfile(
                user_id=user.id,
                name=row['name'],
                branch=row['department'],
                semester=int(row['current_semester']),
                interests=None
            )
            self.session.add(profile)
            imported += 1
            
            # Progress update
            if imported % 1000 == 0:
                self.log_info(f"Imported {imported} students...")
        
        self.session.commit()
        
        self.log_success(f"Import complete: {imported} users imported, {skipped} skipped")
    
    def downgrade(self) -> None:
        """Rollback to backup data."""
        self.log_info("Rolling back IEEE CSV import")
        
        # Restore from backups
        self.restore_from_backup("users", f"users_backup_{self.version}")
        self.restore_from_backup("student_profiles", f"student_profiles_backup_{self.version}")
        
        self.session.commit()
        
        self.log_success("Rollback complete")
