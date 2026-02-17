"""Logging configuration and utilities"""
import logging
import sys
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import Optional

from src.config.settings import settings


def setup_logger(
    name: str,
    log_file: Optional[str] = None,
    level: Optional[str] = None
) -> logging.Logger:
    """
    Set up a logger with file and console handlers
    
    Args:
        name: Logger name
        log_file: Optional log file name (will be placed in logs directory)
        level: Optional log level (defaults to settings.log_level)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Set log level
    log_level = level or settings.log_level
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        settings.log_format,
        datefmt=settings.log_date_format
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (if log_file specified)
    if log_file:
        settings.ensure_directories()
        log_path = Path(settings.logs_dir) / log_file
        
        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_pipeline_logger() -> logging.Logger:
    """Get logger for pipeline operations"""
    timestamp = datetime.now().strftime("%Y%m%d")
    log_file = f"pipeline_{timestamp}.log"
    return setup_logger("pipeline", log_file=log_file)


def get_error_logger() -> logging.Logger:
    """Get logger for errors"""
    timestamp = datetime.now().strftime("%Y%m%d")
    log_file = f"errors_{timestamp}.log"
    return setup_logger("errors", log_file=log_file, level="ERROR")
