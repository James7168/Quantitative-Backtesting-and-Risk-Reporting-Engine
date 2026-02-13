from decimal import Decimal

from backtester.models import Bar, SignalType


def sma(bars: list[Bar], window: int) -> Decimal:
    """
    Calculate the Simple Moving Average of closing prices.

    Args:
        bars (list[Bar]): Market bars available at decision time.
        window (int): Number of most recent periods included in the average.

    Returns:
        Decimal: The computed moving average of closing prices.

    Raises:
        ValueError: If the number of bars is insufficient to compute the requested window.
    """
    if window <= 0:
        raise ValueError("SMA window must be > 0.")
    if len(bars) < window:
        raise ValueError(f"Not enough data to compute SMA: requires {window} values, got {len(bars)}.")
    
    closes = [bar.close for bar in bars[-window:]]
    return sum(closes) / Decimal(window)


def sma_crossover_strategy(bars: list[Bar], *, fast_w: int, slow_w: int) -> SignalType:
    """
    Generate a trading signal using a fast/slow SMA crossover rule.

    Args:
        bars (list[Bar]): Market bars available at decision time.

    Returns:
        SignalType: BUY, SELL, or HOLD.
    """
    if fast_w <= 0 or slow_w <= 0:
        raise ValueError("SMA windows must be > 0.")
    if fast_w >= slow_w:
        raise ValueError("fast window must be < slow window.")

    if len(bars) < slow_w + 1:
        return SignalType.HOLD
    
    fast_now = sma(bars, fast_w)
    slow_now = sma(bars, slow_w)

    fast_prev = sma(bars[:-1], fast_w)
    slow_prev = sma(bars[:-1], slow_w)

    if fast_prev <= slow_prev and fast_now > slow_now:
        return SignalType.BUY
    
    if fast_prev >= slow_prev and fast_now < slow_now:
        return SignalType.SELL
    
    return SignalType.HOLD