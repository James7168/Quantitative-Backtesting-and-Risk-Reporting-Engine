from datetime import datetime
from decimal import Decimal
import pytest

from backtester.models import Side, Trade
from backtester.portfolio import Portfolio


def _trade(
    *,
    timestamp: datetime,
    side: Side,
    symbol: str = "AAPL",
    quantity: str = "1",
    price: str = "100",
    fee: str = "0",
    slippage: str = "0",
) -> Trade:
    return Trade(
        timestamp = timestamp,
        side = side,
        quantity = Decimal(quantity),
        price = Decimal(price),
        fee = Decimal(fee),
        slippage = Decimal(slippage),
        symbol = symbol,
    )


def test_apply_buy_reduces_cash_and_creates_position():
    position = Portfolio(cash = Decimal("1000"))
    trade = _trade(
        timestamp = datetime(2024, 1, 1),
        side = Side.BUY,
        quantity = "2",
        price = "100",
        fee = "1",
        slippage = "0.50",
    )

    position.apply_trade(trade)

    assert position.cash == Decimal("798.50")
    assert "AAPL" in position.positions
    assert position.positions["AAPL"].quantity == Decimal("2")
    assert position.positions["AAPL"].average_price == Decimal("100")
    assert position.trades == [trade]


def test_apply_buy_raises_if_insufficient_cash():
    position = Portfolio(cash = Decimal("50"))
    trade = _trade(
        timestamp = datetime(2024, 1, 1),
        side = Side.BUY,
        quantity = "1",
        price = "100",
    )

    with pytest.raises(ValueError, match = "Insufficient cash."):
        position.apply_trade(trade)


def test_apply_buy_updates_weighted_average_price():
    position = Portfolio(cash = Decimal("10_000"))

    trade_1 = _trade(
        timestamp = datetime(2024, 1, 1),
        side = Side.BUY,
        quantity = "2",
        price = "100",
    )

    trade_2 = _trade(
        timestamp = datetime(2024, 1, 2),
        side = Side.BUY,
        quantity = "1",
        price = "130",
    )

    position.apply_trade(trade_1)
    position.apply_trade(trade_2)

    assert position.positions["AAPL"].quantity == Decimal("3")
    assert position.positions["AAPL"].average_price == Decimal("110")


def test_apply_sell_increases_cash_and_reduces_position_quantity():
    position = Portfolio(cash = Decimal("10_000"))

    trade_buy = _trade(
        timestamp = datetime(2024, 1, 1),
        side = Side.BUY,
        quantity = "3",
        price = "100",
    )

    trade_sell = _trade(
        timestamp = datetime(2024, 1, 2),
        side = Side.SELL,
        quantity = "1",
        price = "120",
        fee = "1",
        slippage = "0.50",
    )

    position.apply_trade(trade_buy)
    cash_after_buy = position.cash

    position.apply_trade(trade_sell)

    assert position.cash == cash_after_buy + Decimal("118.50")
    assert position.positions["AAPL"].quantity == Decimal("2")
    assert position.positions["AAPL"].average_price == Decimal("100")


def test_apply_sell_closes_position_when_quantity_zero():
    position = Portfolio(cash = Decimal("10_000"))

    trade_buy = _trade(
        timestamp = datetime(2024, 1, 1),
        side = Side.BUY,
        quantity = "2",
        price = "100",
    )

    trade_sell = _trade(
        timestamp = datetime(2024, 1, 2),
        side = Side.SELL,
        quantity = "2",
        price = "100",
    )

    position.apply_trade(trade_buy)
    position.apply_trade(trade_sell)

    assert "AAPL" not in position.positions


def test_apply_sell_raises_if_no_position():
    position = Portfolio(cash = Decimal("10_000"))

    trade = _trade(
        timestamp = datetime(2024, 1, 1),
        side = Side.SELL,
        quantity = "1",
        price = "100",
    )

    with pytest.raises(ValueError, match = "Cannot sell more than existing position."):
        position.apply_trade(trade)


def test_apply_sell_raises_if_sell_exceeds_position():
    position = Portfolio(cash = Decimal("10_000"))

    trade_buy = _trade(
        timestamp = datetime(2024, 1, 1),
        side = Side.BUY,
        quantity = "1",
        price = "100",
    )

    trade_sell = _trade(
        timestamp = datetime(2024, 1, 2),
        side = Side.SELL,
        quantity = "2",
        price = "100",
    )

    position.apply_trade(trade_buy)

    with pytest.raises(ValueError, match = "Cannot sell more than existing position."):
        position.apply_trade(trade_sell)


def test_mark_to_market_creates_snapshot_and_appends_to_equity_curve():
    position = Portfolio(cash = Decimal("1000"))

    trade = _trade(
        timestamp = datetime(2024, 1, 1),
        side = Side.BUY,
        quantity = "2",
        price = "100",
    )

    position.apply_trade(trade)

    timestamp = datetime(2024, 1, 2)
    snapshot = position.mark_to_market(timestamp, {"AAPL": Decimal("120")})

    assert snapshot.timestamp == timestamp
    assert snapshot.cash == position.cash
    assert snapshot.positions_value == Decimal("240")
    assert snapshot.equity == position.cash + Decimal("240")
    assert position.equity_curve[-1] == snapshot


def test_mark_to_market_raises_if_missing_price_for_held_symbol():
    position = Portfolio(cash = Decimal("1000"))

    trade = _trade(
        timestamp = datetime(2024, 1, 1),
        side = Side.BUY,
        quantity = "1",
        price = "100",
    )

    position.apply_trade(trade)

    with pytest.raises(ValueError, match = "Missing close price for symbol."):
        position.mark_to_market(datetime(2024, 1, 2), {})