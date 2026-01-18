"""
Example Data Migration: Initial Migration (Empty)

This is the initial migration that does nothing.
It exists to establish the migration system.
"""

from .base import DataMigration


class InitialMigration(DataMigration):
    """Initial empty migration to establish the migration system."""
    
    version = "001"
    description = "Initial migration setup"
    
    def upgrade(self) -> None:
        """Apply the migration (no-op for initial)."""
        self.log_info("Initial migration - no data changes")
        self.log_success("Initial migration complete")
    
    def downgrade(self) -> None:
        """Rollback the migration (no-op for initial)."""
        self.log_info("Initial migration - no rollback needed")
        self.log_success("Initial migration rollback complete")
