"""Stock data downloader using Yahoo Finance"""
import time
from typing import Optional, List
from datetime import datetime
import pandas as pd
import yfinance as yf

from src.config.settings import settings
from src.utils.logger import get_pipeline_logger

logger = get_pipeline_logger()


class StockDataDownloader:
    """Download historical stock data from Yahoo Finance"""
    
    def __init__(self, max_retries: Optional[int] = None, retry_delay: Optional[int] = None):
        """
        Initialize downloader
        
        Args:
            max_retries: Maximum number of retry attempts (defaults to settings)
            retry_delay: Delay between retries in seconds (defaults to settings)
        """
        self.max_retries = max_retries or settings.max_retries
        self.retry_delay = retry_delay or settings.retry_delay
    
    def download_ticker(
        self,
        ticker: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Optional[pd.DataFrame]:
        """
        Download historical data for a single ticker
        
        Args:
            ticker: Stock ticker symbol (e.g., 'AAPL')
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
        
        Returns:
            DataFrame with OHLCV data or None if download fails
        """
        start_date = start_date or settings.default_start_date
        end_date = end_date or settings.default_end_date
        
        logger.info(f"Downloading data for {ticker} from {start_date} to {end_date}")
        
        for attempt in range(self.max_retries):
            try:
                # Download data using yfinance
                stock = yf.Ticker(ticker)
                df = stock.history(start=start_date, end=end_date, auto_adjust=False)
                
                if df.empty:
                    logger.warning(f"No data returned for {ticker}")
                    return None
                
                # Reset index to make date a column
                df = df.reset_index()
                
                # Rename Date column if it exists
                if 'Date' in df.columns:
                    df = df.rename(columns={'Date': 'date'})
                elif 'index' in df.columns:
                    df = df.rename(columns={'index': 'date'})
                
                # Add ticker column
                df['ticker'] = ticker
                
                # Standardize column names
                column_mapping = {
                    'Open': 'open',
                    'High': 'high',
                    'Low': 'low',
                    'Close': 'close',
                    'Volume': 'volume',
                    'Adj Close': 'adj_close'
                }
                df = df.rename(columns=column_mapping)
                
                # Select only required columns
                required_cols = ['ticker', 'date', 'open', 'high', 'low', 'close', 'volume', 'adj_close']
                df = df[required_cols]
                
                # Convert date to datetime
                df['date'] = pd.to_datetime(df['date']).dt.date
                
                logger.info(f"Successfully downloaded {len(df)} rows for {ticker}")
                return df
                
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1}/{self.max_retries} failed for {ticker}: {str(e)}")
                
                if attempt < self.max_retries - 1:
                    logger.info(f"Retrying in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)
                else:
                    logger.error(f"Failed to download data for {ticker} after {self.max_retries} attempts")
                    return None
    
    def download_multiple_tickers(
        self,
        tickers: List[str],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> dict[str, Optional[pd.DataFrame]]:
        """
        Download historical data for multiple tickers
        
        Args:
            tickers: List of stock ticker symbols
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
        
        Returns:
            Dictionary mapping ticker symbols to DataFrames (or None if failed)
        """
        logger.info(f"Downloading data for {len(tickers)} tickers")
        
        results = {}
        for ticker in tickers:
            df = self.download_ticker(ticker, start_date, end_date)
            results[ticker] = df
            
            # Small delay to avoid rate limiting
            time.sleep(0.5)
        
        successful = sum(1 for df in results.values() if df is not None)
        logger.info(f"Successfully downloaded data for {successful}/{len(tickers)} tickers")
        
        return results
