"""
Performance Metrics Module

Calculates comprehensive trading performance metrics including
Sharpe ratio, maximum drawdown, CAGR, win rate, and more.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict


@dataclass
class PerformanceMetrics:
    """
    Container for performance metrics.
    
    All metrics commonly used in trading strategy evaluation.
    """
    # Returns metrics
    total_return: float = 0.0
    annualized_return: float = 0.0
    cagr: float = 0.0
    
    # Risk metrics
    volatility: float = 0.0
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    calmar_ratio: float = 0.0
    
    # Drawdown metrics
    max_drawdown: float = 0.0
    max_drawdown_duration: int = 0
    avg_drawdown: float = 0.0
    
    # Trade metrics
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    
    # Profit metrics
    avg_win: float = 0.0
    avg_loss: float = 0.0
    profit_factor: float = 0.0
    expectancy: float = 0.0
    
    # Additional metrics
    best_trade: float = 0.0
    worst_trade: float = 0.0
    longest_win_streak: int = 0
    longest_loss_streak: int = 0
    
    def to_dict(self) -> Dict:
        """Convert metrics to dictionary."""
        return asdict(self)
    
    def to_dataframe(self) -> pd.DataFrame:
        """Convert metrics to DataFrame."""
        return pd.DataFrame([self.to_dict()]).T
    
    def summary(self) -> str:
        """Generate formatted summary string."""
        lines = [
            "="*60,
            "PERFORMANCE SUMMARY",
            "="*60,
            "",
            "Returns:",
            f"  Total Return:       {self.total_return:>12.2%}",
            f"  CAGR:               {self.cagr:>12.2%}",
            f"  Annualized Return:  {self.annualized_return:>12.2%}",
            "",
            "Risk:",
            f"  Volatility:         {self.volatility:>12.2%}",
            f"  Sharpe Ratio:       {self.sharpe_ratio:>12.2f}",
            f"  Sortino Ratio:      {self.sortino_ratio:>12.2f}",
            f"  Calmar Ratio:       {self.calmar_ratio:>12.2f}",
            "",
            "Drawdown:",
            f"  Max Drawdown:       {self.max_drawdown:>12.2%}",
            f"  Avg Drawdown:       {self.avg_drawdown:>12.2%}",
            f"  Max DD Duration:    {self.max_drawdown_duration:>12} days",
            "",
            "Trading:",
            f"  Total Trades:       {self.total_trades:>12}",
            f"  Win Rate:           {self.win_rate:>12.2%}",
            f"  Profit Factor:      {self.profit_factor:>12.2f}",
            f"  Expectancy:         ${self.expectancy:>11.2f}",
            "",
            "Wins/Losses:",
            f"  Winning Trades:     {self.winning_trades:>12}",
            f"  Losing Trades:      {self.losing_trades:>12}",
            f"  Avg Win:            ${self.avg_win:>11.2f}",
            f"  Avg Loss:           ${self.avg_loss:>11.2f}",
            f"  Best Trade:         ${self.best_trade:>11.2f}",
            f"  Worst Trade:        ${self.worst_trade:>11.2f}",
            "",
            "="*60
        ]
        return "\n".join(lines)


class PerformanceCalculator:
    """
    Calculates comprehensive performance metrics for backtesting results.
    """
    
    def __init__(self, risk_free_rate: float = 0.02):
        """
        Initialize calculator.
        
        Args:
            risk_free_rate: Annual risk-free rate for Sharpe/Sortino (default: 2%)
        """
        self.risk_free_rate = risk_free_rate
    
    def calculate_metrics(
        self,
        equity_curve: pd.Series,
        trades: Optional[List] = None,
        periods_per_year: int = 252
    ) -> PerformanceMetrics:
        """
        Calculate all performance metrics.
        
        Args:
            equity_curve: Time series of portfolio equity
            trades: List of Trade objects (optional)
            periods_per_year: Trading periods per year (252 for daily)
            
        Returns:
            PerformanceMetrics object with all metrics
        """
        metrics = PerformanceMetrics()
        
        # Calculate returns
        returns = equity_curve.pct_change().dropna()
        
        # Returns metrics
        metrics.total_return = (equity_curve.iloc[-1] / equity_curve.iloc[0]) - 1
        metrics.annualized_return = self._annualized_return(
            equity_curve, periods_per_year
        )
        metrics.cagr = self._cagr(equity_curve, periods_per_year)
        
        # Risk metrics
        metrics.volatility = self._volatility(returns, periods_per_year)
        metrics.sharpe_ratio = self._sharpe_ratio(
            returns, periods_per_year, self.risk_free_rate
        )
        metrics.sortino_ratio = self._sortino_ratio(
            returns, periods_per_year, self.risk_free_rate
        )
        
        # Drawdown metrics
        drawdown_series = self._drawdown_series(equity_curve)
        metrics.max_drawdown = abs(drawdown_series.min())
        metrics.max_drawdown_duration = self._max_drawdown_duration(drawdown_series)
        metrics.avg_drawdown = abs(drawdown_series.mean())
        
        # Calmar ratio
        metrics.calmar_ratio = (
            metrics.cagr / metrics.max_drawdown 
            if metrics.max_drawdown != 0 else 0
        )
        
        # Trade metrics (if trades provided)
        if trades:
            metrics = self._calculate_trade_metrics(metrics, trades)
        
        return metrics
    
    def _annualized_return(
        self,
        equity_curve: pd.Series,
        periods_per_year: int
    ) -> float:
        """Calculate annualized return."""
        total_return = (equity_curve.iloc[-1] / equity_curve.iloc[0]) - 1
        n_periods = len(equity_curve)
        n_years = n_periods / periods_per_year
        
        if n_years <= 0:
            return 0.0
        
        annualized = (1 + total_return) ** (1 / n_years) - 1
        return annualized
    
    def _cagr(self, equity_curve: pd.Series, periods_per_year: int) -> float:
        """Calculate Compound Annual Growth Rate."""
        return self._annualized_return(equity_curve, periods_per_year)
    
    def _volatility(self, returns: pd.Series, periods_per_year: int) -> float:
        """Calculate annualized volatility."""
        return returns.std() * np.sqrt(periods_per_year)
    
    def _sharpe_ratio(
        self,
        returns: pd.Series,
        periods_per_year: int,
        risk_free_rate: float
    ) -> float:
        """
        Calculate Sharpe Ratio.
        
        Sharpe = (Return - RiskFreeRate) / Volatility
        """
        excess_returns = returns - (risk_free_rate / periods_per_year)
        
        if excess_returns.std() == 0:
            return 0.0
        
        sharpe = excess_returns.mean() / excess_returns.std()
        sharpe_annualized = sharpe * np.sqrt(periods_per_year)
        
        return sharpe_annualized
    
    def _sortino_ratio(
        self,
        returns: pd.Series,
        periods_per_year: int,
        risk_free_rate: float
    ) -> float:
        """
        Calculate Sortino Ratio.
        
        Like Sharpe but only penalizes downside volatility.
        """
        excess_returns = returns - (risk_free_rate / periods_per_year)
        
        # Downside deviation (only negative returns)
        downside_returns = returns[returns < 0]
        
        if len(downside_returns) == 0 or downside_returns.std() == 0:
            return 0.0
        
        downside_std = downside_returns.std()
        sortino = excess_returns.mean() / downside_std
        sortino_annualized = sortino * np.sqrt(periods_per_year)
        
        return sortino_annualized
    
    def _drawdown_series(self, equity_curve: pd.Series) -> pd.Series:
        """
        Calculate drawdown series.
        
        Drawdown = (Current - Peak) / Peak
        """
        running_max = equity_curve.expanding().max()
        drawdown = (equity_curve - running_max) / running_max
        return drawdown
    
    def _max_drawdown_duration(self, drawdown_series: pd.Series) -> int:
        """Calculate maximum drawdown duration in periods."""
        # Find periods when not at new highs
        is_drawdown = drawdown_series < 0
        
        # Find consecutive drawdown periods
        drawdown_periods = []
        current_period = 0
        
        for in_dd in is_drawdown:
            if in_dd:
                current_period += 1
            else:
                if current_period > 0:
                    drawdown_periods.append(current_period)
                current_period = 0
        
        # Add final period if still in drawdown
        if current_period > 0:
            drawdown_periods.append(current_period)
        
        return max(drawdown_periods) if drawdown_periods else 0
    
    def _calculate_trade_metrics(
        self,
        metrics: PerformanceMetrics,
        trades: List
    ) -> PerformanceMetrics:
        """Calculate metrics based on individual trades."""
        if not trades:
            return metrics
        
        # Extract trade P&Ls
        trade_pnls = []
        for trade in trades:
            if hasattr(trade, 'pnl'):
                trade_pnls.append(trade.pnl)
        
        if not trade_pnls:
            return metrics
        
        # Basic trade counts
        metrics.total_trades = len(trade_pnls)
        wins = [pnl for pnl in trade_pnls if pnl > 0]
        losses = [pnl for pnl in trade_pnls if pnl < 0]
        
        metrics.winning_trades = len(wins)
        metrics.losing_trades = len(losses)
        metrics.win_rate = (
            metrics.winning_trades / metrics.total_trades 
            if metrics.total_trades > 0 else 0
        )
        
        # Win/Loss metrics
        metrics.avg_win = np.mean(wins) if wins else 0
        metrics.avg_loss = np.mean(losses) if losses else 0
        metrics.best_trade = max(trade_pnls) if trade_pnls else 0
        metrics.worst_trade = min(trade_pnls) if trade_pnls else 0
        
        # Profit factor
        total_wins = sum(wins) if wins else 0
        total_losses = abs(sum(losses)) if losses else 0
        metrics.profit_factor = (
            total_wins / total_losses 
            if total_losses > 0 else 0
        )
        
        # Expectancy (average P&L per trade)
        metrics.expectancy = np.mean(trade_pnls) if trade_pnls else 0
        
        # Win/Loss streaks
        streaks = self._calculate_streaks(trade_pnls)
        metrics.longest_win_streak = streaks['max_win_streak']
        metrics.longest_loss_streak = streaks['max_loss_streak']
        
        return metrics
    
    def _calculate_streaks(self, trade_pnls: List[float]) -> Dict:
        """Calculate win/loss streaks."""
        max_win_streak = 0
        max_loss_streak = 0
        current_win_streak = 0
        current_loss_streak = 0
        
        for pnl in trade_pnls:
            if pnl > 0:
                current_win_streak += 1
                current_loss_streak = 0
                max_win_streak = max(max_win_streak, current_win_streak)
            elif pnl < 0:
                current_loss_streak += 1
                current_win_streak = 0
                max_loss_streak = max(max_loss_streak, current_loss_streak)
        
        return {
            'max_win_streak': max_win_streak,
            'max_loss_streak': max_loss_streak
        }


class RiskMetrics:
    """Additional risk metrics calculations."""
    
    @staticmethod
    def value_at_risk(returns: pd.Series, confidence: float = 0.95) -> float:
        """
        Calculate Value at Risk (VaR).
        
        VaR is the maximum expected loss at a given confidence level.
        
        Args:
            returns: Return series
            confidence: Confidence level (0.95 = 95%)
            
        Returns:
            VaR value (positive number representing potential loss)
        """
        return abs(returns.quantile(1 - confidence))
    
    @staticmethod
    def conditional_var(returns: pd.Series, confidence: float = 0.95) -> float:
        """
        Calculate Conditional Value at Risk (CVaR) / Expected Shortfall.
        
        CVaR is the average loss beyond the VaR threshold.
        
        Args:
            returns: Return series
            confidence: Confidence level
            
        Returns:
            CVaR value
        """
        var = RiskMetrics.value_at_risk(returns, confidence)
        # Average of returns worse than VaR
        return abs(returns[returns <= -var].mean())
    
    @staticmethod
    def maximum_adverse_excursion(trades: List) -> float:
        """
        Calculate Maximum Adverse Excursion (MAE).
        
        MAE is the largest peak-to-trough decline during a trade.
        """
        maes = []
        for trade in trades:
            if hasattr(trade, 'mae'):
                maes.append(trade.mae)
        
        return max(maes) if maes else 0.0
    
    @staticmethod
    def maximum_favorable_excursion(trades: List) -> float:
        """
        Calculate Maximum Favorable Excursion (MFE).
        
        MFE is the largest trough-to-peak gain during a trade.
        """
        mfes = []
        for trade in trades:
            if hasattr(trade, 'mfe'):
                mfes.append(trade.mfe)
        
        return max(mfes) if mfes else 0.0
