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

<img width="3500" height="1000" alt="QBE_Architecture" src="https://github.com/user-attachments/assets/9a24e7e7-bd91-42d6-8c9e-fe57603ba677" />

Bar data -> Strategy -> Signal (BUY / SELL / HOLD) -> Order -> Execution model -> Trade -> Portfolio update -> Metrics & Report

The system is designed as a deterministic state machine operating over a time-ordered sequence of market data. Portfolio updates are pure state transitions triggered only by executed trades, ensuring temporal consistency and preventing implicit side effects. The modular separation of strategy, execution, and portfolio logic allows alternative trading rules or execution models to be introduced without altering core state behaviour.

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
- validates schema,
- parses types explicitly (`datetime`, `Decimal`, `int`),
- enforces ordering and uniqueness,
- rejects invalid rows with row-number context.

This prioritises correctness, determinism, and transparency over convenience.

### Precision handling

Prices, quantities, and cash are represented with `Decimal` to reduce floating point drift.  
This is important in financial systems where rounding and cumulative error can meaningfully distort results.

### Determinism and explicit state transitions

The engine is designed to behave identically on repeated runs:
- explicit iteration order over bars,
- no hidden randomness,
- validated inputs,
- portfolio state changes are only triggered by explicit trades.

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

This project is intentionally scoped to stay simple and deterministic:

- Single instrument per run.
- Long-only position model (no shorting / leverage).
- Daily bar data.
- No corporate actions (splits/dividends).
- No live data feeds.
- No transaction cost models beyond fixed fees & slippage in bps.

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
