# Trading Strategy Framework - Complete Guide

## 📋 Overview

A **production-ready, plug-and-play framework** for implementing and backtesting trading strategies with Python. Features vectorized calculations, parameter tuning, and support for both long and short positions.

## 🎯 What's Included

### Core Components

1. **Base Strategy Interface** (`src/strategies/base.py`)
   - Abstract base class for creating custom strategies
   - Signal generator utilities
   - Parameter validation framework

2. **Technical Strategies** (`src/strategies/technical.py`)
   - Moving Average Crossover (SMA/EMA)
   - RSI Mean-Reversion
   - Bollinger Bands
   - Combined Strategy (ensemble methods)

3. **Example Usage** (`examples/strategy_usage.py`)
   - 7 comprehensive examples
   - Real-world integration with DuckDB
   - Parameter tuning demonstrations

4. **Validation Tests** (`tests/test_strategies.py`)
   - Automated testing suite
   - Ensures correctness of all strategies

## 🚀 Quick Start

### 1. Test the Framework

```powershell
# Validate that everything works
python tests/test_strategies.py
```

Expected output:
```
✅ ALL TESTS PASSED!
The strategy framework is working correctly.
```

### 2. Run Examples

```powershell
# Run all examples
python examples/strategy_usage.py

# Or run individual examples
python -c "from examples.strategy_usage import example_moving_average; example_moving_average()"
```

### 3. Create Your First Strategy

```python
from src.strategies import MovingAverageCrossover
from src.ingestion.storage import DuckDBStorage

# Load data
with DuckDBStorage() as storage:
    data = storage.query_ticker_data('AAPL', start_date='2023-01-01')

# Create strategy
strategy = MovingAverageCrossover(
    fast_period=20,
    slow_period=50,
    ma_type='SMA',
    long_only=False
)

# Generate signals
result = strategy.generate_signals(data)

# View results
print(result[['date', 'close', 'signal', 'position']].tail())
```

## 📊 Built-in Strategies

### 1. Moving Average Crossover

**Use Case**: Trend following

**Parameters**:
- `fast_period` (int): Fast MA period, default 20
- `slow_period` (int): Slow MA period, default 50
- `ma_type` (str): 'SMA' or 'EMA', default 'SMA'
- `long_only` (bool): Only long positions, default False

**Example**:
```python
strategy = MovingAverageCrossover(
    fast_period=20,
    slow_period=50,
    ma_type='EMA',
    long_only=False
)
```

### 2. RSI Strategy

**Use Case**: Mean reversion / Overbought-oversold

**Parameters**:
- `period` (int): RSI period, default 14
- `oversold` (float): Oversold threshold (0-100), default 30
- `overbought` (float): Overbought threshold (0-100), default 70
- `long_only` (bool): Only long positions, default False

**Example**:
```python
strategy = RSIStrategy(
    period=14,
    oversold=30,
    overbought=70,
    long_only=False
)
```

### 3. Bollinger Bands

**Use Case**: Mean reversion / Volatility breakout

**Parameters**:
- `period` (int): MA period, default 20
- `num_std` (float): Standard deviations, default 2.0
- `ma_type` (str): 'SMA' or 'EMA', default 'SMA'
- `long_only` (bool): Only long positions, default False

**Example**:
```python
strategy = BollingerBandsStrategy(
    period=20,
    num_std=2.0,
    ma_type='SMA',
    long_only=False
)
```

### 4. Combined Strategy

**Use Case**: Ensemble methods / Strategy confirmation

**Parameters**:
- `strategies` (list): List of strategy instances
- `combination_method` (str): 'unanimous', 'majority', or 'any'

**Example**:
```python
# Create individual strategies
ma = MovingAverageCrossover(fast_period=20, slow_period=50)
rsi = RSIStrategy(period=14, oversold=30, overbought=70)
bb = BollingerBandsStrategy(period=20, num_std=2.0)

# Combine with unanimous voting
combined = CombinedStrategy(
    strategies=[ma, rsi, bb],
    combination_method='unanimous'
)
```

## 🔧 Advanced Features

### Parameter Tuning

```python
# Create strategy
strategy = RSIStrategy(period=14, oversold=30, overbought=70)

# Test different parameters
for period in [10, 14, 20]:
    strategy.update_parameters(period=period)
    result = strategy.generate_signals(data)
    signals = (result['signal'] != 0).sum()
    print(f"Period {period}: {signals} signals")
```

### Long-Only Mode

```python
# For accounts without short capability
strategy = MovingAverageCrossover(
    fast_period=20,
    slow_period=50,
    long_only=True  # No short positions
)
```

### Multiple Tickers

```python
tickers = ['AAPL', 'MSFT', 'GOOGL']
strategy = RSIStrategy(period=14, oversold=30, overbought=70)

for ticker in tickers:
    data = storage.query_ticker_data(ticker, start_date='2023-01-01')
    result = strategy.generate_signals(data)
    print(f"{ticker}: {(result['signal'] != 0).sum()} signals")
```

## 🛠️ Creating Custom Strategies

Extend `BaseStrategy` to create your own:

```python
from src.strategies.base import BaseStrategy, SignalGenerator
import pandas as pd

class MyCustomStrategy(BaseStrategy):
    """Custom trading strategy."""
    
    def __init__(self, my_param=10):
        super().__init__(
            name='MyCustomStrategy',
            my_param=my_param
        )
    
    def _validate_parameters(self) -> None:
        """Validate parameters."""
        if self.parameters['my_param'] <= 0:
            raise ValueError("my_param must be positive")
    
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate indicators (vectorized)."""
        df = data.copy()
        df['my_indicator'] = df['close'].rolling(
            window=self.parameters['my_param']
        ).mean()
        return df
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """Generate trading signals."""
        df = self.calculate_indicators(data)
        
        # Signal logic
        df['signal'] = 0
        df.loc[df['close'] > df['my_indicator'], 'signal'] = 1
        df.loc[df['close'] < df['my_indicator'], 'signal'] = -1
        
        # Convert to positions
        df['position'] = SignalGenerator.apply_position_sizing(df['signal'])
        
        return df
```

## 📈 Signal Format

All strategies return a DataFrame with:

| Column | Type | Description |
|--------|------|-------------|
| `signal` | int | 1 (long), -1 (short), 0 (neutral) |
| `position` | int | Actual position held (forward-filled) |
| + strategy-specific indicators | varies | e.g., `fast_ma`, `rsi`, `bb_upper` |

## ⚡ Performance Features

- ✅ **Vectorized Operations**: All calculations use pandas vectorization
- ✅ **No Python Loops**: Efficient rolling windows and boolean indexing
- ✅ **Memory Efficient**: Copy-on-write semantics
- ✅ **Fast Execution**: Can process years of data in seconds

## 🧪 Testing Your Strategies

```python
# Run validation tests
python tests/test_strategies.py

# Test your custom strategy
from tests.test_strategies import create_sample_data

data = create_sample_data()
strategy = MyCustomStrategy()
result = strategy.generate_signals(data)

# Verify signal quality
assert result['signal'].isin([0, 1, -1]).all()
assert 'position' in result.columns
print(f"Generated {(result['signal'] != 0).sum()} signals")
```

## 📝 Best Practices

1. **Always Vectorize**: Use pandas operations, never Python loops
2. **Validate Parameters**: Implement thorough validation in `_validate_parameters()`
3. **Avoid Look-Ahead Bias**: Only use past data for signal generation
4. **Handle NaN Values**: Account for initial periods with insufficient data
5. **Document Thoroughly**: Clear docstrings for all methods
6. **Test Extensively**: Validate with multiple timeframes and tickers

## 🔗 Integration Points

### With Data Ingestion Pipeline

```python
from src.ingestion.pipeline import run_pipeline
from src.strategies import MovingAverageCrossover
from src.ingestion.storage import DuckDBStorage

# Download fresh data
run_pipeline(tickers=['AAPL', 'MSFT'])

# Generate signals
with DuckDBStorage() as storage:
    data = storage.query_ticker_data('AAPL')
    
strategy = MovingAverageCrossover()
signals = strategy.generate_signals(data)
```

### For Backtesting

The signal format is ready for backtesting:
- `position` column shows actual holdings
- `signal` column shows entry/exit points
- All indicators available for analysis

## 📚 File Structure

```
Trading_Strategy_Backtesting_Platform/
├── src/
│   └── strategies/
│       ├── __init__.py          # Module exports
│       ├── base.py              # Abstract base class
│       ├── technical.py         # Concrete strategies
│       └── README.md            # Detailed documentation
├── examples/
│   └── strategy_usage.py        # 7 comprehensive examples
├── tests/
│   └── test_strategies.py       # Validation tests
└── STRATEGY_FRAMEWORK_GUIDE.md  # This file
```

## 🎓 Learning Path

1. **Start**: Run `python tests/test_strategies.py` to validate setup
2. **Explore**: Run `python examples/strategy_usage.py` to see all features
3. **Experiment**: Modify parameters in example strategies
4. **Create**: Build your own custom strategy
5. **Backtest**: Integrate signals with backtesting engine

## 💡 Example Workflows

### Workflow 1: Quick Signal Generation

```python
from src.strategies import RSIStrategy
from src.ingestion.storage import DuckDBStorage

with DuckDBStorage() as storage:
    data = storage.query_ticker_data('AAPL', start_date='2023-01-01')

strategy = RSIStrategy()
result = strategy.generate_signals(data)

# Latest signal
print(f"Current RSI: {result['rsi'].iloc[-1]:.2f}")
print(f"Current signal: {result['signal'].iloc[-1]}")
```

### Workflow 2: Parameter Optimization

```python
from src.strategies import MovingAverageCrossover
from src.ingestion.storage import DuckDBStorage

with DuckDBStorage() as storage:
    data = storage.query_ticker_data('AAPL', start_date='2023-01-01')

# Test different parameter combinations
best_config = None
max_signals = 0

for fast in [10, 20, 30]:
    for slow in [40, 50, 60]:
        if fast >= slow:
            continue
            
        strategy = MovingAverageCrossover(fast_period=fast, slow_period=slow)
        result = strategy.generate_signals(data)
        signals = (result['signal'] != 0).sum()
        
        if signals > max_signals:
            max_signals = signals
            best_config = (fast, slow)

print(f"Best config: fast={best_config[0]}, slow={best_config[1]}")
```

### Workflow 3: Multi-Strategy Confirmation

```python
from src.strategies import (
    MovingAverageCrossover,
    RSIStrategy,
    BollingerBandsStrategy,
    CombinedStrategy
)

# Create strategies
strategies = [
    MovingAverageCrossover(fast_period=20, slow_period=50),
    RSIStrategy(period=14, oversold=30, overbought=70),
    BollingerBandsStrategy(period=20, num_std=2.0)
]

# Require all to agree for high-confidence signals
combined = CombinedStrategy(strategies=strategies, combination_method='unanimous')

result = combined.generate_signals(data)
high_confidence_signals = result[result['signal'] != 0]

print(f"High-confidence signals: {len(high_confidence_signals)}")
```

## 🤝 Contributing

To add a new strategy:

1. Extend `BaseStrategy` in `src/strategies/technical.py`
2. Implement all abstract methods
3. Add comprehensive docstrings
4. Export in `src/strategies/__init__.py`
5. Add example to `examples/strategy_usage.py`
6. Add test to `tests/test_strategies.py`

## 📄 License

MIT License - see repository root for details

---

**Ready to start building trading strategies?** Run the examples or validation tests to begin!

```powershell
# Test the framework
python tests/test_strategies.py

# Run all examples
python examples/strategy_usage.py
```
