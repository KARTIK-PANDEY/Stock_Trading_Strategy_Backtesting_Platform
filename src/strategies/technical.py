"""
Technical Trading Strategies

This module implements concrete trading strategies based on
technical indicators: Moving Average, RSI, and Bollinger Bands.
All calculations are vectorized using pandas for performance.
"""

import pandas as pd
import numpy as np
from typing import Optional
from .base import BaseStrategy, SignalGenerator


class MovingAverageCrossover(BaseStrategy):
    """
    Moving Average Crossover Strategy
    
    Generates signals based on the crossover of two moving averages.
    - Long signal: Fast MA crosses above Slow MA
    - Short signal: Fast MA crosses below Slow MA
    
    Parameters:
        fast_period (int): Period for fast moving average (default: 20)
        slow_period (int): Period for slow moving average (default: 50)
        ma_type (str): Type of MA ('SMA' or 'EMA') (default: 'SMA')
        long_only (bool): Only generate long signals (default: False)
    """
    
    def __init__(
        self,
        fast_period: int = 20,
        slow_period: int = 50,
        ma_type: str = 'SMA',
        long_only: bool = False
    ):
        """
        Initialize Moving Average Crossover strategy.
        
        Args:
            fast_period: Fast MA period
            slow_period: Slow MA period
            ma_type: Type of moving average ('SMA' or 'EMA')
            long_only: If True, only generate long signals
        """
        super().__init__(
            name='MovingAverageCrossover',
            fast_period=fast_period,
            slow_period=slow_period,
            ma_type=ma_type,
            long_only=long_only
        )
    
    def _validate_parameters(self) -> None:
        """Validate strategy parameters."""
        fast = self.parameters['fast_period']
        slow = self.parameters['slow_period']
        ma_type = self.parameters['ma_type']
        
        if fast <= 0 or slow <= 0:
            raise ValueError("MA periods must be positive integers")
        
        if fast >= slow:
            raise ValueError(f"Fast period ({fast}) must be less than slow period ({slow})")
        
        if ma_type not in ['SMA', 'EMA']:
            raise ValueError(f"ma_type must be 'SMA' or 'EMA', got '{ma_type}'")
    
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate moving averages using vectorized operations.
        
        Args:
            data: OHLCV price data
            
        Returns:
            DataFrame with added MA columns
        """
        df = data.copy()
        fast_period = self.parameters['fast_period']
        slow_period = self.parameters['slow_period']
        ma_type = self.parameters['ma_type']
        
        # Vectorized MA calculations
        if ma_type == 'SMA':
            # Simple Moving Average
            df['fast_ma'] = df['close'].rolling(window=fast_period).mean()
            df['slow_ma'] = df['close'].rolling(window=slow_period).mean()
        else:
            # Exponential Moving Average
            df['fast_ma'] = df['close'].ewm(span=fast_period, adjust=False).mean()
            df['slow_ma'] = df['close'].ewm(span=slow_period, adjust=False).mean()
        
        return df
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Generate trading signals based on MA crossover.
        
        Args:
            data: OHLCV price data
            
        Returns:
            DataFrame with signal and position columns
        """
        # Calculate indicators
        df = self.calculate_indicators(data)
        
        # Generate crossover signals (vectorized)
        df['signal'] = SignalGenerator.generate_crossover_signal(
            fast=df['fast_ma'],
            slow=df['slow_ma'],
            long_only=self.parameters['long_only']
        )
        
        # Convert signals to positions (forward fill)
        df['position'] = SignalGenerator.apply_position_sizing(df['signal'])
        
        return df


class RSIStrategy(BaseStrategy):
    """
    Relative Strength Index (RSI) Strategy
    
    Mean-reversion strategy based on RSI indicator.
    - Long signal: RSI crosses below oversold threshold
    - Short signal: RSI crosses above overbought threshold
    
    Parameters:
        period (int): RSI calculation period (default: 14)
        oversold (float): Oversold threshold (default: 30)
        overbought (float): Overbought threshold (default: 70)
        long_only (bool): Only generate long signals (default: False)
    """
    
    def __init__(
        self,
        period: int = 14,
        oversold: float = 30,
        overbought: float = 70,
        long_only: bool = False
    ):
        """
        Initialize RSI strategy.
        
        Args:
            period: RSI calculation period
            oversold: Oversold threshold (0-100)
            overbought: Overbought threshold (0-100)
            long_only: If True, only generate long signals
        """
        super().__init__(
            name='RSIStrategy',
            period=period,
            oversold=oversold,
            overbought=overbought,
            long_only=long_only
        )
    
    def _validate_parameters(self) -> None:
        """Validate strategy parameters."""
        period = self.parameters['period']
        oversold = self.parameters['oversold']
        overbought = self.parameters['overbought']
        
        if period <= 0:
            raise ValueError("RSI period must be a positive integer")
        
        if not (0 <= oversold <= 100) or not (0 <= overbought <= 100):
            raise ValueError("RSI thresholds must be between 0 and 100")
        
        if oversold >= overbought:
            raise ValueError(f"Oversold ({oversold}) must be less than overbought ({overbought})")
    
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate RSI using vectorized operations.
        
        RSI = 100 - (100 / (1 + RS))
        where RS = Average Gain / Average Loss
        
        Args:
            data: OHLCV price data
            
        Returns:
            DataFrame with RSI column
        """
        df = data.copy()
        period = self.parameters['period']
        
        # Calculate price changes (vectorized)
        delta = df['close'].diff()
        
        # Separate gains and losses
        gains = delta.where(delta > 0, 0.0)
        losses = -delta.where(delta < 0, 0.0)
        
        # Calculate exponential moving averages of gains and losses
        avg_gains = gains.ewm(span=period, adjust=False).mean()
        avg_losses = losses.ewm(span=period, adjust=False).mean()
        
        # Calculate RS and RSI (vectorized)
        rs = avg_gains / avg_losses
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # Handle edge cases
        df['rsi'] = df['rsi'].fillna(50)  # Neutral RSI when no data
        
        return df
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Generate trading signals based on RSI thresholds.
        
        Args:
            data: OHLCV price data
            
        Returns:
            DataFrame with signal and position columns
        """
        # Calculate RSI
        df = self.calculate_indicators(data)
        
        oversold = self.parameters['oversold']
        overbought = self.parameters['overbought']
        long_only = self.parameters['long_only']
        
        # Generate mean-reversion signals (vectorized)
        # Buy when oversold, sell when overbought
        df['signal'] = SignalGenerator.generate_threshold_signal(
            indicator=df['rsi'],
            upper_threshold=overbought,
            lower_threshold=oversold,
            invert=True  # Mean reversion: buy low, sell high
        )
        
        # Only long signals if specified
        if long_only:
            df['signal'] = df['signal'].clip(lower=0)
        
        # Convert signals to positions
        df['position'] = SignalGenerator.apply_position_sizing(df['signal'])
        
        return df


class BollingerBandsStrategy(BaseStrategy):
    """
    Bollinger Bands Strategy
    
    Mean-reversion strategy based on Bollinger Bands.
    - Long signal: Price touches or crosses below lower band
    - Short signal: Price touches or crosses above upper band
    - Exit: Price returns to middle band
    
    Parameters:
        period (int): Moving average period (default: 20)
        num_std (float): Number of standard deviations (default: 2.0)
        ma_type (str): Type of MA ('SMA' or 'EMA') (default: 'SMA')
        long_only (bool): Only generate long signals (default: False)
    """
    
    def __init__(
        self,
        period: int = 20,
        num_std: float = 2.0,
        ma_type: str = 'SMA',
        long_only: bool = False
    ):
        """
        Initialize Bollinger Bands strategy.
        
        Args:
            period: Moving average period
            num_std: Number of standard deviations for bands
            ma_type: Type of moving average ('SMA' or 'EMA')
            long_only: If True, only generate long signals
        """
        super().__init__(
            name='BollingerBandsStrategy',
            period=period,
            num_std=num_std,
            ma_type=ma_type,
            long_only=long_only
        )
    
    def _validate_parameters(self) -> None:
        """Validate strategy parameters."""
        period = self.parameters['period']
        num_std = self.parameters['num_std']
        ma_type = self.parameters['ma_type']
        
        if period <= 0:
            raise ValueError("Period must be a positive integer")
        
        if num_std <= 0:
            raise ValueError("Number of standard deviations must be positive")
        
        if ma_type not in ['SMA', 'EMA']:
            raise ValueError(f"ma_type must be 'SMA' or 'EMA', got '{ma_type}'")
    
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate Bollinger Bands using vectorized operations.
        
        Upper Band = MA + (num_std * standard deviation)
        Middle Band = MA
        Lower Band = MA - (num_std * standard deviation)
        
        Args:
            data: OHLCV price data
            
        Returns:
            DataFrame with Bollinger Bands columns
        """
        df = data.copy()
        period = self.parameters['period']
        num_std = self.parameters['num_std']
        ma_type = self.parameters['ma_type']
        
        # Calculate middle band (moving average) - vectorized
        if ma_type == 'SMA':
            df['bb_middle'] = df['close'].rolling(window=period).mean()
            # Calculate standard deviation
            std = df['close'].rolling(window=period).std()
        else:
            df['bb_middle'] = df['close'].ewm(span=period, adjust=False).mean()
            # Calculate standard deviation for EMA
            std = df['close'].ewm(span=period, adjust=False).std()
        
        # Calculate upper and lower bands (vectorized)
        df['bb_upper'] = df['bb_middle'] + (std * num_std)
        df['bb_lower'] = df['bb_middle'] - (std * num_std)
        
        # Calculate %B indicator (position within bands)
        # %B = (Close - Lower Band) / (Upper Band - Lower Band)
        df['bb_pct'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
        
        return df
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Generate trading signals based on Bollinger Bands.
        
        Args:
            data: OHLCV price data
            
        Returns:
            DataFrame with signal and position columns
        """
        # Calculate Bollinger Bands
        df = self.calculate_indicators(data)
        
        long_only = self.parameters['long_only']
        
        # Initialize signals
        df['signal'] = 0
        
        # Vectorized signal generation
        # Long signal: price touches/crosses below lower band (%B < 0)
        df.loc[df['bb_pct'] < 0, 'signal'] = 1
        
        # Short signal: price touches/crosses above upper band (%B > 1)
        if not long_only:
            df.loc[df['bb_pct'] > 1, 'signal'] = -1
        
        # Exit signal: price returns to middle band (0.4 < %B < 0.6)
        # This creates a neutral zone around the middle
        middle_zone = (df['bb_pct'] > 0.4) & (df['bb_pct'] < 0.6)
        df.loc[middle_zone, 'signal'] = 0
        
        # Convert signals to positions
        df['position'] = SignalGenerator.apply_position_sizing(df['signal'])
        
        return df


class CombinedStrategy(BaseStrategy):
    """
    Combined Strategy Framework
    
    Allows combining multiple strategies with custom logic.
    Can be used for ensemble methods or confirmation-based strategies.
    
    Parameters:
        strategies (list): List of strategy instances
        combination_method (str): How to combine signals ('unanimous', 'majority', 'any')
    """
    
    def __init__(self, strategies: list, combination_method: str = 'unanimous'):
        """
        Initialize combined strategy.
        
        Args:
            strategies: List of BaseStrategy instances
            combination_method: Method to combine signals
        """
        super().__init__(
            name='CombinedStrategy',
            strategies=strategies,
            combination_method=combination_method
        )
    
    def _validate_parameters(self) -> None:
        """Validate strategy parameters."""
        strategies = self.parameters['strategies']
        method = self.parameters['combination_method']
        
        if not strategies or not isinstance(strategies, list):
            raise ValueError("Must provide a list of strategies")
        
        if method not in ['unanimous', 'majority', 'any']:
            raise ValueError(f"Invalid combination method: {method}")
    
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate indicators for all sub-strategies.
        
        Args:
            data: OHLCV price data
            
        Returns:
            DataFrame with all indicators
        """
        df = data.copy()
        
        # Calculate indicators for each strategy
        for i, strategy in enumerate(self.parameters['strategies']):
            strategy_df = strategy.calculate_indicators(data)
            
            # Add strategy-specific columns with prefixes
            for col in strategy_df.columns:
                if col not in data.columns:
                    df[f's{i}_{col}'] = strategy_df[col]
        
        return df
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Generate combined signals from multiple strategies.
        
        Args:
            data: OHLCV price data
            
        Returns:
            DataFrame with combined signal and position columns
        """
        df = data.copy()
        strategies = self.parameters['strategies']
        method = self.parameters['combination_method']
        
        # Generate signals for each strategy
        strategy_signals = []
        for strategy in strategies:
            strategy_df = strategy.generate_signals(data)
            strategy_signals.append(strategy_df['signal'])
        
        # Combine signals based on method
        signals_df = pd.DataFrame(strategy_signals).T
        
        if method == 'unanimous':
            # All strategies must agree
            df['signal'] = signals_df.apply(
                lambda row: row.iloc[0] if len(set(row)) == 1 else 0,
                axis=1
            )
        elif method == 'majority':
            # Majority vote
            df['signal'] = signals_df.mode(axis=1)[0]
        else:  # 'any'
            # Any strategy can trigger
            df['signal'] = signals_df.abs().max(axis=1) * signals_df.sum(axis=1).apply(np.sign)
        
        # Convert signals to positions
        df['position'] = SignalGenerator.apply_position_sizing(df['signal'])
        
        return df
