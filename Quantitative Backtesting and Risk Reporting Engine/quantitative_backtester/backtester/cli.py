import argparse
from decimal import Decimal
from pathlib import Path

from backtester.data import load_bars
from backtester.execution import ExecutionModel
from backtester.metrics import Metrics
from backtester.models import Order, Side, SignalType
from backtester.portfolio import Portfolio  
from backtester.report import export_run
from backtester.strategy import sma_crossover_strategy


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments for a backtest run.

    This keeps configuration outside the code so the same backtester can be run with
    different datasets and assumptions (cash, fees, slippage, fill price) without edits.

    Returns:
        argparse.Namespace: Parsed runtime configuration.
    """
    p = argparse.ArgumentParser(
        description = "Quantitative Backtesting and Risk Reporting Engine."
    )
    p.add_argument("--data", type = Path, required = True)
    p.add_argument("--cash", type = Decimal, default = Decimal("10000"))
    p.add_argument("--symbol", type = str, default = "AAPL")
    p.add_argument("--quantity", type = Decimal, default = Decimal("1"))
    p.add_argument("--slippage-bps", type = Decimal, default = Decimal("0"))
    p.add_argument("--fee", type = Decimal, default = Decimal("0"))
    p.add_argument("--fill-trade-on", choices = ["open", "close"], default = "open")
    p.add_argument("--fast-window", type = int, default = 5)
    p.add_argument("--slow-window", type = int, default = 10)
    p.add_argument("--output", type = Path, default = Path("output"))
    p.add_argument("--no-plot", action = "store_true")
    return p.parse_args()


def main() -> int:
    """
    Run a full backtest.

    The system loads validated market data, generates trading signals, 
    executes position-aware trades with costs, updates portfolio state, 
    tracks equity over time, and outputs performance metrics.

    Trades fill on bar open/close per configuration,
    equity is marked to market on bar close.
    
    Returns:
        int: Process exit code.
    """
    args = parse_args()
    bars = load_bars(args.data)

    if args.fast_window <= 0 or args.slow_window <= 0:
        raise ValueError("SMA windows must be > 0.")
    if args.fast_window >= args.slow_window:
        raise ValueError("fast window must be < slow window.")

    exec_model = ExecutionModel(
        slippage_bps = args.slippage_bps,
        fee_per_trade = args.fee,
        fill_trade_on = args.fill_trade_on,
    )

    portfolio = Portfolio(cash = args.cash)

    for i in range(1, len(bars)):
        previous_bar = bars[i - 1]
        bar = bars[i]

        signal = sma_crossover_strategy(
            bars[: i], 
            fast_w=args.fast_window,
            slow_w=args.slow_window
        )

        has_position = args.symbol in portfolio.positions
        order = None

        if signal == SignalType.BUY and not has_position:
            order = Order(
                timestamp = previous_bar.timestamp,
                side = Side.BUY,
                quantity = args.quantity,
                symbol = args.symbol,
            )
        elif signal == SignalType.SELL and has_position:
            order = Order(
                timestamp = previous_bar.timestamp,
                side = Side.SELL,
                quantity = portfolio.positions[args.symbol].quantity,
                symbol = args.symbol,
            )

        if order is not None:
            trade = exec_model.execute(order, bar)
            portfolio.apply_trade(trade)

        portfolio.mark_to_market(
            bar.timestamp,
            {args.symbol: bar.close},
        )

    metrics_obj = Metrics(equity_curve = portfolio.equity_curve)
    metrics = {
        "total_return": metrics_obj.total_return(),
        "annualised_volatility": metrics_obj.annualised_volatility(),
        "max_drawdown": metrics_obj.max_drawdown(),
        "sharpe_ratio": metrics_obj.sharpe_ratio()
    }

    config = {
        "data": str(args.data),
        "symbol": args.symbol,
        "quantity": str(args.quantity),
        "cash": str(args.cash),
        "slippage_bps": str(args.slippage_bps),
        "fee_per_trade": str(args.fee),
        "fill_trade_on": args.fill_trade_on,
        "fast_window": args.fast_window,
        "slow_window": args.slow_window,
    }

    export_run(
        output_root = args.output,
        config = config,
        equity_curve = portfolio.equity_curve,
        trades = portfolio.trades,
        metrics = metrics,
        make_plot = not args.no_plot,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())