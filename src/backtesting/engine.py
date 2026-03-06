"""
Backtesting Engine

Main backtesting engine that orchestrates strategy execution, portfolio management,
transaction costs, and performance calculation.

Architecture:
1. Engine coordinates all components
2. Portfolio tracks positions and equity
3. Cost calculator applies realistic fees
4. Position sizer determines trade sizes
5. Metrics calculator evaluates performance
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, List
from datetime import datetime
import warnings

from .portfolio import Portfolio
from .position import Trade, PositionSizer
from .costs import TransactionCostCalculator, CostModel, StandardCostModels
from .metrics import PerformanceCalculator, PerformanceMetrics
from src.strategies.base import BaseStrategy


class BacktestEngine:
    """
    Professional backtesting engine for trading strategies.
    
    Features:
    - Position sizing (fixed, percent, risk-based, volatility-based)
    - Transaction costs (commission + slippage)
    - Portfolio tracking (equity, positions, cash)
    - Performance metrics (Sharpe, drawdown, CAGR, win rate, etc.)
    - Clean, modular architecture
    """
    
    def __init__(
        self,
        initial_capital: float = 100000.0,
        position_sizer: Optional[PositionSizer] = None,
        cost_model: Optional[CostModel] = None,
        risk_free_rate: float = 0.02
    ):
        """
        Initialize backtesting engine.
        
        Args:
            initial_capital: Starting portfolio capital
            position_sizer: Position sizing strategy (default: 10% of equity)
            cost_model: Transaction cost model (default: RETAIL)
            risk_free_rate: Risk-free rate for Sharpe/Sortino (default: 2%)
        """
        # Initialize components
        self.portfolio = Portfolio(initial_capital=initial_capital)
        self.position_sizer = position_sizer or PositionSizer(method='percent', size_value=0.1)
        self.cost_calculator = TransactionCostCalculator(
            cost_model=cost_model or StandardCostModels.RETAIL
        )
        self.metrics_calculator = PerformanceCalculator(risk_free_rate=risk_free_rate)
        
        # Results storage
        self.results: Optional[BacktestResults] = None
        
    def run(
        self,
        strategy: BaseStrategy,
        data: pd.DataFrame,
        ticker: str = 'STOCK'
    ) -> 'BacktestResults':
        """
        Run backtest on a strategy with historical data.
        
        Args:
            strategy: Trading strategy instance
            data: Historical OHLCV data with date index
            ticker: Stock ticker symbol
            
        Returns:
            BacktestResults object with complete results
        """
        print(f"\nStarting backtest...")
        print(f"Strategy: {strategy}")
        print(f"Initial Capital: ${self.portfolio.initial_capital:,.2f}")
        print(f"Data: {len(data)} periods from {data.index[0]} to {data.index[-1]}")
        
        # Generate signals from strategy
        signals_data = strategy.generate_signals(data.copy())
        
        # Validate data
        required_cols = ['close', 'signal', 'position']
        if not all(col in signals_data.columns for col in required_cols):
            missing = [col for col in required_cols if col not in signals_data.columns]
            raise ValueError(f"Strategy output missing required columns: {missing}")
        
        # Run simulation
        self._simulate(signals_data, ticker)
        
        # Calculate performance metrics
        equity_series = self.portfolio.get_equity_series()
        metrics = self.metrics_calculator.calculate_metrics(equity_series)
        
        # Create results object
        self.results = BacktestResults(
            portfolio=self.portfolio,
            metrics=metrics,
            signals_data=signals_data,
            strategy=strategy
        )
        
        print(f"\nBacktest completed!")
        print(f"Final Equity: ${self.portfolio.equity:,.2f}")
        print(f"Total Return: {self.portfolio.return_pct:.2%}")
        print(f"Total Trades: {len(self.portfolio.trades)}")
        
        return self.results
    
    def _simulate(self, data: pd.DataFrame, ticker: str) -> None:
        """
        Simulate trading based on signals.
        
        Args:
            data: DataFrame with signals and price data
            ticker: Stock ticker symbol
        """
        # Track current position
        current_position = 0  # 0 = flat, 1 = long, -1 = short
        
        # Iterate through each time period
        for idx, row in data.iterrows():
            date = pd.to_datetime(idx)
            price = row['close']
            signal = row['signal']
            target_position = row['position']
            
            # Update position market values
            self.portfolio.update_position_prices({ticker: price})
            
            # Check if we need to trade
            if target_position != current_position:
                # Calculate trade quantity
                trade_signal = np.sign(target_position - current_position)
                
                quantity = self.position_sizer.calculate_quantity(
                    signal=trade_signal,
                    current_price=price,
                    portfolio_equity=self.portfolio.equity,
                    volatility=row.get('volatility', 0.02),
                    stop_loss_pct=0.02  # Default 2% stop
                )
                
                if quantity > 0:
                    # Determine trade side
                    if target_position > current_position:
                        # Going long or covering short
                        trade_side = 'BUY'
                    else:
                        # Going short or closing long
                        trade_side = 'SELL'
                    
                    # Calculate costs
                    commission, slippage, _ = self.cost_calculator.calculate_total_costs(
                        quantity=quantity,
                        price=price,
                        side=trade_side,
                        volatility=row.get('volatility', 0.02),
                        volume=row.get('volume', 1000000)
                    )
                    
                    # Create trade
                    trade = Trade(
                        date=date,
                        ticker=ticker,
                        side=trade_side,
                        quantity=quantity,
                        price=price,
                        commission=commission,
                        slippage=slippage
                    )
                    
                    # Execute trade
                    success = self.portfolio.execute_trade(trade)
                    
                    if success:
                        current_position = target_position
            
            # Record portfolio snapshot
            self.portfolio.record_snapshot(date)
    
    def run_multiple(
        self,
        strategy: BaseStrategy,
        data_dict: Dict[str, pd.DataFrame]
    ) -> 'BacktestResults':
        """
        Run backtest on multiple tickers.
        
        Args:
            strategy: Trading strategy instance
            data_dict: Dictionary of {ticker: data}
            
        Returns:
            BacktestResults with combined performance
        """
        print(f"\nStarting multi-ticker backtest...")
        print(f"Tickers: {list(data_dict.keys())}")
        
        # Generate signals for each ticker
        all_signals = {}
        for ticker, data in data_dict.items():
            signals = strategy.generate_signals(data.copy())
            all_signals[ticker] = signals
        
        # Combine all dates
        all_dates = sorted(set(
            date for signals in all_signals.values()
            for date in signals.index
        ))
        
        # Track positions for each ticker
        positions = {ticker: 0 for ticker in data_dict.keys()}
        
        # Simulate trading
        for date in all_dates:
            # Get current prices
            current_prices = {}
            for ticker, signals in all_signals.items():
                if date in signals.index:
                    current_prices[ticker] = signals.loc[date, 'close']
            
            # Update all position prices
            self.portfolio.update_position_prices(current_prices)
            
            # Process signals for each ticker
            for ticker, signals in all_signals.items():
                if date not in signals.index:
                    continue
                
                row = signals.loc[date]
                price = row['close']
                target_position = row['position']
                current_position = positions[ticker]
                
                # Execute trade if position changed
                if target_position != current_position:
                    trade_signal = np.sign(target_position - current_position)
                    
                    # Calculate position size (divide equity among tickers)
                    quantity = self.position_sizer.calculate_quantity(
                        signal=trade_signal,
                        current_price=price,
                        portfolio_equity=self.portfolio.equity / len(data_dict),
                        volatility=row.get('volatility', 0.02)
                    )
                    
                    if quantity > 0:
                        trade_side = 'BUY' if target_position > current_position else 'SELL'
                        
                        commission, slippage, _ = self.cost_calculator.calculate_total_costs(
                            quantity=quantity,
                            price=price,
                            side=trade_side,
                            volatility=row.get('volatility', 0.02),
                            volume=row.get('volume', 1000000)
                        )
                        
                        trade = Trade(
                            date=date,
                            ticker=ticker,
                            side=trade_side,
                            quantity=quantity,
                            price=price,
                            commission=commission,
                            slippage=slippage
                        )
                        
                        if self.portfolio.execute_trade(trade):
                            positions[ticker] = target_position
            
            # Record snapshot
            self.portfolio.record_snapshot(date)
        
        # Calculate metrics
        equity_series = self.portfolio.get_equity_series()
        metrics = self.metrics_calculator.calculate_metrics(equity_series)
        
        self.results = BacktestResults(
            portfolio=self.portfolio,
            metrics=metrics,
            signals_data=pd.concat(all_signals),
            strategy=strategy
        )
        
        print(f"\nBacktest completed!")
        print(f"Final Equity: ${self.portfolio.equity:,.2f}")
        
        return self.results


class BacktestResults:
    """
    Container for backtest results and analysis.
    
    Provides methods for accessing and analyzing backtest outcomes.
    """
    
    def __init__(
        self,
        portfolio: Portfolio,
        metrics: PerformanceMetrics,
        signals_data: pd.DataFrame,
        strategy: BaseStrategy
    ):
        """
        Initialize results container.
        
        Args:
            portfolio: Final portfolio state
            metrics: Performance metrics
            signals_data: DataFrame with signals and indicators
            strategy: Strategy that was tested
        """
        self.portfolio = portfolio
        self.metrics = metrics
        self.signals_data = signals_data
        self.strategy = strategy
    
    def summary(self) -> str:
        """Generate comprehensive summary report."""
        lines = [
            "\n" + "="*70,
            "BACKTEST RESULTS SUMMARY",
            "="*70,
            "",
            f"Strategy: {self.strategy}",
            "",
            self.portfolio.summary(),
            "",
            self.metrics.summary()
        ]
        return "\n".join(lines)
    
    def get_equity_curve(self) -> pd.Series:
        """Get equity curve."""
        return self.portfolio.get_equity_series()
    
    def get_trades(self) -> pd.DataFrame:
        """Get all trades."""
        return self.portfolio.get_trades_dataframe()
    
    def get_positions(self) -> pd.DataFrame:
        """Get position summary."""
        return self.portfolio.get_positions_summary()
    
    def get_metrics_dict(self) -> Dict:
        """Get metrics as dictionary."""
        return self.metrics.to_dict()
    
    def plot_results(self) -> None:
        """
        Plot backtest results (requires matplotlib).
        
        Shows: equity curve, drawdown, returns distribution
        """
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            print("Matplotlib not installed. Install with: pip install matplotlib")
            return
        
        equity_curve = self.get_equity_curve()
        returns = equity_curve.pct_change().dropna()
        
        # Calculate drawdown
        running_max = equity_curve.expanding().max()
        drawdown = (equity_curve - running_max) / running_max
        
        fig, axes = plt.subplots(3, 1, figsize=(12, 10))
        
        # Equity curve
        axes[0].plot(equity_curve.index, equity_curve.values)
        axes[0].set_title('Equity Curve')
        axes[0].set_ylabel('Equity ($)')
        axes[0].grid(True, alpha=0.3)
        
        # Drawdown
        axes[1].fill_between(drawdown.index, 0, drawdown.values, color='red', alpha=0.3)
        axes[1].set_title('Drawdown')
        axes[1].set_ylabel('Drawdown (%)')
        axes[1].grid(True, alpha=0.3)
        
        # Returns distribution
        axes[2].hist(returns.values, bins=50, edgecolor='black', alpha=0.7)
        axes[2].set_title('Returns Distribution')
        axes[2].set_xlabel('Return')
        axes[2].set_ylabel('Frequency')
        axes[2].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.show()
    
    def __repr__(self) -> str:
        return (f"BacktestResults("
                f"equity=${self.portfolio.equity:,.2f}, "
                f"return={self.portfolio.return_pct:.2%}, "
                f"sharpe={self.metrics.sharpe_ratio:.2f})")
