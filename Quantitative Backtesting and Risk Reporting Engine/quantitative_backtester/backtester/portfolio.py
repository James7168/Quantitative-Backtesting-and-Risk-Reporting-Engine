from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

from backtester.models import PortfolioSnapshot, Position, Side, Trade


@dataclass
class Portfolio:
    """
    Portfolio that receives executed Trades and maintains account state over time.

    Parameters:
        cash: Current liquid cash available for trading.
        equity_curve: Time-ordered list of PortfolioSnapshot objects.
        positions: Positions representing current holdings.
        trades: Log of executed trades applied to the portfolio.
    """
    cash: Decimal = Decimal("0")
    # Use of field() to ensure each instance gets its own independent list and dictionary state.
    equity_curve: list[PortfolioSnapshot] = field(default_factory = list)
    positions: dict[str, Position] = field(default_factory = dict)
    trades: list[Trade] = field(default_factory = list)

    def apply_trade(self, trade: Trade) -> None:
        """
        Apply an executed Trade to portfolio.

        Args:
            trade: Executed trade to apply.

        Raises:
            ValueError: If a BUY exceeds available cash, if a SELL exceeds position size,
                or if the trade side is unsupported.
        """
        if trade.side == Side.BUY:
            amount = trade.notional_value + trade.fee + trade.slippage
            if self.cash < amount:
                raise ValueError("Insufficient cash to execute BUY trade.")
            self.cash -= amount
        elif trade.side == Side.SELL:
            amount = trade.notional_value - trade.fee - trade.slippage
            self.cash += amount
        else:
            raise ValueError(f"Unsupported trade side: {trade.side}")
        
        position = self.positions.get(trade.symbol)

        if trade.side == Side.BUY:
            if position is None:
                self.positions[trade.symbol] = Position(
                    symbol = trade.symbol,
                    quantity = trade.quantity,
                    average_price = trade.price
                )
            
            else:
                new_quantity = position.quantity + trade.quantity
                new_average_price = (
                    (position.average_price * position.quantity) + 
                    (trade.price * trade.quantity)
                ) / new_quantity

                self.positions[trade.symbol] = Position(
                    symbol = trade.symbol,
                    quantity = new_quantity,
                    average_price = new_average_price
                )
        
        else:
            if position is None or position.quantity < trade.quantity:
                raise ValueError("Cannot sell more than existing position.")

            new_quantity = position.quantity - trade.quantity
            if new_quantity == 0:
                del self.positions[trade.symbol]
            else:
                self.positions[trade.symbol] = Position(
                    symbol = trade.symbol,
                    quantity = new_quantity,
                    average_price = position.average_price
                )
        
        self.trades.append(trade)

    def mark_to_market(self, timestamp: datetime, close_prices: dict[str, Decimal]) -> PortfolioSnapshot:
        """
        Calculate portfolio equity at a timestamp.

        Args:
            timestamp: Time associated with this valuation point.
            close_prices: Price used for valuation.

        Returns:
            PortfolioSnapshot: Snapshot containing cash, total positions value, and implied equity.

        Raises:
            ValueError: If any held symbol is missing from close_prices.
        """
        positions_value = Decimal("0")

        for symbol, position in self.positions.items():
            if symbol not in close_prices:
                raise ValueError(f"Missing close price for symbol: {symbol}.")
            positions_value += position.quantity * close_prices[symbol]
        
        snapshot = PortfolioSnapshot(
            timestamp = timestamp,
            cash = self.cash,
            positions_value = positions_value
        )

        self.equity_curve.append(snapshot)
        return snapshot