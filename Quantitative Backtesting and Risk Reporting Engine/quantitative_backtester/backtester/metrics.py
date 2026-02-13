from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
import math
from statistics import mean, pstdev
from typing import Sequence

from backtester.models import PortfolioSnapshot


@dataclass(frozen = True)
class Metrics:
    """
    Calculate common performance and risk metrics from a portfolio equity curve.

    Accounting focused metrics return Decimal for numerical precision, 
    statistical metrics return float for compatibility with math/statistics.

    Parameters:
        equity_curve: The equity curve is a time-ordered list of PortfolioSnapshot objects produced by
            the portfolio. Each snapshot is assumed to represent total portfolio equity at a timestamp.
    """
    equity_curve: list[PortfolioSnapshot] = field(default_factory = list)


    def total_return(self) -> Decimal:
        """
        Calculate the overall portfolio growth with total return.

        Returns:
            Decimal: Total return as a Decimal ratio.

        Raises:
            ValueError: If the equity curve is empty.
            ValueError: If initial equity is zero.
        """
        if len(self.equity_curve) == 0:
            raise ValueError("Equity curve does not yet contain any values.")
        else:
            final_equity = self.equity_curve[-1].equity
            initial_equity = self.equity_curve[0].equity
        
        if initial_equity == 0:
            raise ValueError("Initial equity must be > 0.")
        
        return (final_equity - initial_equity) / initial_equity
    

    def returns_series(self) -> list[tuple[datetime, Decimal]]:
        """
        Calculate the period-to-period percentage change in equity.

        Returns:
            list[tuple[datetime, Decimal]]:
                A list of pairs aligned to the current period. 
                The first period is dropped because it has no prior equity value.
        
        Raises:
            ValueError: If previous equity is zero.
        """
        if len(self.equity_curve) < 2:
            return []
        
        returns: list[tuple[datetime, Decimal]] = []

        for i in range(1, len(self.equity_curve)):
            previous_equity = self.equity_curve[i - 1].equity
            current_equity = self.equity_curve[i].equity
            timestamp = self.equity_curve[i].timestamp

            if previous_equity == 0:
                raise ValueError("Previous equity must not be = 0.")
        
            r_t = (current_equity / previous_equity) - Decimal("1")
            returns.append((timestamp, r_t))

        return returns
    

    def annualised_volatility(self, periods_per_year: int = 252) -> float:
        """
        Calculate annualised volatility of returns.

        Measure of an investment's return dispersion scaled to a one-year period, 
        representing the expected range of price fluctuations.

        Args:
            periods_per_year: Number of return periods in one year.

        Returns:
            float: Annualised volatility.
        """
        returns = self.returns_series()

        values = [float(r) for _, r in returns]

        if len(values) == 0:
            return 0.0
        
        volatility_per_period = pstdev(values)

        return volatility_per_period * math.sqrt(periods_per_year)


    def max_drawdown(self) -> float:
        """
        Calculate maximum drawdown over the equity curve.

        A risk metric that measures the largest percentage decline from a portfolio's
        peak value to its lowest point before a new peak is reached.

        Returns:
            float: Maximum drawdown as a non-positive number.
        """
        if len(self.equity_curve) == 0:
            return 0.0
        
        running_max = self.equity_curve[0].equity
        worst_drawdown = Decimal("0")

        for snapshot in self.equity_curve:
            equity = snapshot.equity
            if equity > running_max:
                running_max = equity

            if running_max == 0:
                continue

            drawdown = (equity - running_max) / running_max
            if drawdown < worst_drawdown:
                worst_drawdown = drawdown

        return float(worst_drawdown)
    

    def sharpe_ratio(self, periods_per_year: int = 252) -> float:
        """
        Calculate the annualised Sharpe ratio.

        A risk-adjusted performance metric that measures how much excess return an 
        investment generates for each unit of volatility.

        Args:
            periods_per_year: Number of return periods in one year.

        Returns:
            float: Annualised Sharpe ratio.
        """
        returns = self.returns_series()
        values = [float(r) for _, r in returns]

        if len(values) == 0:
            return 0.0
        
        mean_return = mean(values)
        sigma = pstdev(values)

        if sigma == 0.0:
            return 0.0
        
        return (mean_return / sigma) * math.sqrt(periods_per_year)
    

    def win_rate(self, realised_pnls: Sequence[Decimal]) -> float:
        """
        Calculate win rate from realised trade P&L's.

        The proportion of trades that are profitable, 
        showing how often a strategy produces a positive outcome.

        Args:
            realised_pnls: Sequence of per-trade realised  values.

        Returns:
            float: Win rate.
        """
        if len(realised_pnls) == 0:
            return 0.0
        
        wins = sum(1 for pnl in realised_pnls if pnl > 0)
        return wins / len(realised_pnls)
    

    def average_win_loss(self, realised_pnls: Sequence[Decimal]) -> tuple[Decimal | None, Decimal | None]:
        """
        Calculate average win and average loss from realised trade P&L's.

        The typical size of profitable trades compared to losing trades, 
        indicating whether gains outweigh losses over time.

        Args:
            realised_pnls: Sequence of per-trade realised P&L values.

        Returns:
            tuple[Decimal | None, Decimal | None]:
                average_win, average_loss, returns None for a side if there is no data for the category.
        """
        wins = [pnl for pnl in realised_pnls if pnl > 0]
        losses = [pnl for pnl in realised_pnls if pnl < 0]

        average_win = (sum(wins) / Decimal(len(wins))) if wins else None
        average_loss = (sum(losses) / Decimal(len(losses))) if losses else None

        return average_win, average_loss