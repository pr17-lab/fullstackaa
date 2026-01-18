"""
Base Data Migration Class

Abstract base class for all data migrations providing:
- Standard interface for upgrade/downgrade operations
- Session management
- Version tracking
- Backup/restore capabilities
"""

from abc import ABC, abstractmethod
from sqlalchemy.orm import Session
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class DataMigration(ABC):
    """
    Abstract base class for data migrations.
    
    All data migrations should inherit from this class and implement
    the upgrade() and downgrade() methods.
    
    Example:
        class MyMigration(DataMigration):
            version = "003"
            description = "Import new student batch"
            
            def upgrade(self):
                # Implementation here
                pass
            
            def downgrade(self):
                # Rollback implementation here
                pass
    """
    
    def __init__(self, session: Session):
        """
        Initialize the migration.
        
        Args:
            session: SQLAlchemy database session
        """
        self.session = session
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    @property
    @abstractmethod
    def version(self) -> str:
        """
        Migration version identifier.
        
        Should be a zero-padded 3-digit string (e.g., "001", "002", "003")
        """
        pass
    
    @property
    def description(self) -> str:
        """
        Optional human-readable description of the migration.
        
        Returns:
            Description string
        """
        return self.__class__.__name__
    
    @abstractmethod
    def upgrade(self) -> None:
        """
        Apply the migration.
        
        This method should contain all the logic to apply the data migration,
        including data imports, transformations, and updates.
        
        Raises:
            Exception: If migration fails
        """
        pass
    
    @abstractmethod
    def downgrade(self) -> None:
        """
        Rollback the migration.
        
        This method should reverse the changes made by upgrade().
        It's recommended to create backups before upgrade to make
        downgrade easier.
        
        Raises:
            Exception: If rollback fails
        """
        pass
    
    def log_info(self, message: str) -> None:
        """
        Log an info message.
        
        Args:
            message: Message to log
        """
        self.logger.info(f"[{self.version}] {message}")
        print(f"ℹ️  [{self.version}] {message}")
    
    def log_warning(self, message: str) -> None:
        """
        Log a warning message.
        
        Args:
            message: Message to log
        """
        self.logger.warning(f"[{self.version}] {message}")
        print(f"⚠️  [{self.version}] {message}")
    
    def log_error(self, message: str) -> None:
        """
        Log an error message.
        
        Args:
            message: Message to log
        """
        self.logger.error(f"[{self.version}] {message}")
        print(f"❌ [{self.version}] {message}")
    
    def log_success(self, message: str) -> None:
        """
        Log a success message.
        
        Args:
            message: Message to log
        """
        self.logger.info(f"[{self.version}] {message}")
        print(f"✅ [{self.version}] {message}")
    
    def execute_sql(self, sql: str, params: Optional[dict] = None) -> None:
        """
        Execute raw SQL safely.
        
        Args:
            sql: SQL query to execute
            params: Optional parameters for the query
        """
        from sqlalchemy import text
        self.session.execute(text(sql), params or {})
    
    def backup_table(self, table_name: str) -> str:
        """
        Create a backup of a table.
        
        Args:
            table_name: Name of the table to backup
            
        Returns:
            Name of the backup table
        """
        backup_name = f"{table_name}_backup_{self.version}"
        self.log_info(f"Creating backup: {backup_name}")
        
        self.execute_sql(f"DROP TABLE IF EXISTS {backup_name}")
        self.execute_sql(f"CREATE TABLE {backup_name} AS SELECT * FROM {table_name}")
        
        self.log_success(f"Backup created: {backup_name}")
        return backup_name
    
    def restore_from_backup(self, table_name: str, backup_name: str) -> None:
        """
        Restore a table from backup.
        
        Args:
            table_name: Name of the table to restore
            backup_name: Name of the backup table
        """
        self.log_info(f"Restoring {table_name} from {backup_name}")
        
        self.execute_sql(f"TRUNCATE TABLE {table_name}")
        self.execute_sql(f"INSERT INTO {table_name} SELECT * FROM {backup_name}")
        
        self.log_success(f"Restored {table_name} from {backup_name}")
