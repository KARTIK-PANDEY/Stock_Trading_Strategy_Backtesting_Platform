"""Main data ingestion pipeline orchestrator"""
from typing import List, Optional, Dict
from datetime import datetime, timedelta
import pandas as pd

from src.ingestion.downloader import StockDataDownloader
from src.ingestion.storage import DuckDBStorage
from src.ingestion.validator import DataValidator
from src.config.settings import settings
from src.utils.logger import get_pipeline_logger, get_error_logger

logger = get_pipeline_logger()
error_logger = get_error_logger()


class IngestionPipeline:
    """Orchestrate the stock data ingestion pipeline"""
    
    def __init__(self, incremental: bool = True):
        """
        Initialize pipeline
        
        Args:
            incremental: If True, only download data since last update
        """
        self.downloader = StockDataDownloader()
        self.storage = DuckDBStorage()
        self.validator = DataValidator()
        self.incremental = incremental
    
    def run(
        self,
        tickers: List[str],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        validate_only: bool = False
    ) -> Dict[str, any]:
        """
        Run the complete ingestion pipeline
        
        Args:
            tickers: List of stock ticker symbols
            start_date: Optional start date (YYYY-MM-DD)
            end_date: Optional end date (YYYY-MM-DD)
            validate_only: If True, only validate without storing
        
        Returns:
            Dictionary with pipeline execution results
        """
        logger.info(f"Starting pipeline for {len(tickers)} tickers")
        logger.info(f"Incremental mode: {self.incremental}")
        
        start_time = datetime.now()
        results = {
            'tickers_processed': 0,
            'tickers_failed': 0,
            'total_rows_inserted': 0,
            'errors': [],
            'warnings': []
        }
        
        try:
            # Connect to database
            self.storage.connect()
            
            # Process each ticker
            for ticker in tickers:
                try:
                    logger.info(f"Processing ticker: {ticker}")
                    
                    # Determine date range
                    download_start = start_date
                    download_end = end_date or settings.default_end_date
                    
                    if self.incremental and not start_date:
                        last_date = self.storage.get_last_date(ticker)
                        if last_date:
                            # Download from day after last date
                            download_start = (last_date + timedelta(days=1)).strftime('%Y-%m-%d')
                            logger.info(f"Incremental load: fetching data from {download_start}")
                        else:
                            download_start = settings.default_start_date
                            logger.info(f"Full load: no existing data found")
                    else:
                        download_start = start_date or settings.default_start_date
                    
                    # Download data
                    df = self.downloader.download_ticker(
                        ticker=ticker,
                        start_date=download_start,
                        end_date=download_end
                    )
                    
                    if df is None or df.empty:
                        logger.warning(f"No data downloaded for {ticker}")
                        results['warnings'].append(f"{ticker}: No data available")
                        continue
                    
                    # Validate data
                    is_valid, schema_errors, quality_warnings = self.validator.validate(df)
                    
                    if schema_errors:
                        error_msg = f"{ticker}: Schema validation failed - {schema_errors}"
                        logger.error(error_msg)
                        error_logger.error(error_msg)
                        results['errors'].append(error_msg)
                        results['tickers_failed'] += 1
                        continue
                    
                    if quality_warnings:
                        warning_msg = f"{ticker}: Data quality warnings - {quality_warnings}"
                        logger.warning(warning_msg)
                        results['warnings'].append(warning_msg)
                        
                        # Attempt to clean data
                        df = self.validator.filter_invalid_rows(df)
                        
                        if df.empty:
                            error_msg = f"{ticker}: All rows filtered out due to quality issues"
                            logger.error(error_msg)
                            results['errors'].append(error_msg)
                            results['tickers_failed'] += 1
                            continue
                    
                    # Store data (unless validate_only mode)
                    if not validate_only:
                        rows_inserted = self.storage.upsert_data(df)
                        results['total_rows_inserted'] += rows_inserted
                        logger.info(f"Stored {rows_inserted} rows for {ticker}")
                    else:
                        logger.info(f"Validation-only mode: skipped storage for {ticker}")
                    
                    results['tickers_processed'] += 1
                    
                except Exception as e:
                    error_msg = f"{ticker}: Pipeline error - {str(e)}"
                    logger.error(error_msg)
                    error_logger.error(error_msg, exc_info=True)
                    results['errors'].append(error_msg)
                    results['tickers_failed'] += 1
            
            # Log summary
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            logger.info("="*50)
            logger.info("PIPELINE EXECUTION SUMMARY")
            logger.info("="*50)
            logger.info(f"Duration: {duration:.2f} seconds")
            logger.info(f"Tickers processed: {results['tickers_processed']}/{len(tickers)}")
            logger.info(f"Tickers failed: {results['tickers_failed']}")
            logger.info(f"Total rows inserted: {results['total_rows_inserted']}")
            logger.info(f"Errors: {len(results['errors'])}")
            logger.info(f"Warnings: {len(results['warnings'])}")
            logger.info("="*50)
            
            results['duration_seconds'] = duration
            
        except Exception as e:
            error_msg = f"Pipeline fatal error: {str(e)}"
            logger.error(error_msg)
            error_logger.error(error_msg, exc_info=True)
            results['errors'].append(error_msg)
        
        finally:
            # Close database connection
            self.storage.close()
        
        return results
    
    def get_summary(self) -> pd.DataFrame:
        """
        Get summary of stored data
        
        Returns:
            DataFrame with summary statistics
        """
        try:
            self.storage.connect()
            summary = self.storage.get_data_summary()
            self.storage.close()
            return summary
        except Exception as e:
            logger.error(f"Error getting summary: {str(e)}")
            return pd.DataFrame()


def run_pipeline(
    tickers: List[str],
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    incremental: bool = True,
    validate_only: bool = False
) -> Dict[str, any]:
    """
    Convenience function to run the pipeline
    
    Args:
        tickers: List of stock ticker symbols
        start_date: Optional start date (YYYY-MM-DD)
        end_date: Optional end date (YYYY-MM-DD)
        incremental: If True, only download new data
        validate_only: If True, only validate without storing
    
    Returns:
        Dictionary with pipeline execution results
    """
    pipeline = IngestionPipeline(incremental=incremental)
    return pipeline.run(
        tickers=tickers,
        start_date=start_date,
        end_date=end_date,
        validate_only=validate_only
    )
