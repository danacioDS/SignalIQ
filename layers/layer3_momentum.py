"""Layer 3 momentum — daily return calculation and rolling z-score processor."""

import math
from collections import deque
from datetime import date

from layers.layer3_config import CONFIG


class MomentumProcessor:
    """Compute daily returns and rolling momentum z-scores per ticker.

    Price history accumulates indefinitely; returns are stored in a
    fixed-length deque.  A two-phase commit (pending → history) prevents
    look-ahead bias: the current day's return stays in ``pending_returns``
    until ``commit_pending_returns`` is called (typically at end-of-day by
    the orchestrator), so rolling z-scores are always calculated against a
    baseline that excludes the current observation.
    """

    def __init__(self, config=CONFIG):
        self._config = config
        self.return_history: dict[str, deque] = {}
        self.price_history: dict[str, dict[date, float]] = {}
        self.pending_returns: dict[str, dict[date, float]] = {}

    @staticmethod
    def calculate_daily_return(price_today: float, price_yesterday: float) -> float:
        """Simple daily return: (today - yesterday) / yesterday."""
        if price_yesterday == 0:
            return 0.0
        return (price_today - price_yesterday) / price_yesterday

    def add_price(self, ticker: str, dt: date, adj_close: float) -> float | None:
        """Store a price and return the daily return (or ``None`` on first day).

        The return is placed in **pending** — it will not appear in
        ``return_history`` until ``commit_pending_returns`` is called.
        """
        if ticker not in self.price_history:
            self.price_history[ticker] = {}

        self.price_history[ticker][dt] = adj_close

        # Prune old prices beyond 2x the config window to prevent unbounded growth
        if len(self.price_history[ticker]) > self._config.max_history_days * 2:
            keep_from = sorted(self.price_history[ticker])[-self._config.max_history_days]
            self.price_history[ticker] = {
                d: v for d, v in self.price_history[ticker].items() if d >= keep_from
            }

        prior_dates = [d for d in self.price_history[ticker] if d < dt]
        if not prior_dates:
            return None

        prev_date = max(prior_dates)
        daily_return = self.calculate_daily_return(adj_close, self.price_history[ticker][prev_date])

        if ticker not in self.pending_returns:
            self.pending_returns[ticker] = {}
        self.pending_returns[ticker][dt] = daily_return

        return daily_return

    def commit_pending_returns(self, ticker: str, dt: date) -> None:
        """Move pending returns for dates <= *dt* into ``return_history``.

        Typically called by the orchestrator during **finalize_day**.
        """
        pending = self.pending_returns.get(ticker)
        if not pending:
            return

        if ticker not in self.return_history:
            self.return_history[ticker] = deque(maxlen=self._config.max_history_days)

        for d in sorted(d for d in pending if d <= dt):
            self.return_history[ticker].append((d, pending[d]))
            del pending[d]

        if not pending:
            del self.pending_returns[ticker]

    def get_return_for_date(self, ticker: str, dt: date) -> float | None:
        """Look up a daily return — checks pending first, then history."""
        pending = self.pending_returns.get(ticker)
        if pending and dt in pending:
            return pending[dt]
        for d, v in self.return_history.get(ticker, []):
            if d == dt:
                return v
        return None

    def get_rolling_zscore(self, ticker: str, dt: date, current_return: float | None) -> float | None:
        """Compute z-score of *current_return* against history strictly before *dt*.

        Returns ``None`` when there are fewer than ``min_valid_days_momentum``
        prior observations.
        """
        if current_return is None:
            return None

        prior = [(d, v) for d, v in self.return_history.get(ticker, []) if d < dt]
        prior = prior[-self._config.momentum_window_days:]

        if len(prior) < self._config.min_valid_days_momentum:
            return None

        values = [v for _, v in prior]
        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        std = math.sqrt(variance)

        if std == 0:
            return 0.0

        return (current_return - mean) / std

    def get_history_length(self, ticker: str) -> int:
        """Number of committed returns for *ticker* (for testing)."""
        return len(self.return_history.get(ticker, []))

    def has_previous_price(self, ticker: str, dt: date) -> bool:
        """``True`` if a price exists for *ticker* on a date strictly before *dt*."""
        prices = self.price_history.get(ticker, {})
        return any(d < dt for d in prices)
