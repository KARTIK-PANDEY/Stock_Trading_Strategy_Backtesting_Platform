"""
Example usage of the stock data ingestion pipeline

This script demonstrates:
1. Basic pipeline execution
2. Incremental loading
3. Data validation
4. Querying stored data
5. Error handling
"""

from src.ingestion.pipeline import run_pipeline, IngestionPipeline
from src.ingestion.storage import DuckDBStorage


def example_basic_usage():
    """Example 1: Basic pipeline usage"""
    print("\n" + "="*60)
    print("EXAMPLE 1: Basic Pipeline Usage")
    print("="*60)
    
    tickers = ['AAPL', 'MSFT', 'GOOGL']
    
    print(f"\nDownloading data for: {', '.join(tickers)}")
    results = run_pipeline(tickers=tickers)
    
    print(f"\n✓ Processed: {results['tickers_processed']}/{len(tickers)}")
    print(f"✓ Total rows inserted: {results['total_rows_inserted']}")
    print(f"✓ Duration: {results['duration_seconds']:.2f} seconds")
    
    if results['errors']:
        print(f"\n✗ Errors: {len(results['errors'])}")
        for error in results['errors']:
            print(f"  - {error}")
    
    if results['warnings']:
        print(f"\n⚠ Warnings: {len(results['warnings'])}")
        for warning in results['warnings'][:3]:  # Show first 3
            print(f"  - {warning}")


def example_incremental_loading():
    """Example 2: Incremental loading"""
    print("\n" + "="*60)
    print("EXAMPLE 2: Incremental Loading")
    print("="*60)
    
    ticker = 'TSLA'
    
    print(f"\nFirst run: Full historical load for {ticker}")
    results1 = run_pipeline(tickers=[ticker])
    print(f"✓ Inserted {results1['total_rows_inserted']} rows")
    
    print(f"\nSecond run: Incremental load (only new data)")
    results2 = run_pipeline(tickers=[ticker])
    print(f"✓ Inserted {results2['total_rows_inserted']} additional rows")


def example_custom_date_range():
    """Example 3: Custom date range"""
    print("\n" + "="*60)
    print("EXAMPLE 3: Custom Date Range")
    print("="*60)
    
    results = run_pipeline(
        tickers=['NVDA'],
        start_date='2023-01-01',
        end_date='2023-12-31',
        incremental=False  # Force full reload
    )
    
    print(f"\n✓ Downloaded 2023 data: {results['total_rows_inserted']} rows")


def example_validation_only():
    """Example 4: Validation without storage"""
    print("\n" + "="*60)
    print("EXAMPLE 4: Validation Only Mode")
    print("="*60)
    
    results = run_pipeline(
        tickers=['AMD', 'INTC'],
        validate_only=True
    )
    
    print(f"\n✓ Validated {results['tickers_processed']} tickers")
    print("(No data was stored)")
    
    if results['warnings']:
        print(f"\n⚠ Data quality warnings:")
        for warning in results['warnings']:
            print(f"  - {warning}")


def example_query_data():
    """Example 5: Query stored data"""
    print("\n" + "="*60)
    print("EXAMPLE 5: Query Stored Data")
    print("="*60)
    
    with DuckDBStorage() as storage:
        # Get all available tickers
        tickers = storage.get_available_tickers()
        print(f"\n✓ Available tickers: {', '.join(tickers)}")
        
        # Get data summary
        summary = storage.get_data_summary()
        print(f"\n✓ Data Summary:")
        print(summary.to_string(index=False))
        
        # Query specific ticker
        if tickers:
            ticker = tickers[0]
            df = storage.query_ticker_data(ticker, start_date='2024-01-01')
            print(f"\n✓ Latest {ticker} data (first 5 rows):")
            print(df.head())


def example_pipeline_summary():
    """Example 6: Get pipeline summary"""
    print("\n" + "="*60)
    print("EXAMPLE 6: Pipeline Summary")
    print("="*60)
    
    pipeline = IngestionPipeline()
    summary = pipeline.get_summary()
    
    if not summary.empty:
        print("\n✓ Pipeline Summary:")
        print(summary.to_string(index=False))
    else:
        print("\n⚠ No data in database yet. Run the pipeline first!")


def example_error_handling():
    """Example 7: Error handling"""
    print("\n" + "="*60)
    print("EXAMPLE 7: Error Handling")
    print("="*60)
    
    # Try with invalid ticker
    results = run_pipeline(tickers=['INVALID_TICKER_XYZ'])
    
    print(f"\n✓ Pipeline handled errors gracefully")
    print(f"  Failed: {results['tickers_failed']}")
    print(f"  Errors: {len(results['errors'])}")


def main():
    """Run all examples"""
    print("\n" + "="*60)
    print("STOCK DATA INGESTION PIPELINE - EXAMPLES")
    print("="*60)
    
    try:
        # Run examples
        example_basic_usage()
        example_incremental_loading()
        example_custom_date_range()
        example_validation_only()
        example_query_data()
        example_pipeline_summary()
        example_error_handling()
        
        print("\n" + "="*60)
        print("✓ ALL EXAMPLES COMPLETED SUCCESSFULLY")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n✗ Error running examples: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Run a simple example (change this to test different features)
    
    # Option 1: Run all examples
    # main()
    
    # Option 2: Run a quick test with popular stocks
    print("\nRunning quick example with tech stocks...")
    results = run_pipeline(tickers=['AAPL', 'MSFT', 'GOOGL'])
    
    print("\n" + "="*50)
    print("RESULTS SUMMARY")
    print("="*50)
    print(f"Processed: {results['tickers_processed']}")
    print(f"Failed: {results['tickers_failed']}")
    print(f"Rows inserted: {results['total_rows_inserted']}")
    print(f"Duration: {results['duration_seconds']:.2f}s")
    print("="*50)
    
    # Show data summary
    pipeline = IngestionPipeline()
    summary = pipeline.get_summary()
    if not summary.empty:
        print("\nData in database:")
        print(summary.to_string(index=False))
