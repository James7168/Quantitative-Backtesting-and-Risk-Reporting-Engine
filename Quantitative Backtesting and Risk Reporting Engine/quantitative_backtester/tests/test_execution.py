from datetime import datetime
from decimal import Decimal
import pytest

from backtester.execution import ExecutionModel
from backtester.models import Bar, Order, Side


def _bar(
    *,
    timestamp: datetime,
    open: str = "100",
    close: str = "110",
) -> Bar:
    open_price = Decimal(open)
    close_price = Decimal(close)
    high = max(open_price, close_price)
    low = min(open_price, close_price)

    return Bar(
        timestamp = timestamp,
        open = open_price,
        high = high,
        low = low,
        close = close_price,
        volume = 1,
    )


def _order(
    *,
    timestamp: datetime,
    side: Side,
    quantity: str = "1",
    symbol: str = "AAPL",
) -> Order:
    return Order(
        timestamp = timestamp,
        side = side,
        quantity = Decimal(quantity),
        symbol = symbol,
    )


def test_init_raises_when_slippage_negative():
    with pytest.raises(ValueError, match = "Slippage must be >= 0."):
        ExecutionModel(slippage_bps = Decimal("-1"))


def test_init_raises_when_fee_negative():
    with pytest.raises(ValueError, match = "Fee must be >= 0."):
        ExecutionModel(fee_per_trade = Decimal("-0.01"))


def test_execute_uses_open_as_base_price_by_default():
    model = ExecutionModel(fill_trade_on = "open")
    bar = _bar(timestamp = datetime(2024, 1, 2), open = "100", close = "110")
    order = _order(timestamp = datetime(2024, 1, 1), side = Side.BUY)

    trade = model.execute(order, bar)

    assert trade.timestamp == bar.timestamp
    assert trade.price == Decimal("100")


def test_execute_uses_close_as_base_price_when_configured():
    model = ExecutionModel(fill_trade_on = "close")
    bar = _bar(timestamp = datetime(2024, 1, 2), open = "100", close = "110")
    order = _order(timestamp = datetime(2024, 1, 1), side = Side.BUY)

    trade = model.execute(order, bar)

    assert trade.timestamp == bar.timestamp
    assert trade.price == Decimal("110")


def test_buy_slippage_increases_fill_price_and_cost_is_positive():
    model = ExecutionModel(slippage_bps = Decimal("50"))  # 0.50%
    bar = _bar(timestamp = datetime(2024, 1, 2), open = "100", close = "100")
    order = _order(timestamp = datetime(2024, 1, 1), side = Side.BUY, quantity = "2")

    trade = model.execute(order, bar)

    # Fill price: 100 * (1 + 0.005) = 100.5
    assert trade.price == Decimal("100.5")

    # Slippage cost: (100.5 - 100) * 2 = 1.0
    assert trade.slippage == Decimal("1.0")
    assert trade.slippage >= 0


def test_sell_slippage_decreases_fill_price_and_cost_is_positive():
    model = ExecutionModel(slippage_bps = Decimal("50"))  # 0.50%
    bar = _bar(timestamp = datetime(2024, 1, 2), open = "100", close = "100")
    order = _order(timestamp = datetime(2024, 1, 1), side = Side.SELL, quantity = "2")

    trade = model.execute(order, bar)

    # Fill price: 100 * (1 - 0.005) = 99.5
    assert trade.price == Decimal("99.5")

    # Slippage cost: (99.5 - 100) * 2 = 1.0
    assert trade.slippage == Decimal("1.0")
    assert trade.slippage >= 0


def test_fee_is_applied_as_fixed_per_trade_value():
    model = ExecutionModel(fee_per_trade = Decimal("1.25"))
    bar = _bar(timestamp = datetime(2024, 1, 2), open = "100", close = "100")
    order = _order(timestamp = datetime(2024, 1, 1), side = Side.BUY)

    trade = model.execute(order, bar)

    assert trade.fee == Decimal("1.25")


def test_trade_fields_preserve_order_identity_and_symbol():
    model = ExecutionModel(slippage_bps = Decimal("0"), fee_per_trade = Decimal("0"))
    bar = _bar(timestamp = datetime(2024, 1, 2), open = "100", close = "110")
    order = _order(timestamp = datetime(2024, 1, 1), side = Side.SELL, quantity = "3", symbol = "MSFT")

    trade = model.execute(order, bar)

    assert trade.side == order.side
    assert trade.quantity == order.quantity
    assert trade.symbol == order.symbol