"""
Portfolio Management Module

Tracks portfolio equity, positions, and cash throughout backtesting.
"""

from typing import Dict, List, Optional
from datetime import datetime
import pandas as pd
from .position import Position, Trade


class Portfolio:
    """
    Tracks portfolio state including cash, positions, and equity.
    
    Manages all position updates, cash flows, and equity calculations.
    """
    
    def __init__(self, initial_capital: float = 100000.0):
        """
        Initialize portfolio.
        
        Args:
            initial_capital: Starting cash amount
        """
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions: Dict[str, Position] = {}
        self.trades: List[Trade] = []
        
        # Historical tracking
        self.equity_curve: List[tuple] = []  # (date, equity)
        self.cash_curve: List[tuple] = []  # (date, cash)
        
    @property
    def equity(self) -> float:
        """Calculate current total equity (cash + positions)."""
        positions_value = sum(pos.market_value for pos in self.positions.values())
        return self.cash + positions_value
    
    @property
    def positions_value(self) -> float:
        """Calculate total value of all positions."""
        return sum(pos.market_value for pos in self.positions.values())
    
    @property
    def total_pnl(self) -> float:
        """Calculate total profit/loss."""
        return self.equity - self.initial_capital
    
    @property
    def return_pct(self) -> float:
        """Calculate total return percentage."""
        return (self.equity / self.initial_capital) - 1
    
    def get_position(self, ticker: str) -> Position:
        """
        Get position for ticker (creates if doesn't exist).
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Position object
        """
        if ticker not in self.positions:
            self.positions[ticker] = Position(ticker=ticker)
        return self.positions[ticker]
    
    def update_position_prices(self, prices: Dict[str, float]) -> None:
        """
        Update market values for all positions.
        
        Args:
            prices: Dictionary of {ticker: current_price}
        """
        for ticker, price in prices.items():
            if ticker in self.positions:
                self.positions[ticker].update_market_value(price)
    
    def execute_trade(self, trade: Trade) -> bool:
        """
        Execute a trade and update portfolio state.
        
        Args:
            trade: Trade to execute
            
        Returns:
            True if trade executed successfully, False otherwise
        """
        # Check if we have enough cash
        if trade.side == 'BUY':
            if self.cash < trade.total_cost:
                return False  # Insufficient cash
            
            # Deduct cash
            self.cash -= trade.total_cost
            
        else:  # SELL
            # Add cash (revenue minus costs)
            self.cash += trade.total_cost
        
        # Update position
        position = self.get_position(trade.ticker)
        position.add_trade(trade)
        
        # Record trade
        self.trades.append(trade)
        
        return True
    
    def record_snapshot(self, date: datetime) -> None:
        """
        Record equity and cash snapshot for this period.
        
        Args:
            date: Current date
        """
        self.equity_curve.append((date, self.equity))
        self.cash_curve.append((date, self.cash))
    
    def get_equity_series(self) -> pd.Series:
        """
        Get equity curve as pandas Series.
        
        Returns:
            Series with date index and equity values
        """
        if not self.equity_curve:
            return pd.Series(dtype=float)
        
        dates, values = zip(*self.equity_curve)
        return pd.Series(values, index=dates, name='equity')
    
    def get_cash_series(self) -> pd.Series:
        """
        Get cash curve as pandas Series.
        
        Returns:
            Series with date index and cash values
        """
        if not self.cash_curve:
            return pd.Series(dtype=float)
        
        dates, values = zip(*self.cash_curve)
        return pd.Series(values, index=dates, name='cash')
    
    def get_positions_summary(self) -> pd.DataFrame:
        """
        Get summary of all positions.
        
        Returns:
            DataFrame with position details
        """
        if not self.positions:
            return pd.DataFrame()
        
        data = []
        for ticker, pos in self.positions.items():
            if not pos.is_flat:
                data.append({
                    'ticker': ticker,
                    'quantity': pos.quantity,
                    'avg_price': pos.avg_price,
                    'market_value': pos.market_value,
                    'unrealized_pnl': pos.unrealized_pnl,
                    'realized_pnl': pos.realized_pnl,
                    'total_pnl': pos.unrealized_pnl + pos.realized_pnl
                })
        
        return pd.DataFrame(data)
    
    def get_trades_dataframe(self) -> pd.DataFrame:
        """
        Get all trades as DataFrame.
        
        Returns:
            DataFrame with trade details
        """
        if not self.trades:
            return pd.DataFrame()
        
        data = []
        for trade in self.trades:
            data.append({
                'date': trade.date,
                'ticker': trade.ticker,
                'side': trade.side,
                'quantity': trade.quantity,
                'price': trade.price,
                'commission': trade.commission,
                'slippage': trade.slippage,
                'total_cost': trade.total_cost
            })
        
        return pd.DataFrame(data)
    
    def summary(self) -> str:
        """Generate formatted portfolio summary."""
        lines = [
            "="*60,
            "PORTFOLIO SUMMARY",
            "="*60,
            "",
            f"Initial Capital:    ${self.initial_capital:>15,.2f}",
            f"Current Cash:       ${self.cash:>15,.2f}",
            f"Positions Value:    ${self.positions_value:>15,.2f}",
            f"Total Equity:       ${self.equity:>15,.2f}",
            "",
            f"Total P&L:          ${self.total_pnl:>15,.2f}",
            f"Total Return:       {self.return_pct:>15.2%}",
            "",
            f"Total Trades:       {len(self.trades):>15}",
            f"Open Positions:     {sum(1 for p in self.positions.values() if not p.is_flat):>15}",
            "",
            "="*60
        ]
        return "\n".join(lines)
    
    def __repr__(self) -> str:
        return (f"Portfolio(equity=${self.equity:,.2f}, "
                f"cash=${self.cash:,.2f}, "
                f"positions={len(self.positions)})")


class PortfolioState:
    """
    Snapshot of portfolio state at a point in time.
    
    Used for analysis and debugging.
    """
    
    def __init__(
        self,
        date: datetime,
        cash: float,
        equity: float,
        positions: Dict[str, Position]
    ):
        """
        Initialize portfolio state snapshot.
        
        Args:
            date: Snapshot date
            cash: Cash amount
            equity: Total equity
            positions: Dictionary of positions
        """
        self.date = date
        self.cash = cash
        self.equity = equity
        self.positions = positions.copy()
    
    def to_dict(self) -> Dict:
        """Convert state to dictionary."""
        return {
            'date': self.date,
            'cash': self.cash,
            'equity': self.equity,
            'num_positions': len([p for p in self.positions.values() if not p.is_flat]),
            'positions_value': sum(p.market_value for p in self.positions.values())
        }
