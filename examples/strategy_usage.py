"""
Trading Strategy Framework - Example Usage

This script demonstrates how to use the trading strategy framework:
1. Loading data from DuckDB
2. Creating and configuring strategies
3. Generating trading signals
4. Parameter tuning
5. Combining multiple strategies
6. Visualizing results
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
from src.ingestion.storage import DuckDBStorage


# ============================================================================
# EXAMPLE 1: Basic Moving Average Crossover Strategy
# ============================================================================

def example_moving_average():
    """Demonstrate Moving Average Crossover strategy."""
    print("\n" + "="*70)
    print("EXAMPLE 1: Moving Average Crossover Strategy")
    print("="*70)
    
    # Load data from DuckDB
    with DuckDBStorage() as storage:
        # Get data for AAPL
        data = storage.query_ticker_data('AAPL', start_date='2023-01-01')
    
    if data.empty:
        print("No data available. Please run the ingestion pipeline first.")
        return
    
    # Create strategy with default parameters (20/50 SMA)
    strategy = MovingAverageCrossover(
        fast_period=20,
        slow_period=50,
        ma_type='SMA',
        long_only=False  # Allow both long and short positions
    )
    
    print(f"\nStrategy: {strategy}")
    print(f"Parameters: {strategy.get_parameter_info()}")
    
    # Generate signals
    result = strategy.generate_signals(data)
    
    # Display signal statistics
    print("\n--- Signal Statistics ---")
    print(f"Total periods: {len(result)}")
    print(f"Long signals: {(result['signal'] == 1).sum()}")
    print(f"Short signals: {(result['signal'] == -1).sum()}")
    print(f"Neutral periods: {(result['signal'] == 0).sum()}")
    
    # Show recent signals
    print("\n--- Recent Signals (Last 10 days) ---")
    display_cols = ['date', 'close', 'fast_ma', 'slow_ma', 'signal', 'position']
    print(result[display_cols].tail(10).to_string(index=False))
    
    return result


# ============================================================================
# EXAMPLE 2: RSI Mean-Reversion Strategy
# ============================================================================

def example_rsi():
    """Demonstrate RSI mean-reversion strategy."""
    print("\n" + "="*70)
    print("EXAMPLE 2: RSI Mean-Reversion Strategy")
    print("="*70)
    
    # Load data
    with DuckDBStorage() as storage:
        data = storage.query_ticker_data('AAPL', start_date='2023-01-01')
    
    if data.empty:
        print("No data available.")
        return
    
    # Create RSI strategy
    strategy = RSIStrategy(
        period=14,
        oversold=30,
        overbought=70,
        long_only=False
    )
    
    print(f"\nStrategy: {strategy}")
    
    # Generate signals
    result = strategy.generate_signals(data)
    
    # Display signal statistics
    print("\n--- Signal Statistics ---")
    print(f"Average RSI: {result['rsi'].mean():.2f}")
    print(f"RSI Std Dev: {result['rsi'].std():.2f}")
    print(f"Times oversold: {(result['rsi'] < 30).sum()}")
    print(f"Times overbought: {(result['rsi'] > 70).sum()}")
    print(f"Long signals: {(result['signal'] == 1).sum()}")
    print(f"Short signals: {(result['signal'] == -1).sum()}")
    
    # Show periods with extreme RSI
    print("\n--- Extreme RSI Periods ---")
    extreme = result[(result['rsi'] < 30) | (result['rsi'] > 70)]
    display_cols = ['date', 'close', 'rsi', 'signal', 'position']
    print(extreme[display_cols].tail(10).to_string(index=False))
    
    return result


# ============================================================================
# EXAMPLE 3: Bollinger Bands Strategy
# ============================================================================

def example_bollinger_bands():
    """Demonstrate Bollinger Bands mean-reversion strategy."""
    print("\n" + "="*70)
    print("EXAMPLE 3: Bollinger Bands Strategy")
    print("="*70)
    
    # Load data
    with DuckDBStorage() as storage:
        data = storage.query_ticker_data('AAPL', start_date='2023-01-01')
    
    if data.empty:
        print("No data available.")
        return
    
    # Create Bollinger Bands strategy
    strategy = BollingerBandsStrategy(
        period=20,
        num_std=2.0,
        ma_type='SMA',
        long_only=False
    )
    
    print(f"\nStrategy: {strategy}")
    
    # Generate signals
    result = strategy.generate_signals(data)
    
    # Display signal statistics
    print("\n--- Signal Statistics ---")
    print(f"Average %B: {result['bb_pct'].mean():.2f}")
    print(f"Times below lower band: {(result['bb_pct'] < 0).sum()}")
    print(f"Times above upper band: {(result['bb_pct'] > 1).sum()}")
    print(f"Long signals: {(result['signal'] == 1).sum()}")
    print(f"Short signals: {(result['signal'] == -1).sum()}")
    
    # Show periods when price touched bands
    print("\n--- Band Touch Events ---")
    band_touches = result[(result['bb_pct'] < 0.1) | (result['bb_pct'] > 0.9)]
    display_cols = ['date', 'close', 'bb_lower', 'bb_middle', 'bb_upper', 'bb_pct', 'signal']
    print(band_touches[display_cols].tail(10).to_string(index=False))
    
    return result


# ============================================================================
# EXAMPLE 4: Parameter Tuning
# ============================================================================

def example_parameter_tuning():
    """Demonstrate parameter tuning for optimization."""
    print("\n" + "="*70)
    print("EXAMPLE 4: Parameter Tuning")
    print("="*70)
    
    # Load data
    with DuckDBStorage() as storage:
        data = storage.query_ticker_data('AAPL', start_date='2023-01-01')
    
    if data.empty:
        print("No data available.")
        return
    
    # Test different RSI parameters
    print("\n--- Testing RSI Parameters ---")
    
    rsi_configs = [
        {'period': 10, 'oversold': 25, 'overbought': 75},
        {'period': 14, 'oversold': 30, 'overbought': 70},
        {'period': 20, 'oversold': 35, 'overbought': 65},
    ]
    
    results = []
    for config in rsi_configs:
        strategy = RSIStrategy(**config, long_only=False)
        result = strategy.generate_signals(data)
        
        # Calculate simple performance metric (number of signals)
        num_signals = (result['signal'] != 0).sum()
        
        results.append({
            'config': config,
            'num_signals': num_signals,
            'avg_rsi': result['rsi'].mean()
        })
        
        print(f"\nConfig: {config}")
        print(f"  Signals generated: {num_signals}")
        print(f"  Average RSI: {result['rsi'].mean():.2f}")
    
    # You can also update parameters dynamically
    print("\n--- Dynamic Parameter Update ---")
    strategy = RSIStrategy(period=14, oversold=30, overbought=70)
    print(f"Original: {strategy}")
    
    strategy.update_parameters(oversold=25, overbought=75)
    print(f"Updated: {strategy}")


# ============================================================================
# EXAMPLE 5: Combined Strategy
# ============================================================================

def example_combined_strategy():
    """Demonstrate combining multiple strategies."""
    print("\n" + "="*70)
    print("EXAMPLE 5: Combined Strategy")
    print("="*70)
    
    # Load data
    with DuckDBStorage() as storage:
        data = storage.query_ticker_data('AAPL', start_date='2023-01-01')
    
    if data.empty:
        print("No data available.")
        return
    
    # Create individual strategies
    ma_strategy = MovingAverageCrossover(fast_period=20, slow_period=50)
    rsi_strategy = RSIStrategy(period=14, oversold=30, overbought=70)
    bb_strategy = BollingerBandsStrategy(period=20, num_std=2.0)
    
    # Combine strategies with unanimous consensus
    combined = CombinedStrategy(
        strategies=[ma_strategy, rsi_strategy, bb_strategy],
        combination_method='unanimous'  # All must agree
    )
    
    print(f"\nCombined Strategy: {combined}")
    print("Method: All strategies must agree (unanimous)")
    
    # Generate signals
    result = combined.generate_signals(data)
    
    # Compare with individual strategies
    ma_result = ma_strategy.generate_signals(data)
    rsi_result = rsi_strategy.generate_signals(data)
    bb_result = bb_strategy.generate_signals(data)
    
    print("\n--- Signal Comparison ---")
    print(f"MA signals: {(ma_result['signal'] != 0).sum()}")
    print(f"RSI signals: {(rsi_result['signal'] != 0).sum()}")
    print(f"BB signals: {(bb_result['signal'] != 0).sum()}")
    print(f"Combined (unanimous): {(result['signal'] != 0).sum()}")
    
    # Show combined signals
    print("\n--- Combined Signals (Last 10) ---")
    display_cols = ['date', 'close', 'signal', 'position']
    print(result[display_cols].tail(10).to_string(index=False))
    
    return result


# ============================================================================
# EXAMPLE 6: Long-Only Strategy
# ============================================================================

def example_long_only():
    """Demonstrate long-only trading (no short positions)."""
    print("\n" + "="*70)
    print("EXAMPLE 6: Long-Only Strategy")
    print("="*70)
    
    # Load data
    with DuckDBStorage() as storage:
        data = storage.query_ticker_data('AAPL', start_date='2023-01-01')
    
    if data.empty:
        print("No data available.")
        return
    
    # Create long-only strategy
    strategy = MovingAverageCrossover(
        fast_period=20,
        slow_period=50,
        ma_type='EMA',  # Use EMA instead of SMA
        long_only=True  # Only long positions
    )
    
    print(f"\nStrategy: {strategy}")
    
    # Generate signals
    result = strategy.generate_signals(data)
    
    print("\n--- Signal Statistics ---")
    print(f"Long signals: {(result['signal'] == 1).sum()}")
    print(f"Short signals: {(result['signal'] == -1).sum()}")
    print(f"Neutral/Exit: {(result['signal'] == 0).sum()}")
    
    # Show entry/exit points
    entries_exits = result[result['signal'] != 0]
    display_cols = ['date', 'close', 'fast_ma', 'slow_ma', 'signal']
    print("\n--- Entry Points ---")
    print(entries_exits[display_cols].tail(10).to_string(index=False))
    
    return result


# ============================================================================
# EXAMPLE 7: Multiple Tickers
# ============================================================================

def example_multiple_tickers():
    """Demonstrate applying strategy to multiple tickers."""
    print("\n" + "="*70)
    print("EXAMPLE 7: Multiple Tickers")
    print("="*70)
    
    # Define tickers to analyze
    tickers = ['AAPL', 'MSFT', 'GOOGL']
    
    # Create strategy
    strategy = RSIStrategy(period=14, oversold=30, overbought=70, long_only=False)
    
    print(f"\nStrategy: {strategy}")
    print(f"Analyzing tickers: {tickers}\n")
    
    # Analyze each ticker
    with DuckDBStorage() as storage:
        for ticker in tickers:
            print(f"\n--- {ticker} ---")
            
            # Load data
            data = storage.query_ticker_data(ticker, start_date='2023-01-01')
            
            if data.empty:
                print(f"No data available for {ticker}")
                continue
            
            # Generate signals
            result = strategy.generate_signals(data)
            
            # Display statistics
            print(f"Average RSI: {result['rsi'].mean():.2f}")
            print(f"Current RSI: {result['rsi'].iloc[-1]:.2f}")
            print(f"Current signal: {result['signal'].iloc[-1]}")
            print(f"Total signals: {(result['signal'] != 0).sum()}")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Run all examples."""
    print("\n" + "="*70)
    print("TRADING STRATEGY FRAMEWORK - COMPREHENSIVE EXAMPLES")
    print("="*70)
    
    try:
        # Run all examples
        example_moving_average()
        example_rsi()
        example_bollinger_bands()
        example_parameter_tuning()
        example_combined_strategy()
        example_long_only()
        example_multiple_tickers()
        
        print("\n" + "="*70)
        print("All examples completed successfully!")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
