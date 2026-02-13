from datetime import datetime, timedelta
from decimal import Decimal
import pytest

from backtester.metrics import Metrics
from backtester.models import PortfolioSnapshot


def _snapshot(timestamp: datetime, equity: str) -> PortfolioSnapshot:
    value = Decimal(equity)
    return PortfolioSnapshot(
        timestamp = timestamp,
        cash = value,
        positions_value = Decimal("0"),
    )


def test_total_return_positive():
    start = datetime(2024, 1, 1)
    equity_curve = [
        _snapshot(start, "100"),
        _snapshot(start + timedelta(days = 1), "150"),
    ]

    metrics = Metrics(equity_curve = equity_curve)
    total_return = metrics.total_return()

    assert total_return == Decimal("0.5")


def test_total_return_negative():
    start = datetime(2024, 1, 1)
    equity_curve = [
        _snapshot(start, "200"),
        _snapshot(start + timedelta(days = 1), "100"),
    ]

    metrics = Metrics(equity_curve = equity_curve)
    total_return = metrics.total_return()

    assert total_return == Decimal("-0.5")


def test_total_return_raises_on_empty_curve():
    metrics = Metrics(equity_curve = [])

    with pytest.raises(ValueError, match = "does not yet contain any values."):
        metrics.total_return()


def test_total_return_raises_on_zero_initial_equity():
    start = datetime(2024, 1, 1)
    equity_curve = [
        _snapshot(start, "0"),
        _snapshot(start + timedelta(days = 1), "100"),
    ]

    metrics = Metrics(equity_curve = equity_curve)

    with pytest.raises(ValueError, match = "Initial equity must be > 0."):
        metrics.total_return()


def test_returns_series_basic():
    start = datetime(2024, 1, 1)
    equity_curve = [
        _snapshot(start, "100"),
        _snapshot(start + timedelta(days = 1), "110"),
        _snapshot(start + timedelta(days = 2), "121"),
    ]

    metrics = Metrics(equity_curve = equity_curve)
    returns_series = metrics.returns_series()

    assert len(returns_series) == 2

    _, first_return = returns_series[0]
    _, second_return = returns_series[1]

    assert first_return == Decimal("0.1")
    assert second_return == Decimal("0.1")


def test_returns_series_empty_for_single_point():
    start = datetime(2024, 1, 1)
    equity_curve = [
        _snapshot(start, "100"),
    ]

    metrics = Metrics(equity_curve = equity_curve)
    returns_series = metrics.returns_series()

    assert returns_series == []


def test_returns_series_raises_when_previous_equity_zero():
    start = datetime(2024, 1, 1)
    equity_curve = [
        _snapshot(start, "0"),
        _snapshot(start + timedelta(days = 1), "100"),
    ]

    metrics = Metrics(equity_curve = equity_curve)

    with pytest.raises(ValueError, match = "Previous equity must not be = 0."):
        metrics.returns_series()


def test_annualised_volatility_zero_when_no_returns():
    metrics = Metrics(equity_curve = [])

    annualised_volatility = metrics.annualised_volatility()

    assert annualised_volatility == 0.0


def test_annualised_volatility_non_zero():
    start = datetime(2024, 1, 1)
    equity_curve = [
        _snapshot(start, "100"),
        _snapshot(start + timedelta(days = 1), "110"),
        _snapshot(start + timedelta(days = 2), "99"),
    ]

    metrics = Metrics(equity_curve = equity_curve)

    annualised_volatility = metrics.annualised_volatility(periods_per_year = 1)

    assert annualised_volatility == pytest.approx(0.1, rel = 1e-6)


def test_max_drawdown_empty_curve_is_zero():
    metrics = Metrics(equity_curve = [])

    maximum_drawdown = metrics.max_drawdown()

    assert maximum_drawdown == 0.0


def test_max_drawdown_with_peak_and_trough():
    start = datetime(2024, 1, 1)
    equity_curve = [
        _snapshot(start, "100"),
        _snapshot(start + timedelta(days = 1), "120"),
        _snapshot(start + timedelta(days = 2), "80"),
        _snapshot(start + timedelta(days = 3), "130"),
    ]

    metrics = Metrics(equity_curve = equity_curve)
    maximum_drawdown = metrics.max_drawdown()

    expected_drawdown = float((Decimal("80") - Decimal("120")) / Decimal("120"))

    assert maximum_drawdown == pytest.approx(expected_drawdown, rel = 1e-6)


def test_sharpe_ratio_zero_when_no_returns():
    metrics = Metrics(equity_curve = [])

    sharpe_ratio = metrics.sharpe_ratio()

    assert sharpe_ratio == 0.0


def test_sharpe_ratio_zero_when_sigma_zero():
    start = datetime(2024, 1, 1)
    equity_curve = [
        _snapshot(start, "100"),
        _snapshot(start + timedelta(days = 1), "100"),
        _snapshot(start + timedelta(days = 2), "100"),
    ]

    metrics = Metrics(equity_curve = equity_curve)
    sharpe_ratio = metrics.sharpe_ratio(periods_per_year = 1)

    assert sharpe_ratio == 0.0


def test_sharpe_ratio_positive_example():
    start = datetime(2024, 1, 1)
    equity_curve = [
        _snapshot(start, "100"),
        _snapshot(start + timedelta(days = 1), "110"),
        _snapshot(start + timedelta(days = 2), "132"),
    ]

    metrics = Metrics(equity_curve = equity_curve)
    sharpe_ratio = metrics.sharpe_ratio(periods_per_year = 1)

    assert sharpe_ratio == pytest.approx(3.0, rel = 1e-6)


def test_win_rate_empty_is_zero():
    metrics = Metrics(equity_curve = [])

    win_rate = metrics.win_rate([])

    assert win_rate == 0.0


def test_win_rate_counts_only_positive_values():
    metrics = Metrics(equity_curve = [])

    realised_pnls = [
        Decimal("-1"),
        Decimal("0"),
        Decimal("2"),
        Decimal("3"),
    ]

    win_rate = metrics.win_rate(realised_pnls)

    assert win_rate == pytest.approx(0.5)


def test_average_win_loss_mixed_values():
    metrics = Metrics(equity_curve = [])

    realised_pnls = [
        Decimal("-1"),
        Decimal("0"),
        Decimal("2"),
        Decimal("3"),
    ]

    average_win, average_loss = metrics.average_win_loss(realised_pnls)

    assert average_win == Decimal("2.5")
    assert average_loss == Decimal("-1")


def test_average_win_loss_only_wins():
    metrics = Metrics(equity_curve = [])

    realised_pnls = [
        Decimal("1"),
        Decimal("2"),
        Decimal("3"),
    ]

    average_win, average_loss = metrics.average_win_loss(realised_pnls)

    assert average_win == Decimal("2")
    assert average_loss is None


def test_average_win_loss_only_losses():
    metrics = Metrics(equity_curve = [])

    realised_pnls = [
        Decimal("-1"),
        Decimal("-2"),
        Decimal("-3"),
    ]

    average_win, average_loss = metrics.average_win_loss(realised_pnls)

    assert average_win is None
    assert average_loss == Decimal("-2")


def test_average_win_loss_empty_sequence():
    metrics = Metrics(equity_curve = [])

    average_win, average_loss = metrics.average_win_loss([])

    assert average_win is None
    assert average_loss is None