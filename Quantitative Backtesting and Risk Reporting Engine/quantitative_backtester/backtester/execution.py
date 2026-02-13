from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

from backtester.models import Bar, Order, Side, Trade


@dataclass(frozen = True)
class ExecutionModel:
    """
    Execution engine that converts Orders into Trades using a Bar, whilst applying
    slippage, transaction fees and a fill price.

    Parameters:
        slippage_bps: Slippage is modelled as an adverse price adjustment in basis points to 
            simulate execution friction, applied in bps.

        fee_per_trade: Fixed fee applied per executed trade.

        fill_trade_on: Determines which price from the Bar is used for execution.
            Default is "open", modelling execution at the next bar open.
    """
    fee_per_trade: Decimal = Decimal("0")
    slippage_bps: Decimal = Decimal("0")    
    fill_trade_on: Literal["open", "close"] = "open"

    def __post_init__(self) -> None:
        if self.slippage_bps < 0:
            raise ValueError("Slippage must be >= 0.")
        if self.fee_per_trade < 0:
            raise ValueError("Fee must be >= 0.")

    def execute(self, order: Order, bar: Bar) -> Trade:
        """
        Convert an Order into a filled Trade.

        Select base execution price, which is set to open unless configured otherwise,
        apply slippage, compute explicit slippage cost, & apply transaction fee.

        Args:
            order: Instruction to trade.
            bar: Market data used to determine fill price.

        Returns:
            Trade: Executed trade including friction costs.
        """
        if order.quantity <= 0:
            raise ValueError("Order quantity must be > 0.")
        if not order.symbol:
            raise ValueError("Order symbol required.")

        base_price = bar.open if self.fill_trade_on == "open" else bar.close

        slippage_rate = self.slippage_bps / Decimal("10_000")
        if order.side == Side.BUY:
            fill_price = base_price * (Decimal("1") + slippage_rate)
        else:
            fill_price = base_price * (Decimal("1") - slippage_rate)

        # Absolute value applied, as cost should always be positive.
        slippage_cost = (fill_price - base_price).copy_abs() * order.quantity

        fee = self.fee_per_trade

        return Trade(
            timestamp = bar.timestamp,
            side = order.side,
            quantity = order.quantity,
            price = fill_price,
            fee = fee,
            slippage = slippage_cost,
            symbol = order.symbol
        )