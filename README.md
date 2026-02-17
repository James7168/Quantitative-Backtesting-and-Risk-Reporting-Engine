# Quantitative Backtesting and Risk Reporting Engine

A lightweight, deterministic backtesting engine for **single-instrument**, **daily-bar** strategies.  

It loads OHLCV data from CSV, generates trading signals, converts signals into orders, simulates fills with slippage/fees, updates a portfolio, and exports performance metrics + run artifacts.

This project is designed with production-inspired separation of concerns, strong domain modelling, explicit timelines, and tests across core modules.

---

## Project Overview

**What it solves**:
Provides a transparent and testable framework to evaluate simple rule-based strategies with realistic execution frictions.

**Target scope**:
- Single asset symbol.
- Daily bars.
- Rule-based strategies.
- Configurable execution assumptions: fee, slippage, fill price.
- Run exports: config, trades, equity curve, metrics, summary, optional plot.

---

## Architecture Overview

The architecture intentionally separates strategy, execution, and portfolio logic, allowing additional strategies or execution models to be added without modifying core state logic.

<img width="3222" height="381" alt="QBE_Architecture" src="https://github.com/user-attachments/assets/c56ce2a0-080d-443e-bc89-98178fe741d9" />

The system is designed as a state-transition model operating over a time-ordered sequence of market data. Portfolio state at time t depends only on the prior state and current inputs, eliminating lookahead bias and implicit side effects. State transitions are triggered exclusively by executed trades and explicit mark-to-market operations. The modular separation of strategy, execution, and portfolio components allows alternative trading rules or execution models to be introduced without modifying core state logic.

---

### Timeline conventions

- Signals are generated using only bars available at decision time.
- Orders are timestamped with the prior bar timestamp.
- Trades are executed using the next bar on open/close per configuration.
- Equity is marked to market using bar close prices.

---

## Key Design Decisions

### Domain-driven data structures

The system operates on strongly typed domain objects (`Bar`, `Order`, `Trade`, `Position`, `PortfolioSnapshot`) rather than raw arrays.  
Historical data is parsed into validated `Bar` objects that enforce OHLCV invariants at construction time.  
Downstream components derive values directly from these objects, keeping financial meaning explicit and avoiding fragile index-based logic.

### Data ingestion

Core ingestion avoids pandas and instead implements a strict CSV loader that:
- Validates schema.
- Parses types explicitly. (`datetime`, `Decimal`, `int`)
- Enforces ordering and uniqueness.
- Rejects invalid rows with row-number context.

The ingestion pipeline deliberately prioritises validation guarantees, reproducible execution, and structural clarity over convenience abstractions.

### Precision handling

Prices, quantities, and cash are represented with `Decimal` to reduce floating point drift.  
This is important in financial systems where rounding and cumulative error can meaningfully distort results.

### Predictability and explicit state transitions

The engine is designed to behave identically on repeated runs:
- Explicit iteration order over bars.
- No hidden randomness.
- Validated inputs.
- Portfolio state changes are only triggered by explicit trades.

Many dataclasses are frozen to enforce immutability where appropriate.

### Sharpe ratio assumption

For the MVP, the Sharpe ratio assumes a zero risk-free rate.  
This can be extended by subtracting a time-aligned risk-free return series.

---

## Module Responsibilities

- `data.py`: CSV ingestion & validation into `Bar`.
- `models.py`: domain language. (Bar, Order, Trade, Position, etc.)
- `strategy.py`: signal generation only. (SMA crossover)
- `execution.py`: fills, slippage, fees, fill price selection.
- `portfolio.py`: state transitions. (cash, positions, trades, equity curve)
- `metrics.py`: performance and risk metrics derived from equity curve.
- `report.py`: export artifacts. (CSV/JSON/MD & optional plot)
- `cli.py`: ties everything together.

---

## Limitations / Scope

This project is intentionally scoped to stay simple:

- Single instrument per run.
- Long-only position model (no shorting / leverage).
- Daily bar data.
- No corporate actions (splits/dividends).
- No live data feeds.
- No transaction cost models beyond fixed fees & slippage in bps.

---

## Future Extensions

Several extensions could be explored to deepen the quantitative and algorithmic foundations of the system:

- **Risk-based position sizing**  
  Replace fixed trade quantities with dynamic sizing derived from portfolio equity and rolling volatility estimates, formalising capital allocation under explicit risk constraints.

- **Online volatility estimation**  
  Implement incremental (O(n)) rolling statistics to avoid repeated window recomputation and improve scalability for larger datasets.

- **Drawdown-aware allocation**  
  Introduce capital scaling based on peak-to-trough drawdown, modelling adaptive risk exposure under adverse conditions.

- **Multi-asset portfolio generalisation**  
  Extend the state model to support correlated instruments and portfolio-level capital constraints.

- **Event-driven execution engine**  
  Refactor the bar-iteration loop into an event-based architecture to support higher-frequency data and alternative market data feeds.

These extensions would allow the system to evolve from a single-strategy backtester into a more generalised quantitative research framework.

---

## How to Run

### Install pip

pip install -e .[dev]

### Run backtest

python -m backtester.cli \
  --data data/sample_prices.csv \
  --symbol AAPL \
  --cash 10000 \
  --quantity 1 \
  --fast-window 5 \
  --slow-window 10 \
  --fill-trade-on open \
  --slippage-bps 0 \
  --fee 0 \
  --output output

---

## Tests

### Unit tests
- Data ingestion and validation.
- Strategy logic and crossover detection.
- Execution model.
- Portfolio state transitions and mark-to-market.
- Performance metrics.

### Run unit tests

pytest -q
