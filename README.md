# Stock Data Ingestion Pipeline

Production-grade data ingestion pipeline for downloading historical stock data from Yahoo Finance and storing it in DuckDB.

## Features

- ✅ **Yahoo Finance Integration**: Download historical OHLCV data
- ✅ **DuckDB Storage**: Fast, embedded analytical database
- ✅ **Incremental Loading**: Only fetch new data since last update
- ✅ **Data Validation**: Schema and quality validation with automatic cleaning
- ✅ **Missing Data Handling**: Graceful error handling and logging
- ✅ **Structured Logging**: Comprehensive logging with rotation
- ✅ **Production-Ready**: Modular architecture with proper error handling

## Project Structure

```
Trading_Strategy_Backtesting_Platform/
├── src/
│   ├── ingestion/
│   │   ├── downloader.py    # Yahoo Finance data downloader
│   │   ├── storage.py       # DuckDB storage management
│   │   ├── validator.py     # Data validation
│   │   └── pipeline.py      # Pipeline orchestrator
│   ├── config/
│   │   └── settings.py      # Configuration management
│   └── utils/
│       └── logger.py        # Logging utilities
├── data/                    # DuckDB database storage
├── logs/                    # Pipeline execution logs
├── tests/                   # Unit tests
├── requirements.txt         # Python dependencies
├── .gitignore
├── .env.example
└── README.md
```

## Installation

### 1. Install Dependencies

```powershell
pip install -r requirements.txt
```

### 2. Configure Environment (Optional)

Copy `.env.example` to `.env` and customize:

```powershell
cp .env.example .env
```

## Usage

### Basic Usage

```python
from src.ingestion.pipeline import run_pipeline

# Download data for specific tickers
tickers = ['AAPL', 'MSFT', 'GOOGL']
results = run_pipeline(tickers=tickers)

print(f"Processed: {results['tickers_processed']}")
print(f"Total rows: {results['total_rows_inserted']}")
```

### Incremental Loading (Default)

```python
# First run: Downloads 5 years of historical data
run_pipeline(tickers=['AAPL'])

# Second run: Only downloads new data since last update
run_pipeline(tickers=['AAPL'])
```

### Full Refresh

```python
# Force full reload with specific date range
run_pipeline(
    tickers=['AAPL'],
    start_date='2020-01-01',
    end_date='2024-12-31',
    incremental=False
)
```

### Validation Only Mode

```python
# Validate data without storing
results = run_pipeline(
    tickers=['AAPL'],
    validate_only=True
)
```

### Get Data Summary

```python
from src.ingestion.pipeline import IngestionPipeline

pipeline = IngestionPipeline()
summary = pipeline.get_summary()
print(summary)
```

### Query Stored Data

```python
from src.ingestion.storage import DuckDBStorage

with DuckDBStorage() as storage:
    # Query specific ticker
    df = storage.query_ticker_data('AAPL', start_date='2024-01-01')
    print(df.head())
    
    # Get available tickers
    tickers = storage.get_available_tickers()
    print(f"Available tickers: {tickers}")
```

## Terminal Commands

### Run Complete Pipeline

```powershell
# Navigate to project directory
cd C:\Users\karti\Trading_Strategy_Backtesting_Platform

# Run pipeline for multiple tickers
python -c "from src.ingestion.pipeline import run_pipeline; run_pipeline(['AAPL', 'MSFT', 'GOOGL', 'TSLA'])"
```

### Check Pipeline Status

```powershell
# View logs
Get-Content logs\pipeline_*.log -Tail 50

# View errors only
Get-Content logs\errors_*.log
```

### Query Database

```powershell
python -c "from src.ingestion.storage import DuckDBStorage; storage = DuckDBStorage(); storage.connect(); print(storage.get_data_summary())"
```

### Test Individual Components

```powershell
# Test downloader
python -c "from src.ingestion.downloader import StockDataDownloader; d = StockDataDownloader(); df = d.download_ticker('AAPL'); print(df.head())"

# Test validator
python -c "from src.ingestion.validator import DataValidator; import pandas as pd; v = DataValidator(); print('Validator ready')"
```

## Configuration

### Settings (src/config/settings.py)

Key configuration options:

- `DATABASE_PATH`: DuckDB database file location
- `DEFAULT_START_DATE`: Default start date for historical data (5 years ago)
- `MAX_RETRIES`: Number of retry attempts for failed downloads (3)
- `RETRY_DELAY`: Delay between retries in seconds (2)
- `MIN_DATA_POINTS`: Minimum rows required for valid data (10)

### Environment Variables

Set via `.env` file or system environment:

- `LOG_LEVEL`: Logging level (INFO, DEBUG, WARNING, ERROR)
- `DATABASE_PATH`: Override default database path
- `MAX_RETRIES`: Override default retry count
- `RETRY_DELAY`: Override default retry delay

## Data Schema

### stock_prices Table

| Column     | Type      | Description                    |
|------------|-----------|--------------------------------|
| ticker     | VARCHAR   | Stock ticker symbol            |
| date       | DATE      | Trading date                   |
| open       | DOUBLE    | Opening price                  |
| high       | DOUBLE    | Highest price                  |
| low        | DOUBLE    | Lowest price                   |
| close      | DOUBLE    | Closing price                  |
| volume     | BIGINT    | Trading volume                 |
| adj_close  | DOUBLE    | Adjusted closing price         |
| created_at | TIMESTAMP | Record creation timestamp      |

**Primary Key**: (ticker, date)

## Validation Rules

### Schema Validation
- All required columns present
- Correct data types (string, date, numeric)
- Valid date formats

### Data Quality Validation
- No negative prices or volumes
- High >= Low constraint
- Minimum data points threshold
- No duplicate ticker-date combinations
- Detection of large date gaps (> 7 days)

## Logging

Logs are stored in the `logs/` directory:

- `pipeline_YYYYMMDD.log`: General pipeline execution logs
- `errors_YYYYMMDD.log`: Error-specific logs with stack traces

Log rotation: 10MB per file, 5 backup files retained

## Error Handling

The pipeline handles errors gracefully:

1. **API Failures**: Automatic retry with exponential backoff
2. **Invalid Data**: Logged and skipped, pipeline continues
3. **Missing Data**: Warnings logged, no data loss
4. **Schema Errors**: Data rejected, detailed error messages
5. **Quality Issues**: Automatic filtering of invalid rows

## Performance

- **Incremental Mode**: Only downloads new data, significantly faster
- **DuckDB**: Fast analytical queries on stored data
- **Connection Pooling**: Efficient database connection management
- **Batch Processing**: Multiple tickers processed in sequence

## Troubleshooting

### No Data Downloaded
- Check ticker symbol is valid
- Verify date range is reasonable
- Check network connectivity
- Review logs for API errors

### Schema Validation Failed
- Ensure yfinance package is up to date
- Check for API changes in Yahoo Finance
- Review error logs for specific issues

### Database Locked
- Ensure no other process is accessing the DuckDB file
- Close all connections properly
- Use context managers (`with` statements)

## Next Steps

- Add unit tests in `tests/` directory
- Implement data quality metrics dashboard
- Add support for multiple data sources
- Implement parallel ticker processing
- Add data export functionality

## License

MIT License - see repository for details
