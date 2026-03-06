"""
Trading Strategies Module

This module provides a plug-and-play framework for implementing
and backtesting trading strategies.
"""

from .base import BaseStrategy, SignalGenerator
from .technical import (
    MovingAverageCrossover,
    RSIStrategy,
    BollingerBandsStrategy,
    CombinedStrategy
)

__all__ = [
    'BaseStrategy',
    'SignalGenerator',
    'MovingAverageCrossover',
    'RSIStrategy',
    'BollingerBandsStrategy',
    'CombinedStrategy'
]
