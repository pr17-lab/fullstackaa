"""
Structured Logging Configuration

Provides centralized logging setup with JSON formatting for the application.
Replaces print() statements with proper structured logging.

Usage:
    from app.core.logging import setup_logging, logger
    
    # In main.py startup
    setup_logging()
    
    # In any module
    logger.info("User logged in", extra={"user_id": user.id, "email": user.email})
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler


def setup_logging(
    app_name: str = "student_tracker",
    level: str = "INFO",
    log_dir: str = "logs"
) -> logging.Logger:
    """
    Configure structured logging for the application.
    
    Args:
        app_name: Name of the application for log identification
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory to store log files
        
    Returns:
        Configured root logger
    """
    # Create logs directory if it doesn't exist
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)
    
    # Get root logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, level.upper()))
    
    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Console handler - human-readable format
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler with rotation - detailed format
    file_handler = RotatingFileHandler(
        log_path / 'app.log',
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # Error file handler - errors only
    error_handler = RotatingFileHandler(
        log_path / 'error.log',
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)
    logger.addHandler(error_handler)
    
    logger.info(f"Logging initialized for {app_name} at level {level}")
    
    return logger


# Convenience logger instance for direct import
logger = logging.getLogger(__name__)
