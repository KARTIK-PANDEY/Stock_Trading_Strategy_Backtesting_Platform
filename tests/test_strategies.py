"""
Quick validation tests for trading strategies

Run these tests to ensure the strategy framework is working correctly.
"""

import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.strategies import (
    MovingAverageCrossover,
    RSIStrategy,
    BollingerBandsStrategy,
    CombinedStrategy
)


def create_sample_data(num_days=252) -> pd.DataFrame:
    """Create sample OHLCV data for testing."""
    np.random.seed(42)
    
    dates = pd.date_range(start='2023-01-01', periods=num_days, freq='D')
    
    # Generate realistic-looking price data
    prices = 100 + np.cumsum(np.random.randn(num_days) * 2)
    prices = np.maximum(prices, 50)  # Ensure positive prices
    
    data = pd.DataFrame({
        'date': dates,
        'open': prices + np.random.randn(num_days) * 0.5,
        'high': prices + np.abs(np.random.randn(num_days) * 1),
        'low': prices - np.abs(np.random.randn(num_days) * 1),
        'close': prices,
        'volume': np.random.randint(1000000, 10000000, num_days),
        'ticker': 'TEST'
    })
    
    return data


def test_moving_average():
    """Test Moving Average Crossover strategy."""
    print("\n" + "="*60)
    print("Testing Moving Average Crossover Strategy")
    print("="*60)
    
    data = create_sample_data()
    
    # Test SMA
    strategy = MovingAverageCrossover(fast_period=20, slow_period=50, ma_type='SMA')
    result = strategy.generate_signals(data)
    
    assert 'fast_ma' in result.columns, "Missing fast_ma column"
    assert 'slow_ma' in result.columns, "Missing slow_ma column"
    assert 'signal' in result.columns, "Missing signal column"
    assert 'position' in result.columns, "Missing position column"
    assert result['signal'].isin([0, 1, -1]).all(), "Invalid signal values"
    
    print("✓ SMA strategy passed")
    
    # Test EMA
    strategy_ema = MovingAverageCrossover(fast_period=20, slow_period=50, ma_type='EMA')
    result_ema = strategy_ema.generate_signals(data)
    
    assert 'fast_ma' in result_ema.columns
    print("✓ EMA strategy passed")
    
    # Test long_only
    strategy_long = MovingAverageCrossover(fast_period=20, slow_period=50, long_only=True)
    result_long = strategy_long.generate_signals(data)
    
    assert (result_long['signal'] >= 0).all(), "Long-only strategy produced short signals"
    print("✓ Long-only mode passed")
    
    print(f"\nSignals generated: {(result['signal'] != 0).sum()}")
    print(f"Long signals: {(result['signal'] == 1).sum()}")
    print(f"Short signals: {(result['signal'] == -1).sum()}")


def test_rsi():
    """Test RSI strategy."""
    print("\n" + "="*60)
    print("Testing RSI Strategy")
    print("="*60)
    
    data = create_sample_data()
    
    strategy = RSIStrategy(period=14, oversold=30, overbought=70)
    result = strategy.generate_signals(data)
    
    assert 'rsi' in result.columns, "Missing RSI column"
    assert 'signal' in result.columns, "Missing signal column"
    assert result['signal'].isin([0, 1, -1]).all(), "Invalid signal values"
    
    # RSI should be between 0 and 100
    assert (result['rsi'] >= 0).all() and (result['rsi'] <= 100).all(), "RSI out of range"
    
    print("✓ RSI calculation passed")
    print(f"Average RSI: {result['rsi'].mean():.2f}")
    print(f"Signals generated: {(result['signal'] != 0).sum()}")
    
    # Test parameter validation
    try:
        invalid_strategy = RSIStrategy(period=-5)
        assert False, "Should have raised ValueError for negative period"
    except ValueError:
        print("✓ Parameter validation passed")


def test_bollinger_bands():
    """Test Bollinger Bands strategy."""
    print("\n" + "="*60)
    print("Testing Bollinger Bands Strategy")
    print("="*60)
    
    data = create_sample_data()
    
    strategy = BollingerBandsStrategy(period=20, num_std=2.0)
    result = strategy.generate_signals(data)
    
    assert 'bb_upper' in result.columns, "Missing upper band"
    assert 'bb_middle' in result.columns, "Missing middle band"
    assert 'bb_lower' in result.columns, "Missing lower band"
    assert 'bb_pct' in result.columns, "Missing %B indicator"
    assert 'signal' in result.columns, "Missing signal column"
    
    # Upper band should be >= middle >= lower (excluding NaN values)
    valid_data = result.dropna(subset=['bb_upper', 'bb_middle', 'bb_lower'])
    valid_bands = (valid_data['bb_upper'] >= valid_data['bb_middle']) & \
                  (valid_data['bb_middle'] >= valid_data['bb_lower'])
    assert valid_bands.all(), "Invalid Bollinger Band ordering"
    
    print("✓ Bollinger Bands calculation passed")
    print(f"Average %B: {result['bb_pct'].mean():.2f}")
    print(f"Signals generated: {(result['signal'] != 0).sum()}")


def test_combined_strategy():
    """Test combined strategy."""
    print("\n" + "="*60)
    print("Testing Combined Strategy")
    print("="*60)
    
    data = create_sample_data()
    
    # Create individual strategies
    ma = MovingAverageCrossover(fast_period=20, slow_period=50)
    rsi = RSIStrategy(period=14, oversold=30, overbought=70)
    bb = BollingerBandsStrategy(period=20, num_std=2.0)
    
    # Test unanimous
    combined_unanimous = CombinedStrategy(
        strategies=[ma, rsi, bb],
        combination_method='unanimous'
    )
    result_unanimous = combined_unanimous.generate_signals(data)
    
    assert 'signal' in result_unanimous.columns
    print("✓ Unanimous combination passed")
    
    # Test majority
    combined_majority = CombinedStrategy(
        strategies=[ma, rsi, bb],
        combination_method='majority'
    )
    result_majority = combined_majority.generate_signals(data)
    print("✓ Majority combination passed")
    
    # Combined should have fewer signals than individual (for unanimous)
    ma_signals = (ma.generate_signals(data)['signal'] != 0).sum()
    combined_signals = (result_unanimous['signal'] != 0).sum()
    
    print(f"\nMA signals: {ma_signals}")
    print(f"Combined (unanimous) signals: {combined_signals}")
    assert combined_signals <= ma_signals, "Combined should have fewer/equal signals"


def test_parameter_tuning():
    """Test parameter tuning."""
    print("\n" + "="*60)
    print("Testing Parameter Tuning")
    print("="*60)
    
    data = create_sample_data()
    
    strategy = RSIStrategy(period=14, oversold=30, overbought=70)
    original_params = strategy.get_parameter_info()
    
    print(f"Original parameters: {original_params}")
    
    # Update parameters
    strategy.update_parameters(oversold=25, overbought=75)
    updated_params = strategy.get_parameter_info()
    
    assert updated_params['parameters']['oversold'] == 25
    assert updated_params['parameters']['overbought'] == 75
    
    print(f"Updated parameters: {updated_params}")
    print("✓ Parameter tuning passed")


def run_all_tests():
    """Run all validation tests."""
    print("\n" + "="*60)
    print("STRATEGY FRAMEWORK VALIDATION TESTS")
    print("="*60)
    
    try:
        test_moving_average()
        test_rsi()
        test_bollinger_bands()
        test_combined_strategy()
        test_parameter_tuning()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60)
        print("\nThe strategy framework is working correctly.")
        print("You can now use it for backtesting.")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()
