"""
Position Management Module

Handles position tracking, sizing, and trade execution.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Literal
import pandas as pd


@dataclass
class Trade:
    """
    Represents a single trade execution.
    
    Attributes:
        date: Trade execution date
        ticker: Stock ticker symbol
        side: 'BUY' or 'SELL'
        quantity: Number of shares
        price: Execution price per share
        commission: Transaction commission
        slippage: Price slippage cost
        total_cost: Total cost including fees
    """
    date: datetime
    ticker: str
    side: Literal['BUY', 'SELL']
    quantity: float
    price: float
    commission: float
    slippage: float
    
    @property
    def total_cost(self) -> float:
        """Calculate total cost including fees."""
        base_cost = self.quantity * self.price
        if self.side == 'BUY':
            return base_cost + self.commission + self.slippage
        else:  # SELL
            return base_cost - self.commission - self.slippage
    
    @property
    def notional_value(self) -> float:
        """Calculate notional value (without fees)."""
        return self.quantity * self.price
    
    def __repr__(self) -> str:
        return (f"Trade({self.date.date()}, {self.side} {self.quantity:.2f} "
                f"{self.ticker} @ ${self.price:.2f})")


@dataclass
class Position:
    """
    Represents a position in a single security.
    
    Attributes:
        ticker: Stock ticker symbol
        quantity: Number of shares held (positive=long, negative=short)
        avg_price: Average entry price
        market_value: Current market value
        unrealized_pnl: Unrealized profit/loss
        realized_pnl: Realized profit/loss from closed trades
    """
    ticker: str
    quantity: float = 0.0
    avg_price: float = 0.0
    market_value: float = 0.0
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    
    @property
    def is_long(self) -> bool:
        """Check if position is long."""
        return self.quantity > 0
    
    @property
    def is_short(self) -> bool:
        """Check if position is short."""
        return self.quantity < 0
    
    @property
    def is_flat(self) -> bool:
        """Check if position is closed."""
        return abs(self.quantity) < 1e-6
    
    def update_market_value(self, current_price: float) -> None:
        """
        Update position's market value and unrealized P&L.
        
        Args:
            current_price: Current market price
        """
        if not self.is_flat:
            self.market_value = self.quantity * current_price
            self.unrealized_pnl = (current_price - self.avg_price) * self.quantity
        else:
            self.market_value = 0.0
            self.unrealized_pnl = 0.0
    
    def add_trade(self, trade: Trade) -> None:
        """
        Add a trade to the position and update average price.
        
        Args:
            trade: Trade to add
        """
        if trade.side == 'BUY':
            new_quantity = self.quantity + trade.quantity
            
            if self.quantity >= 0:
                # Adding to long or opening long
                total_cost = (self.quantity * self.avg_price + 
                             trade.quantity * trade.price)
                self.avg_price = total_cost / new_quantity if new_quantity != 0 else 0
            else:
                # Covering short
                if new_quantity >= 0:
                    # Closing short, opening long
                    pnl = (self.avg_price - trade.price) * abs(self.quantity)
                    self.realized_pnl += pnl
                    self.avg_price = trade.price if new_quantity > 0 else 0
                else:
                    # Partial cover
                    pnl = (self.avg_price - trade.price) * trade.quantity
                    self.realized_pnl += pnl
            
            self.quantity = new_quantity
            
        else:  # SELL
            new_quantity = self.quantity - trade.quantity
            
            if self.quantity > 0:
                # Closing long or partial close
                if new_quantity >= 0:
                    pnl = (trade.price - self.avg_price) * trade.quantity
                    self.realized_pnl += pnl
                else:
                    # Closed long, opened short
                    pnl = (trade.price - self.avg_price) * self.quantity
                    self.realized_pnl += pnl
                    self.avg_price = trade.price
            else:
                # Adding to short or opening short
                total_cost = (abs(self.quantity) * self.avg_price + 
                             trade.quantity * trade.price)
                self.avg_price = total_cost / abs(new_quantity) if new_quantity != 0 else 0
            
            self.quantity = new_quantity
    
    def __repr__(self) -> str:
        pos_type = "LONG" if self.is_long else "SHORT" if self.is_short else "FLAT"
        return (f"Position({self.ticker}, {pos_type}, "
                f"qty={abs(self.quantity):.2f}, "
                f"P&L=${self.unrealized_pnl + self.realized_pnl:.2f})")


class PositionSizer:
    """
    Handles position sizing calculations.
    
    Supports multiple sizing methods:
    - Fixed: Fixed dollar amount per trade
    - Percent: Percentage of portfolio equity
    - Risk-based: Size based on risk per trade
    - Volatility-based: Size based on volatility
    """
    
    def __init__(
        self,
        method: Literal['fixed', 'percent', 'risk', 'volatility'] = 'percent',
        size_value: float = 0.1
    ):
        """
        Initialize position sizer.
        
        Args:
            method: Sizing method
            size_value: Value for sizing (interpretation depends on method)
                - fixed: Dollar amount per trade
                - percent: Percentage of equity (0.1 = 10%)
                - risk: Risk percentage per trade
                - volatility: Target volatility level
        """
        self.method = method
        self.size_value = size_value
    
    def calculate_quantity(
        self,
        signal: int,
        current_price: float,
        portfolio_equity: float,
        volatility: Optional[float] = None,
        stop_loss_pct: Optional[float] = None
    ) -> float:
        """
        Calculate position quantity based on sizing method.
        
        Args:
            signal: Trading signal (1=long, -1=short, 0=neutral)
            current_price: Current price
            portfolio_equity: Current portfolio equity
            volatility: Asset volatility (for volatility-based sizing)
            stop_loss_pct: Stop loss percentage (for risk-based sizing)
            
        Returns:
            Number of shares to trade
        """
        if signal == 0 or current_price <= 0:
            return 0.0
        
        if self.method == 'fixed':
            # Fixed dollar amount per trade
            target_value = self.size_value
            
        elif self.method == 'percent':
            # Percentage of portfolio equity
            target_value = portfolio_equity * self.size_value
            
        elif self.method == 'risk':
            # Risk-based sizing
            if stop_loss_pct is None or stop_loss_pct <= 0:
                # Default to percent method if no stop loss provided
                target_value = portfolio_equity * self.size_value
            else:
                # Size based on risk per trade
                risk_amount = portfolio_equity * self.size_value
                position_size = risk_amount / stop_loss_pct
                target_value = position_size
                
        elif self.method == 'volatility':
            # Volatility-based sizing
            if volatility is None or volatility <= 0:
                target_value = portfolio_equity * self.size_value
            else:
                # Inverse volatility sizing
                target_volatility = self.size_value
                target_value = (portfolio_equity * target_volatility) / volatility
                
        else:
            raise ValueError(f"Unknown sizing method: {self.method}")
        
        # Calculate quantity
        quantity = target_value / current_price
        
        # Round to whole shares (or allow fractional if needed)
        quantity = round(quantity, 2)
        
        return abs(quantity)  # Return absolute value
    
    def __repr__(self) -> str:
        return f"PositionSizer(method={self.method}, size_value={self.size_value})"
