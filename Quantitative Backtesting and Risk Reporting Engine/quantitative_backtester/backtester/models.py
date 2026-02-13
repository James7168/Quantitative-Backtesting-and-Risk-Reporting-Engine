from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum


@dataclass(frozen = True)
class Bar:
    """
    Market data candlestick representing price behaviour over a fixed time interval.

    Parameters:
        timestamp: Date and time associated with the bar.
        open: Opening price for the interval.
        high: Highest traded price during the interval.
        low: Lowest traded price during the interval.
        close: Closing price for the interval.
        volume: Total traded quantity during the interval.
    """
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int

    def __post_init__(self):
        if any(p <= 0 for p in (self.open, self.close, self.high, self.low)):
            raise ValueError("Prices must be positive!")
    
        if self.high < max(self.open, self.close):
            raise ValueError("High must be >= open and close.")
        
        if self.low > min(self.open, self.close):
            raise ValueError("Low must be <= open and close.")
        
        if self.high < self.low:
            raise ValueError("High must be >= low.")
        
        if self.volume < 0:
            raise ValueError("Volume cannot be negative.")


class SignalType(Enum):
    """
    Enumeration of possible strategy decisions.

    Does not represent an executed transaction.

    Parameters:
        BUY: Indicates a long entry or position increase.
        SELL: Indicates a position reduction or exit.
        HOLD: Indicates no trading action.
    """
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


@dataclass(frozen = True)
class Signal:
    """
    Alert that suggests an opportunity to buy, sell, or hold an asset.

    Parameters:
        timestamp: Time at which the signal was generated.
        signal_type: Directional decision.
        symbol: Asset identifier.
    """
    timestamp: datetime
    signal_type: SignalType
    symbol: str

    def __post_init__(self):
        if not self.symbol.strip():
            raise ValueError("Signal must contain a symbol.")


class Side(Enum):
    """
    Enumeration representing the direction of an executed market transaction.

    Used by Orders and Trades after a strategy decision is translated into an action.

    Parameters:
        BUY: Represents a purchase transaction.
        SELL: Represents a sale transaction.
    """
    BUY = "BUY"
    SELL = "SELL"


@dataclass(frozen = True)
class Order:
    """
    Request mechanism to enter or exit a position in the market.

    Parameters:
        timestamp: Time at which the order is submitted.
        side: Direction of the order.
        quantity: Number of units to transact.
        symbol: Asset identifier.
    """
    timestamp: datetime
    side: Side
    quantity: Decimal
    symbol: str

    def __post_init__(self):
        if self.quantity <= 0:
            raise ValueError("Order quantity must be > 0.")
        
        if not self.symbol.strip():
            raise ValueError("Order must contain a symbol.")
        

@dataclass(frozen = True)
class Trade:
    """
    Result of an executed order.

    Parameters:
        timestamp: Execution time.
        side: Direction of the executed trade.
        quantity: Executed quantity.
        price: Actual fill price after slippage adjustment.
        fee: Transaction fee.
        slippage: Modelled execution friction cost.
        symbol: Asset identifier.
    """
    timestamp: datetime
    side: Side
    quantity: Decimal
    price: Decimal
    fee: Decimal
    slippage: Decimal
    symbol: str

    def __post_init__(self):
        if self.quantity <= 0:
            raise ValueError("Trade quantity must be > 0.")
        
        if self.price <= 0:
            raise ValueError("Trade price must be > 0.")
        
        if self.fee < 0:
            raise ValueError("Trade fee cannot be < 0.")
        
        if self.slippage < 0:
            raise ValueError("Trade slippage cannot be < 0.")
        
        if not self.symbol.strip():
            raise ValueError("Trade must contain a symbol.")
    
    @property
    def notional_value(self) -> Decimal:
        """
        Calculate the gross market value of the trade.

        Notional value represents the total market value of the trade
        before transaction costs are applied.

        Returns:
            Decimal: Quantity multiplied by execution price.
        """
        return self.quantity * self.price
    
    @property
    def transaction_cost(self) -> Decimal:
        """
        Calculate total associated cost to an executed trade.

        Returns:
            Decimal: Sum of fee and slippage cost.
        """
        return self.fee + self.slippage


@dataclass(frozen = True)
class Position:
    """
    Aggregated holdings of a specific asset.

    Current amount of shares held in a given asset, 
    aggregated from all executed trades.

    Parameters:
        symbol: Asset identifier.
        quantity: Current units held.
        average_price: Weighted average cost basis.
    """
    symbol: str
    quantity: Decimal
    average_price: Decimal

    def __post_init__(self):
        if self.quantity <= 0:
            raise ValueError("Position quantity must be > 0.")
        
        if self.average_price <= 0:
            raise ValueError("Average price must be > 0.")
        
        if not self.symbol.strip():
            raise ValueError("Position must contain a symbol.")


@dataclass(frozen = True)
class PortfolioSnapshot:
    """
    State of the portfolio at a specific moment in time.

    These snapshots collectively form the equity curve, which is later 
    used for performance and risk analysis.

    Parameters:
        timestamp: The point in time at which the portfolio is evaluated.

        cash: Liquid capital available in the portfolio at this timestamp.

        positions_value: Aggregate market value of all open positions, computed using 
            current market prices.
    """
    timestamp: datetime
    cash: Decimal
    positions_value: Decimal

    @property
    def equity(self) -> Decimal:
        """
        Total value of all current assets.

        Returns:
            Decimal: Total portfolio value at the given timestamp.
        """
        return self.cash + self.positions_value