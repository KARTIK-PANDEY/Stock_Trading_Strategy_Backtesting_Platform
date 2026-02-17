"""DuckDB storage management for stock data"""
from typing import Optional, List
from datetime import datetime, date
import pandas as pd
import duckdb

from src.config.settings import settings
from src.utils.logger import get_pipeline_logger

logger = get_pipeline_logger()


class DuckDBStorage:
    """Manage stock data storage in DuckDB"""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize DuckDB storage
        
        Args:
            db_path: Path to DuckDB database file (defaults to settings)
        """
        self.db_path = db_path or settings.database_path
        self.conn = None
        settings.ensure_directories()
    
    def connect(self) -> duckdb.DuckDBPyConnection:
        """
        Establish connection to DuckDB
        
        Returns:
            DuckDB connection object
        """
        if self.conn is None:
            logger.info(f"Connecting to DuckDB at {self.db_path}")
            self.conn = duckdb.connect(self.db_path)
            self._initialize_schema()
        return self.conn
    
    def _initialize_schema(self):
        """Create tables if they don't exist"""
        logger.info("Initializing database schema")
        
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS stock_prices (
            ticker VARCHAR NOT NULL,
            date DATE NOT NULL,
            open DOUBLE,
            high DOUBLE,
            low DOUBLE,
            close DOUBLE,
            volume BIGINT,
            adj_close DOUBLE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (ticker, date)
        )
        """
        
        self.conn.execute(create_table_sql)
        
        # Create index for better query performance
        try:
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_ticker_date ON stock_prices(ticker, date)")
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_date ON stock_prices(date)")
        except Exception as e:
            logger.warning(f"Index creation warning (may already exist): {e}")
        
        logger.info("Schema initialization complete")
    
    def get_last_date(self, ticker: str) -> Optional[date]:
        """
        Get the last available date for a ticker
        
        Args:
            ticker: Stock ticker symbol
        
        Returns:
            Last date as date object, or None if ticker not found
        """
        query = """
        SELECT MAX(date) as last_date 
        FROM stock_prices 
        WHERE ticker = ?
        """
        
        result = self.conn.execute(query, [ticker]).fetchone()
        
        if result and result[0]:
            logger.info(f"Last date for {ticker}: {result[0]}")
            return result[0]
        
        logger.info(f"No existing data found for {ticker}")
        return None
    
    def upsert_data(self, df: pd.DataFrame) -> int:
        """
        Insert or update stock data
        
        Args:
            df: DataFrame with stock data
        
        Returns:
            Number of rows affected
        """
        if df is None or df.empty:
            logger.warning("Attempted to upsert empty DataFrame")
            return 0
        
        ticker = df['ticker'].iloc[0]
        logger.info(f"Upserting {len(df)} rows for {ticker}")
        
        try:
            # Delete existing records for the date range to avoid duplicates
            min_date = df['date'].min()
            max_date = df['date'].max()
            
            delete_sql = """
            DELETE FROM stock_prices 
            WHERE ticker = ? AND date BETWEEN ? AND ?
            """
            self.conn.execute(delete_sql, [ticker, min_date, max_date])
            
            # Insert new data
            insert_sql = """
            INSERT INTO stock_prices (ticker, date, open, high, low, close, volume, adj_close)
            SELECT ticker, date, open, high, low, close, volume, adj_close
            FROM df
            """
            self.conn.execute(insert_sql)
            
            rows_affected = len(df)
            logger.info(f"Successfully upserted {rows_affected} rows for {ticker}")
            return rows_affected
            
        except Exception as e:
            logger.error(f"Error upserting data for {ticker}: {str(e)}")
            raise
    
    def bulk_upsert(self, data_dict: dict[str, pd.DataFrame]) -> dict[str, int]:
        """
        Bulk upsert data for multiple tickers
        
        Args:
            data_dict: Dictionary mapping ticker symbols to DataFrames
        
        Returns:
            Dictionary mapping ticker symbols to row counts
        """
        results = {}
        
        for ticker, df in data_dict.items():
            if df is not None:
                try:
                    rows = self.upsert_data(df)
                    results[ticker] = rows
                except Exception as e:
                    logger.error(f"Failed to upsert {ticker}: {str(e)}")
                    results[ticker] = 0
            else:
                results[ticker] = 0
        
        return results
    
    def query_ticker_data(
        self,
        ticker: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Query data for a specific ticker
        
        Args:
            ticker: Stock ticker symbol
            start_date: Optional start date filter (YYYY-MM-DD)
            end_date: Optional end date filter (YYYY-MM-DD)
        
        Returns:
            DataFrame with stock data
        """
        query = "SELECT * FROM stock_prices WHERE ticker = ?"
        params = [ticker]
        
        if start_date:
            query += " AND date >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND date <= ?"
            params.append(end_date)
        
        query += " ORDER BY date"
        
        df = self.conn.execute(query, params).fetchdf()
        logger.info(f"Retrieved {len(df)} rows for {ticker}")
        return df
    
    def get_available_tickers(self) -> List[str]:
        """
        Get list of all tickers in the database
        
        Returns:
            List of ticker symbols
        """
        query = "SELECT DISTINCT ticker FROM stock_prices ORDER BY ticker"
        result = self.conn.execute(query).fetchdf()
        tickers = result['ticker'].tolist()
        logger.info(f"Found {len(tickers)} tickers in database")
        return tickers
    
    def get_data_summary(self) -> pd.DataFrame:
        """
        Get summary statistics for stored data
        
        Returns:
            DataFrame with summary by ticker
        """
        query = """
        SELECT 
            ticker,
            MIN(date) as start_date,
            MAX(date) as end_date,
            COUNT(*) as row_count,
            MAX(created_at) as last_updated
        FROM stock_prices
        GROUP BY ticker
        ORDER BY ticker
        """
        df = self.conn.execute(query).fetchdf()
        return df
    
    def close(self):
        """Close database connection"""
        if self.conn:
            logger.info("Closing DuckDB connection")
            self.conn.close()
            self.conn = None
    
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
