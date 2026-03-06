# Trading Strategy Framework

A **plug-and-play, reusable framework** for implementing and backtesting trading strategies with support for technical indicators, parameter tuning, and signal generation.

## 🚀 Features

- ✅ **Abstract Base Class**: Easy-to-extend interface for custom strategies
- ✅ **Vectorized Calculations**: Fast pandas-based indicator computations
- ✅ **Built-in Strategies**: Moving Average, RSI, Bollinger Bands
- ✅ **Parameter Tuning**: Dynamic parameter updates for optimization
- ✅ **Long/Short Signals**: Support for both long and short positions
- ✅ **Strategy Combination**: Combine multiple strategies with different voting methods
- ✅ **Production Ready**: Comprehensive validation and error handling

## 📋 Architecture

```
src/strategies/
├── base.py          # Abstract base class and signal generator utilities
├── technical.py     # Concrete strategy implementations
├── __init__.py      # Module exports
└── README.md        # This file
```

## 🎯 Quick Start

### 1. Basic Moving Average Strategy

```python
from src.strategies import MovingAverageCrossover
from src.ingestion.storage import DuckDBStorage

# Load price data
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

# View signals
print(result[['date', 'close', 'fast_ma', 'slow_ma', 'signal', 'position']].tail())
```

### 2. RSI Mean-Reversion Strategy

```python
from src.strategies import RSIStrategy

strategy = RSIStrategy(
    period=14,
    oversold=30,
    overbought=70,
    long_only=False
)

result = strategy.generate_signals(data)
print(result[['date', 'close', 'rsi', 'signal', 'position']].tail())
```

### 3. Bollinger Bands Strategy

```python
from src.strategies import BollingerBandsStrategy

strategy = BollingerBandsStrategy(
    period=20,
    num_std=2.0,
    ma_type='SMA',
    long_only=False
)

result = strategy.generate_signals(data)
print(result[['date', 'close', 'bb_lower', 'bb_middle', 'bb_upper', 'signal']].tail())
```

## 📊 Available Strategies

### 1. Moving Average Crossover

**Parameters:**
- `fast_period` (int): Fast MA period (default: 20)
- `slow_period` (int): Slow MA period (default: 50)
- `ma_type` (str): 'SMA' or 'EMA' (default: 'SMA')
- `long_only` (bool): Only long positions (default: False)

**Signal Logic:**
- **Long**: Fast MA > Slow MA
- **Short**: Fast MA < Slow MA

### 2. RSI Strategy

**Parameters:**
- `period` (int): RSI calculation period (default: 14)
- `oversold` (float): Oversold threshold 0-100 (default: 30)
- `overbought` (float): Overbought threshold 0-100 (default: 70)
- `long_only` (bool): Only long positions (default: False)

**Signal Logic (Mean Reversion):**
- **Long**: RSI < oversold threshold
- **Short**: RSI > overbought threshold

### 3. Bollinger Bands Strategy

**Parameters:**
- `period` (int): MA period (default: 20)
- `num_std` (float): Standard deviations (default: 2.0)
- `ma_type` (str): 'SMA' or 'EMA' (default: 'SMA')
- `long_only` (bool): Only long positions (default: False)

**Signal Logic:**
- **Long**: Price touches/crosses below lower band
- **Short**: Price touches/crosses above upper band
- **Exit**: Price returns to middle band

## 🔧 Advanced Features

### Parameter Tuning

```python
# Create strategy with initial parameters
strategy = RSIStrategy(period=14, oversold=30, overbought=70)

# Update parameters dynamically
strategy.update_parameters(oversold=25, overbought=75)

# Test multiple parameter combinations
for period in [10, 14, 20]:
    strategy.update_parameters(period=period)
    result = strategy.generate_signals(data)
    print(f"Period {period}: {(result['signal'] != 0).sum()} signals")
```

### Combining Multiple Strategies

```python
from src.strategies import CombinedStrategy

# Create individual strategies
ma_strategy = MovingAverageCrossover(fast_period=20, slow_period=50)
rsi_strategy = RSIStrategy(period=14, oversold=30, overbought=70)
bb_strategy = BollingerBandsStrategy(period=20, num_std=2.0)

# Combine with unanimous voting (all must agree)
combined = CombinedStrategy(
    strategies=[ma_strategy, rsi_strategy, bb_strategy],
    combination_method='unanimous'
)

result = combined.generate_signals(data)
```

**Combination Methods:**
- `unanimous`: All strategies must agree
- `majority`: Majority vote wins
- `any`: Any strategy can trigger signal

### Long-Only Mode

```python
# Only generate long signals (useful for accounts without short capability)
strategy = MovingAverageCrossover(
    fast_period=20,
    slow_period=50,
    long_only=True
)
```

## 🛠️ Creating Custom Strategies

Extend `BaseStrategy` to create your own strategy:

```python
from src.strategies.base import BaseStrategy, SignalGenerator
import pandas as pd

class CustomStrategy(BaseStrategy):
    """Your custom trading strategy."""
    
    def __init__(self, param1=10, param2=20):
        super().__init__(
            name='CustomStrategy',
            param1=param1,
            param2=param2
        )
    
    def _validate_parameters(self) -> None:
        """Validate parameters."""
        if self.parameters['param1'] <= 0:
            raise ValueError("param1 must be positive")
    
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate custom indicators."""
        df = data.copy()
        
        # Your indicator calculations here (vectorized)
        df['custom_indicator'] = df['close'].rolling(
            window=self.parameters['param1']
        ).mean()
        
        return df
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """Generate trading signals."""
        df = self.calculate_indicators(data)
        
        # Your signal logic here
        df['signal'] = 0
        df.loc[df['custom_indicator'] > df['close'], 'signal'] = 1
        
        # Convert to positions
        df['position'] = SignalGenerator.apply_position_sizing(df['signal'])
        
        return df
```

## 📈 Signal Format

All strategies return a DataFrame with these columns:

| Column | Type | Description |
|--------|------|-------------|
| `signal` | int | Raw signal: 1 (long), -1 (short), 0 (neutral) |
| `position` | int | Actual position held (forward-filled signal) |

Additional columns depend on the strategy (e.g., `fast_ma`, `slow_ma`, `rsi`, etc.)

## 🔍 Signal Statistics

```python
result = strategy.generate_signals(data)

# Count signals
long_signals = (result['signal'] == 1).sum()
short_signals = (result['signal'] == -1).sum()
neutral = (result['signal'] == 0).sum()

print(f"Long: {long_signals}, Short: {short_signals}, Neutral: {neutral}")

# View signal changes (entries/exits)
signal_changes = result[result['signal'] != 0]
print(signal_changes[['date', 'close', 'signal']])
```

## 🎓 Example Usage

See `examples/strategy_usage.py` for comprehensive examples:

```powershell
# Run all examples
python examples/strategy_usage.py

# Or run in Python
cd C:\Users\karti\Trading_Strategy_Backtesting_Platform
python -c "from examples.strategy_usage import example_moving_average; example_moving_average()"
```

## ⚡ Performance

All calculations are **vectorized** using pandas for maximum performance:

- ✅ No Python loops in indicator calculations
- ✅ Efficient rolling window operations
- ✅ Fast boolean indexing for signal generation
- ✅ Minimal memory footprint with in-place operations

## 🧪 Testing Strategies

```python
# Test strategy with historical data
strategy = MovingAverageCrossover(fast_period=20, slow_period=50)
result = strategy.generate_signals(data)

# Analyze signal quality
print(f"Strategy: {strategy}")
print(f"Total signals: {(result['signal'] != 0).sum()}")
print(f"Signal ratio: {(result['signal'] != 0).sum() / len(result):.2%}")

# Check for look-ahead bias (signals should never use future data)
assert result['signal'].notna().all(), "Signals contain NaN values"
```

## 📝 Best Practices

1. **Always validate parameters** in `_validate_parameters()`
2. **Use vectorized operations** for all calculations
3. **Avoid look-ahead bias** - only use past data for signal generation
4. **Test with multiple timeframes** and tickers
5. **Document your strategy logic** clearly
6. **Handle edge cases** (missing data, insufficient history)

## 🔗 Integration with Backtesting

The strategy framework integrates seamlessly with the data ingestion pipeline:

```python
from src.ingestion.storage import DuckDBStorage
from src.strategies import MovingAverageCrossover

# Load data
with DuckDBStorage() as storage:
    data = storage.query_ticker_data('AAPL', start_date='2020-01-01')

# Generate signals
strategy = MovingAverageCrossover()
signals = strategy.generate_signals(data)

# Signals ready for backtesting!
```

## 📚 Further Reading

- [Pandas Rolling Windows](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.rolling.html)
- [Technical Analysis Indicators](https://www.investopedia.com/terms/t/technicalindicator.asp)
- [Vectorization in Pandas](https://pandas.pydata.org/docs/user_guide/enhancingperf.html)

## 🤝 Contributing

To add a new strategy:

1. Create a new class in `technical.py` extending `BaseStrategy`
2. Implement all abstract methods
3. Add comprehensive docstrings
4. Export in `__init__.py`
5. Add example usage to `examples/strategy_usage.py`

## 📄 License

MIT License - see repository root for details
