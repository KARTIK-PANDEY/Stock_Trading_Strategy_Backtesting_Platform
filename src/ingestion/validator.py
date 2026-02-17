"""Data validation for stock market data"""
from typing import List, Tuple, Optional
import pandas as pd

from src.config.settings import settings
from src.utils.logger import get_pipeline_logger

logger = get_pipeline_logger()


class DataValidator:
    """Validate stock data schema and quality"""
    
    def __init__(self):
        """Initialize validator"""
        self.required_columns = ['ticker', 'date', 'open', 'high', 'low', 'close', 'volume', 'adj_close']
    
    def validate_schema(self, df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """
        Validate DataFrame schema
        
        Args:
            df: DataFrame to validate
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        if df is None or df.empty:
            errors.append("DataFrame is None or empty")
            return False, errors
        
        # Check required columns
        missing_cols = set(self.required_columns) - set(df.columns)
        if missing_cols:
            errors.append(f"Missing required columns: {missing_cols}")
        
        # Check data types
        if 'ticker' in df.columns and not pd.api.types.is_string_dtype(df['ticker']):
            errors.append("Column 'ticker' must be string type")
        
        if 'date' in df.columns:
            # Check if date is already date type or can be converted
            try:
                pd.to_datetime(df['date'])
            except Exception as e:
                errors.append(f"Column 'date' must be valid date format: {str(e)}")
        
        # Check numeric columns
        numeric_cols = ['open', 'high', 'low', 'close', 'adj_close']
        for col in numeric_cols:
            if col in df.columns and not pd.api.types.is_numeric_dtype(df[col]):
                errors.append(f"Column '{col}' must be numeric type")
        
        if 'volume' in df.columns and not pd.api.types.is_numeric_dtype(df['volume']):
            errors.append("Column 'volume' must be numeric type")
        
        is_valid = len(errors) == 0
        
        if is_valid:
            logger.info("Schema validation passed")
        else:
            logger.error(f"Schema validation failed: {errors}")
        
        return is_valid, errors
    
    def validate_data_quality(self, df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """
        Validate data quality
        
        Args:
            df: DataFrame to validate
        
        Returns:
            Tuple of (is_valid, list_of_warnings)
        """
        warnings = []
        
        if df is None or df.empty:
            warnings.append("DataFrame is None or empty")
            return False, warnings
        
        # Check minimum data points
        if len(df) < settings.min_data_points:
            warnings.append(f"Insufficient data: {len(df)} rows (minimum: {settings.min_data_points})")
        
        # Check for negative prices
        price_cols = ['open', 'high', 'low', 'close', 'adj_close']
        for col in price_cols:
            if col in df.columns:
                negative_count = (df[col] < 0).sum()
                if negative_count > 0:
                    warnings.append(f"Found {negative_count} negative values in '{col}'")
        
        # Check for negative volume
        if 'volume' in df.columns:
            negative_volume = (df['volume'] < 0).sum()
            if negative_volume > 0:
                warnings.append(f"Found {negative_volume} negative values in 'volume'")
        
        # Check high >= low constraint
        if 'high' in df.columns and 'low' in df.columns:
            invalid_high_low = (df['high'] < df['low']).sum()
            if invalid_high_low > 0:
                warnings.append(f"Found {invalid_high_low} rows where high < low")
        
        # Check for missing values
        null_counts = df[self.required_columns].isnull().sum()
        cols_with_nulls = null_counts[null_counts > 0]
        if not cols_with_nulls.empty:
            for col, count in cols_with_nulls.items():
                warnings.append(f"Column '{col}' has {count} missing values")
        
        # Check for duplicate dates per ticker
        if 'ticker' in df.columns and 'date' in df.columns:
            duplicates = df.duplicated(subset=['ticker', 'date']).sum()
            if duplicates > 0:
                warnings.append(f"Found {duplicates} duplicate ticker-date combinations")
        
        # Check date continuity (detect large gaps)
        if 'date' in df.columns and len(df) > 1:
            df_sorted = df.sort_values('date')
            df_sorted['date_dt'] = pd.to_datetime(df_sorted['date'])
            date_diffs = df_sorted['date_dt'].diff().dt.days
            large_gaps = date_diffs[date_diffs > 7].count()  # Gaps > 1 week
            if large_gaps > 0:
                warnings.append(f"Found {large_gaps} date gaps larger than 7 days")
        
        is_valid = len(warnings) == 0
        
        if is_valid:
            logger.info("Data quality validation passed")
        else:
            logger.warning(f"Data quality issues found: {warnings}")
        
        return is_valid, warnings
    
    def validate(self, df: pd.DataFrame) -> Tuple[bool, List[str], List[str]]:
        """
        Run complete validation (schema + quality)
        
        Args:
            df: DataFrame to validate
        
        Returns:
            Tuple of (is_valid, schema_errors, quality_warnings)
        """
        schema_valid, schema_errors = self.validate_schema(df)
        
        # Only run quality checks if schema is valid
        if schema_valid:
            quality_valid, quality_warnings = self.validate_data_quality(df)
        else:
            quality_warnings = ["Skipped quality validation due to schema errors"]
            quality_valid = False
        
        is_valid = schema_valid and quality_valid
        
        ticker = df['ticker'].iloc[0] if 'ticker' in df.columns and not df.empty else 'Unknown'
        
        if is_valid:
            logger.info(f"Validation passed for {ticker}")
        else:
            logger.warning(f"Validation issues for {ticker}")
        
        return is_valid, schema_errors, quality_warnings
    
    def filter_invalid_rows(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Remove rows with invalid data
        
        Args:
            df: DataFrame to filter
        
        Returns:
            Filtered DataFrame
        """
        if df is None or df.empty:
            return df
        
        original_len = len(df)
        
        # Remove rows with negative prices
        price_cols = ['open', 'high', 'low', 'close', 'adj_close']
        for col in price_cols:
            if col in df.columns:
                df = df[df[col] >= 0]
        
        # Remove rows with negative volume
        if 'volume' in df.columns:
            df = df[df['volume'] >= 0]
        
        # Remove rows where high < low
        if 'high' in df.columns and 'low' in df.columns:
            df = df[df['high'] >= df['low']]
        
        # Remove rows with missing required data
        df = df.dropna(subset=['ticker', 'date', 'close'])
        
        removed = original_len - len(df)
        if removed > 0:
            logger.warning(f"Filtered out {removed} invalid rows")
        
        return df
