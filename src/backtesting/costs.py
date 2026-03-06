"""
Transaction Costs and Slippage Module

Models realistic trading costs including commissions and slippage.
"""

from typing import Literal
from dataclasses import dataclass


@dataclass
class CostModel:
    """
    Configuration for transaction cost modeling.
    
    Attributes:
        commission_type: 'fixed' or 'percent'
        commission_value: Commission amount or percentage
        slippage_type: 'fixed', 'percent', or 'volume_based'
        slippage_value: Slippage amount or percentage
        min_commission: Minimum commission per trade
    """
    commission_type: Literal['fixed', 'percent'] = 'percent'
    commission_value: float = 0.001  # 0.1% or $0.001 per share
    slippage_type: Literal['fixed', 'percent', 'volume_based'] = 'percent'
    slippage_value: float = 0.0005  # 0.05% slippage
    min_commission: float = 0.0


class TransactionCostCalculator:
    """
    Calculates realistic transaction costs for trades.
    
    Supports multiple cost models:
    - Fixed commission per trade
    - Percentage-based commission
    - Fixed slippage
    - Percentage-based slippage
    - Volume-based slippage
    """
    
    def __init__(self, cost_model: CostModel = None):
        """
        Initialize cost calculator.
        
        Args:
            cost_model: Cost model configuration. If None, uses default.
        """
        self.cost_model = cost_model or CostModel()
    
    def calculate_commission(
        self,
        quantity: float,
        price: float,
        side: Literal['BUY', 'SELL']
    ) -> float:
        """
        Calculate commission for a trade.
        
        Args:
            quantity: Number of shares
            price: Price per share
            side: Trade side ('BUY' or 'SELL')
            
        Returns:
            Commission amount
        """
        notional_value = quantity * price
        
        if self.cost_model.commission_type == 'fixed':
            # Fixed commission per share
            commission = quantity * self.cost_model.commission_value
        else:
            # Percentage-based commission
            commission = notional_value * self.cost_model.commission_value
        
        # Apply minimum commission
        commission = max(commission, self.cost_model.min_commission)
        
        return commission
    
    def calculate_slippage(
        self,
        quantity: float,
        price: float,
        side: Literal['BUY', 'SELL'],
        volatility: float = 0.02,
        volume: float = 1000000
    ) -> float:
        """
        Calculate slippage cost for a trade.
        
        Slippage models market impact and execution uncertainty.
        
        Args:
            quantity: Number of shares
            price: Price per share
            side: Trade side ('BUY' or 'SELL')
            volatility: Asset volatility (for volume-based slippage)
            volume: Average trading volume (for volume-based slippage)
            
        Returns:
            Slippage cost
        """
        notional_value = quantity * price
        
        if self.cost_model.slippage_type == 'fixed':
            # Fixed slippage per share
            slippage = quantity * self.cost_model.slippage_value
            
        elif self.cost_model.slippage_type == 'percent':
            # Percentage-based slippage
            slippage = notional_value * self.cost_model.slippage_value
            
        else:  # volume_based
            # Volume-based slippage (market impact model)
            # Slippage increases with trade size relative to volume
            trade_volume_ratio = quantity / max(volume, 1)
            
            # Market impact: slippage = base_slippage * (1 + trade_ratio) * volatility
            base_slippage = self.cost_model.slippage_value
            market_impact = base_slippage * (1 + trade_volume_ratio) * (1 + volatility)
            
            slippage = notional_value * market_impact
        
        return slippage
    
    def calculate_total_costs(
        self,
        quantity: float,
        price: float,
        side: Literal['BUY', 'SELL'],
        volatility: float = 0.02,
        volume: float = 1000000
    ) -> tuple[float, float, float]:
        """
        Calculate total transaction costs.
        
        Args:
            quantity: Number of shares
            price: Price per share
            side: Trade side
            volatility: Asset volatility
            volume: Average trading volume
            
        Returns:
            Tuple of (commission, slippage, total_cost)
        """
        commission = self.calculate_commission(quantity, price, side)
        slippage = self.calculate_slippage(quantity, price, side, volatility, volume)
        total_cost = commission + slippage
        
        return commission, slippage, total_cost
    
    def __repr__(self) -> str:
        return (f"TransactionCostCalculator("
                f"commission={self.cost_model.commission_type}:"
                f"{self.cost_model.commission_value}, "
                f"slippage={self.cost_model.slippage_type}:"
                f"{self.cost_model.slippage_value})")


class SlippageModel:
    """
    Advanced slippage modeling.
    
    Provides different slippage estimation methods based on
    market conditions and trade characteristics.
    """
    
    @staticmethod
    def fixed_slippage(price: float, slippage_bps: float = 5.0) -> float:
        """
        Fixed slippage in basis points.
        
        Args:
            price: Trade price
            slippage_bps: Slippage in basis points (1 bp = 0.01%)
            
        Returns:
            Slippage amount
        """
        return price * (slippage_bps / 10000)
    
    @staticmethod
    def percentage_slippage(
        price: float,
        quantity: float,
        slippage_pct: float = 0.0005
    ) -> float:
        """
        Percentage-based slippage.
        
        Args:
            price: Trade price
            quantity: Trade quantity
            slippage_pct: Slippage percentage (0.0005 = 0.05%)
            
        Returns:
            Total slippage cost
        """
        return price * quantity * slippage_pct
    
    @staticmethod
    def market_impact(
        price: float,
        quantity: float,
        avg_volume: float,
        volatility: float,
        liquidity_factor: float = 0.1
    ) -> float:
        """
        Market impact-based slippage model.
        
        Based on Almgren-Chriss market impact model.
        Impact increases with: trade size, volatility, low liquidity
        
        Args:
            price: Trade price
            quantity: Trade quantity
            avg_volume: Average daily volume
            volatility: Asset volatility (annualized)
            liquidity_factor: Liquidity adjustment factor
            
        Returns:
            Estimated slippage cost
        """
        # Participation rate (percentage of daily volume)
        participation_rate = quantity / max(avg_volume, 1)
        
        # Temporary impact (dissipates after trade)
        temporary_impact = liquidity_factor * volatility * (participation_rate ** 0.5)
        
        # Permanent impact (market moves against us)
        permanent_impact = liquidity_factor * volatility * participation_rate
        
        # Total impact
        total_impact = temporary_impact + permanent_impact
        
        # Convert to dollar cost
        slippage = price * quantity * total_impact
        
        return slippage
    
    @staticmethod
    def bid_ask_spread(
        bid: float,
        ask: float,
        quantity: float,
        side: Literal['BUY', 'SELL']
    ) -> float:
        """
        Slippage based on bid-ask spread crossing.
        
        Args:
            bid: Bid price
            ask: Ask price
            quantity: Trade quantity
            side: Trade side
            
        Returns:
            Slippage from spread crossing
        """
        spread = ask - bid
        mid_price = (bid + ask) / 2
        
        if side == 'BUY':
            # Pay the ask, slippage is distance from mid
            execution_price = ask
        else:  # SELL
            # Receive the bid, slippage is distance from mid
            execution_price = bid
        
        slippage_per_share = abs(execution_price - mid_price)
        total_slippage = slippage_per_share * quantity
        
        return total_slippage


# Predefined cost models for different market types
class StandardCostModels:
    """Common cost model configurations."""
    
    # Zero cost (for testing)
    ZERO_COST = CostModel(
        commission_type='fixed',
        commission_value=0.0,
        slippage_type='fixed',
        slippage_value=0.0
    )
    
    # Retail broker (e.g., Interactive Brokers)
    RETAIL = CostModel(
        commission_type='fixed',
        commission_value=0.005,  # $0.005 per share
        slippage_type='percent',
        slippage_value=0.0005,  # 0.05% slippage
        min_commission=1.0  # $1 minimum
    )
    
    # Low-cost broker (e.g., Robinhood, zero commission)
    LOW_COST = CostModel(
        commission_type='fixed',
        commission_value=0.0,
        slippage_type='percent',
        slippage_value=0.001,  # 0.1% slippage (payment for order flow)
        min_commission=0.0
    )
    
    # Institutional (lower costs, volume-based slippage)
    INSTITUTIONAL = CostModel(
        commission_type='fixed',
        commission_value=0.002,  # $0.002 per share
        slippage_type='volume_based',
        slippage_value=0.0001,  # Base 0.01% + volume impact
        min_commission=0.0
    )
    
    # High-frequency trading (very low costs)
    HFT = CostModel(
        commission_type='fixed',
        commission_value=0.0001,  # $0.0001 per share
        slippage_type='percent',
        slippage_value=0.0001,  # 0.01% slippage
        min_commission=0.0
    )
    
    # Conservative (higher costs for realistic backtesting)
    CONSERVATIVE = CostModel(
        commission_type='percent',
        commission_value=0.001,  # 0.1% commission
        slippage_type='percent',
        slippage_value=0.002,  # 0.2% slippage
        min_commission=1.0
    )
