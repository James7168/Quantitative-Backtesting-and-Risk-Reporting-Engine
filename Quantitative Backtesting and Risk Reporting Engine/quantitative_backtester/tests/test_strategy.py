from datetime import datetime, timedelta
from decimal import Decimal
import pytest

from backtester.models import Bar, SignalType
from backtester.strategy import sma_crossover_strategy


def _bar(ts, close):
    return Bar(
        timestamp = ts,
        # high = low = open = close, to test logic.
        open = close,
        high = close,
        low = close,
        close = close,
        volume = 1,
    )


def test_returns_hold_when_not_enough_data():
    start = datetime(2024, 1, 1)
    bars = [_bar(start + timedelta(days = i), Decimal("100")) for i in range(10)]

    signal = sma_crossover_strategy(bars, fast_w = 5, slow_w = 10)

    assert signal == SignalType.HOLD


def test_returns_hold_when_no_crossover():
    start = datetime(2024, 1, 1)
    closes = [Decimal("100")] * 20
    bars = [_bar(start + timedelta(days = i), closes[i]) for i in range(len(closes))]

    signal = sma_crossover_strategy(bars, fast_w = 5, slow_w = 10)

    assert signal == SignalType.HOLD


def test_buy_signal_on_upward_crossover():
    start = datetime(2024, 1, 1)

    closes = [Decimal("100")] * 10 + [Decimal("200")]
    bars = [_bar(start + timedelta(days = i), closes[i]) for i in range(len(closes))]

    signal = sma_crossover_strategy(bars, fast_w = 5, slow_w = 10)

    assert signal == SignalType.BUY


def test_sell_signal_on_downward_crossover():
    start = datetime(2024, 1, 1)

    closes = [Decimal("200")] * 10 + [Decimal("100")]
    bars = [_bar(start + timedelta(days = i), closes[i]) for i in range(len(closes))]

    signal = sma_crossover_strategy(bars, fast_w = 5, slow_w = 10)

    assert signal == SignalType.SELL


def test_invalid_fast_window():
    start = datetime(2024, 1, 1)

    closes = [Decimal("200")] * 10 + [Decimal("100")]
    bars = [_bar(start + timedelta(days = i), closes[i]) for i in range(len(closes))]

    with pytest.raises(ValueError):
        sma_crossover_strategy(bars, fast_w = -1, slow_w = 10)


def test_invalid_slow_window():
    start = datetime(2024, 1, 1)

    closes = [Decimal("200")] * 10 + [Decimal("100")]
    bars = [_bar(start + timedelta(days = i), closes[i]) for i in range(len(closes))]

    with pytest.raises(ValueError):
        sma_crossover_strategy(bars, fast_w = 5, slow_w = -1)


def test_invalid_window_relationship():
    start = datetime(2024, 1, 1)

    closes = [Decimal("200")] * 10 + [Decimal("100")]
    bars = [_bar(start + timedelta(days = i), closes[i]) for i in range(len(closes))]

    with pytest.raises(ValueError):
        sma_crossover_strategy(bars, fast_w = 10, slow_w = 5)