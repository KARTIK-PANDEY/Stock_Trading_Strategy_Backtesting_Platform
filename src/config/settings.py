"""Configuration settings for data ingestion pipeline"""
import os
from pathlib import Path
from typing import Optional
from datetime import datetime, timedelta

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Database configuration
DATABASE_DIR = PROJECT_ROOT / "data"
DATABASE_PATH = DATABASE_DIR / "stock_data.duckdb"

# Logging configuration
LOGS_DIR = PROJECT_ROOT / "logs"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Data ingestion configuration
DEFAULT_START_DATE = (datetime.now() - timedelta(days=365 * 5)).strftime("%Y-%m-%d")  # 5 years ago
DEFAULT_END_DATE = datetime.now().strftime("%Y-%m-%d")

# API configuration
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds
REQUEST_TIMEOUT = 30  # seconds

# Data validation configuration
REQUIRED_COLUMNS = ["Open", "High", "Low", "Close", "Volume", "Adj Close"]
MIN_DATA_POINTS = 10  # Minimum number of rows required for valid data


class Settings:
    """Application settings"""
    
    def __init__(self):
        self.database_path = str(DATABASE_PATH)
        self.logs_dir = str(LOGS_DIR)
        self.log_level = LOG_LEVEL
        self.log_format = LOG_FORMAT
        self.log_date_format = LOG_DATE_FORMAT
        self.default_start_date = DEFAULT_START_DATE
        self.default_end_date = DEFAULT_END_DATE
        self.max_retries = MAX_RETRIES
        self.retry_delay = RETRY_DELAY
        self.request_timeout = REQUEST_TIMEOUT
        self.required_columns = REQUIRED_COLUMNS
        self.min_data_points = MIN_DATA_POINTS
    
    def ensure_directories(self):
        """Ensure required directories exist"""
        DATABASE_DIR.mkdir(parents=True, exist_ok=True)
        LOGS_DIR.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()
