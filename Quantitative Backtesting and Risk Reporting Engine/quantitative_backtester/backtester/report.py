import csv
from dataclasses import asdict, is_dataclass
from datetime import datetime
from decimal import Decimal
import json
from pathlib import Path
from typing import Any

from backtester.models import PortfolioSnapshot, Trade


def _make_run_directory(output_root: Path) -> Path:
    """
    Create a timestamped run directory inside the specified output root.

    Args:
        output_root (Path): Base directory where run folders are stored.

    Returns:
        Path: Newly created run directory path.
    """
    output_root.mkdir(parents = True, exist_ok = True)

    stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    run_dir = output_root / f"run_{stamp}"
    run_dir.mkdir(parents = True, exist_ok = False)
    return run_dir


def _json_default(obj: Any) -> Any:
    """
    Custom JSON serialiser for non-native JSON types.

    Args:
        obj (Any): Object to serialise.

    Returns:
        Any: JSON-serialisable representation.

    Raises:
        TypeError: If the object type is unsupported.
    """
    if isinstance(obj, Decimal):
        return str(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    if is_dataclass(obj):
        return asdict(obj)
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serialisable.")

def _write_json(path: Path, payload: dict[str, Any]) -> None:
    """
    Write structured data to a JSON file.

    Args:
        path (Path): Destination file path.
        payload (dict[str, Any]): Data to serialise.
    """
    with path.open("w", encoding = "utf-8") as fh:
        json.dump(payload, fh, indent = 2, default = _json_default, sort_keys = True)


def _write_equity_curve_csv(path: Path, equity_curve: list[PortfolioSnapshot]) -> None:
    """
    Export the portfolio equity curve to CSV format.

    Args:
        path (Path): Destination CSV file.
        equity_curve (list[PortfolioSnapshot]): Time-ordered portfolio snapshots.
    """
    fieldnames = ["timestamp", "cash", "positions_value", "equity"]

    with path.open("w", newline = "", encoding = "utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames = fieldnames)
        writer.writeheader()

        for snapshot in equity_curve:
            writer.writerow(
                {
                    "timestamp": snapshot.timestamp.isoformat(),
                    "cash": str(snapshot.cash),
                    "positions_value": str(snapshot.positions_value),
                    "equity": str(snapshot.equity)
                }
            )


def _write_trades_csv(path: Path, trades: list[Trade]) -> None:
    """
    Export executed trades to CSV format.

    Args:
        path (Path): Destination CSV file.
        trades (list[Trade]): Executed trades.
    """
    fieldnames = [
        "timestamp",
        "symbol",
        "side",
        "quantity",
        "price",
        "fee",
        "slippage",
        "notional_value",
        "transaction_cost"
    ]

    with path.open("w", newline = "", encoding = "utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames = fieldnames)
        writer.writeheader()

        for t in trades:
            writer.writerow(
                {
                    "timestamp": t.timestamp.isoformat(),
                    "symbol": t.symbol,
                    "side": t.side.value if hasattr(t.side, "value") else str(t.side),
                    "quantity": str(t.quantity),
                    "price": str(t.price),
                    "fee": str(t.fee),
                    "slippage": str(t.slippage),
                    "notional_value": str(t.notional_value),
                    "transaction_cost": str(t.transaction_cost),
                }
            )


def _write_summary_md(
    *,
    path: Path,
    config: dict[str, Any],
    metrics: dict[str, Any],
    equity_curve: list[PortfolioSnapshot],
    trades: list[Trade],
) -> None:
    """
    Generate a Markdown summary report for a backtest run.

    Args:
        path (Path): Destination Markdown file.
        config (dict[str, Any]): Backtest configuration parameters.
        metrics (dict[str, Any]): Calculated performance metrics.
        equity_curve (list[PortfolioSnapshot]): Portfolio equity history.
        trades (list[Trade]): Executed trades.
    """
    lines: list[str] = []

    lines.append("# Backtest Summary\n")

    lines.append("## Run Info\n")
    lines.append(f"- Generated: {datetime.now().isoformat()}\n")
    lines.append(f"- Bars: {len(equity_curve)}\n")
    lines.append(f"- Trades: {len(trades)}\n")

    lines.append("\n## Config\n")
    for k in sorted(config.keys()):
        lines.append(f"- {k}: {config[k]}\n")

    lines.append("\n## Metrics\n")
    if not metrics:
        lines.append("_No metrics provided._\n")
    else:
        lines.append("\n| Metric | Value |\n|---|---|\n")
        for k in sorted(metrics.keys()):
            lines.append(f"| {k} | {metrics[k]} |\n")

    if equity_curve:
        start = equity_curve[0].equity
        end = equity_curve[-1].equity
        lines.append("\n## Equity\n")
        lines.append(f"- Start equity: {start}\n")
        lines.append(f"- End equity: {end}\n")

    with path.open("w", encoding="utf-8") as fh:
        fh.writelines(lines)


def _plot_equity_curve_png(path: Path, equity_curve: list[PortfolioSnapshot]) -> None:
    """
    Generate and save an equity curve plot as PNG.

    Plotting is optional and skipped if matplotlib is unavailable.

    Args:
        path (Path): Destination image file.
        equity_curve (list[PortfolioSnapshot]): Portfolio equity history.
    """
    if not equity_curve:
        return

    try:
        import matplotlib.pyplot as plt
    except Exception:
        return

    xs = [s.timestamp for s in equity_curve]
    ys = [float(s.equity) for s in equity_curve]

    plt.figure()
    plt.plot(xs, ys)
    plt.title("Equity Curve")
    plt.xlabel("Time")
    plt.ylabel("Equity")
    plt.tight_layout()
    plt.savefig(path)
    plt.close()


def export_run(
        *,
        output_root: Path,
        config: dict[str, Any],
        equity_curve: list[PortfolioSnapshot],
        trades: list[Trade],
        metrics: dict[str, Any],
        make_plot: bool = True
) -> Path:
    """
    Export all backtest artifacts into a timestamped run directory.

    Args:
        output_root (Path): Base output directory.
        config (dict[str, Any]): Backtest configuration parameters.
        equity_curve (list[PortfolioSnapshot]): Portfolio equity history.
        trades (list[Trade]): Executed trades.
        metrics (dict[str, Any]): Performance metrics.
        make_plot (bool): Whether to generate an equity curve PNG.

    Returns:
        Path: Path to the created run directory.
    """
    run_dir = _make_run_directory(output_root)

    _write_json(run_dir / "config.json", config)
    _write_equity_curve_csv(run_dir / "equity_curve.csv", equity_curve)
    _write_trades_csv(run_dir / "trades.csv", trades)
    _write_json(run_dir / "metrics.json", metrics)
    _write_summary_md(
        path=run_dir / "summary.md",
        config=config,
        metrics=metrics,
        equity_curve=equity_curve,
        trades=trades,
    )

    if make_plot:
        _plot_equity_curve_png(run_dir / "equity_curve.png", equity_curve)

    return run_dir