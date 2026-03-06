"""
Base Strategy Interface for Trading Strategies

This module provides an abstract base class that defines the interface
for all trading strategies in the backtesting platform.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import pandas as pd
import numpy as np


class BaseStrategy(ABC):
    """
    Abstract base class for all trading strategies.
    
    All concrete strategies must implement the generate_signals method.
    This provides a plug-and-play interface for adding new strategies.
    
    Attributes:
        name (str): Name of the strategy
        parameters (Dict[str, Any]): Strategy-specific parameters
    """
    
    def __init__(self, name: str, **parameters):
        """
        Initialize the strategy with parameters.
        
        Args:
            name (str): Name of the strategy
            **parameters: Strategy-specific parameters (e.g., window sizes, thresholds)
        """
        self.name = name
        self.parameters = parameters
        self._validate_parameters()
    
    @abstractmethod
    def _validate_parameters(self) -> None:
        """
        Validate strategy parameters.
        
        Raises:
            ValueError: If parameters are invalid
        """
        pass
    
    @abstractmethod
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate technical indicators required for the strategy.
        
        Args:
            data (pd.DataFrame): OHLCV price data with columns:
                - open, high, low, close, volume
                
        Returns:
            pd.DataFrame: Original data with added indicator columns
        """
        pass
    
    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Generate trading signals based on the strategy logic.
        
        Args:
            data (pd.DataFrame): OHLCV price data
            
        Returns:
            pd.DataFrame: Data with added columns:
                - signal: 1 (long), -1 (short), 0 (neutral/no position)
                - position: Actual position held (forward-filled signal)
        """
        pass
    
    def get_parameter_info(self) -> Dict[str, Any]:
        """
        Get information about strategy parameters.
        
        Returns:
            Dict[str, Any]: Strategy name and parameters
        """
        return {
            'name': self.name,
            'parameters': self.parameters
        }
    
    def update_parameters(self, **new_parameters) -> None:
        """
        Update strategy parameters for parameter tuning.
        
        Args:
            **new_parameters: New parameter values to update
        """
        self.parameters.update(new_parameters)
        self._validate_parameters()
    
    def __repr__(self) -> str:
        """String representation of the strategy."""
        params_str = ', '.join(f"{k}={v}" for k, v in self.parameters.items())
        return f"{self.name}({params_str})"


class SignalGenerator:
    """
    Utility class for common signal generation operations.
    
    Provides helper methods for generating trading signals from
    various conditions and patterns.
    """
    
    @staticmethod
    def generate_crossover_signal(
        fast: pd.Series,
        slow: pd.Series,
        long_only: bool = False
    ) -> pd.Series:
        """
        Generate signals based on crossover of two series.
        
        Args:
            fast (pd.Series): Fast-moving indicator
            slow (pd.Series): Slow-moving indicator
            long_only (bool): If True, only generate long signals
            
        Returns:
            pd.Series: Signal series (1 for long, -1 for short, 0 for neutral)
        """
        signal = pd.Series(0, index=fast.index)
        
        # Long signal: fast crosses above slow
        signal[fast > slow] = 1
        
        if not long_only:
            # Short signal: fast crosses below slow
            signal[fast < slow] = -1
        
        return signal
    
    @staticmethod
    def generate_threshold_signal(
        indicator: pd.Series,
        upper_threshold: float,
        lower_threshold: float,
        invert: bool = False
    ) -> pd.Series:
        """
        Generate signals based on indicator crossing thresholds.
        
        Args:
            indicator (pd.Series): Technical indicator values
            upper_threshold (float): Upper threshold (overbought)
            lower_threshold (float): Lower threshold (oversold)
            invert (bool): If True, invert the signals (for mean-reversion)
            
        Returns:
            pd.Series: Signal series (1 for long, -1 for short, 0 for neutral)
        """
        signal = pd.Series(0, index=indicator.index)
        
        if not invert:
            # Momentum strategy: buy strength, sell weakness
            signal[indicator > upper_threshold] = 1
            signal[indicator < lower_threshold] = -1
        else:
            # Mean reversion: buy oversold, sell overbought
            signal[indicator < lower_threshold] = 1
            signal[indicator > upper_threshold] = -1
        
        return signal
    
    @staticmethod
    def apply_position_sizing(
        signal: pd.Series,
        method: str = 'fixed'
    ) -> pd.Series:
        """
        Apply position sizing to signals.
        
        Args:
            signal (pd.Series): Raw trading signals
            method (str): Position sizing method ('fixed', 'scaled')
            
        Returns:
            pd.Series: Position series with sizing applied
        """
        if method == 'fixed':
            # Fixed position: hold until signal changes
            return signal.replace(0, np.nan).ffill().fillna(0)
        else:
            # Can implement other methods (volatility-based, etc.)
            return signal
