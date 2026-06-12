"""Sublayer 4B: Signal State — persistence tracker and regime classification."""

import json
from datetime import datetime
from pathlib import Path

SIGNAL_STATE = ["INACTIVE", "WATCHING", "ACTIVE"]
REGIME = ["ALIGNED", "ACCUMULATION_DIVERGENCE", "OVERHEATING_DIVERGENCE", "INSUFFICIENT_DATA"]
MAX_GAP_DAYS = 3  # max calendar gap before streak resets (covers Fri→Mon as 1 trading day)


class PersistenceTracker:
    """Tracks consecutive-day threshold breaches per ticker.

    State is persisted to a JSON file (default ``persistence_state.json``)
    so that streaks survive process restarts (e.g. a daily cron job).

    Call :meth:`save` explicitly after all updates are done, rather than
    writing to disk on every single call.
    """

    def __init__(self, state_file: Path = Path("persistence_state.json")):
        self._state_file = state_file
        self._data: dict[str, dict] = {}
        if state_file.exists():
            with state_file.open() as f:
                self._data = json.load(f)

    def save(self):
        """Persist current state to disk."""
        with self._state_file.open("w") as f:
            json.dump(self._data, f, indent=2)

    def get_streak(self, ticker: str) -> int:
        """Return the current streak for *ticker* (0 if unknown)."""
        return self._data.get(ticker, {}).get("streak", 0)

    def get_last_ndi(self, ticker: str) -> float | None:
        """Return the previous NDI for *ticker* (None if unknown)."""
        return self._data.get(ticker, {}).get("last_ndi")

    def update(self, ticker: str, ndi: float | None, threshold: float = 1.5, date_string: str | None = None) -> int:
        """Update the streak for *ticker*.

        Rules
        -----
        * ``ndi is None`` → streak = 0
        * ``|ndi| >= threshold`` → streak += 1
        * otherwise → streak = 0

        Stale detection
        ---------------
        If *date_string* is provided and the stored ``last_updated`` differs
        by more than ``MAX_GAP_DAYS`` calendar days, the streak is reset to 0
        first.  This prevents a gap (weekend, holiday, data outage) from
        silently extending a real streak.
        """
        ticker_data = self._data.setdefault(ticker, {"streak": 0, "last_ndi": None, "last_updated": None})

        if date_string is not None and ticker_data.get("last_updated") is not None:
            try:
                prev = datetime.strptime(ticker_data["last_updated"], "%Y-%m-%d").date()
                curr = datetime.strptime(date_string, "%Y-%m-%d").date()
                if (curr - prev).days > MAX_GAP_DAYS:
                    ticker_data["streak"] = 0
            except ValueError:
                pass

        if ndi is None:
            ticker_data["streak"] = 0
        elif abs(ndi) >= threshold:
            ticker_data["streak"] += 1
        else:
            ticker_data["streak"] = 0

        ticker_data["last_ndi"] = ndi
        if date_string is not None:
            ticker_data["last_updated"] = date_string
        return ticker_data["streak"]

    def get_signal_state(self, ticker: str, ndi: float | None, date_string: str | None = None) -> str:
        """Return the signal state for *ticker* after updating persistence."""
        streak = self.update(ticker, ndi, date_string=date_string)
        if streak >= 2:
            return "ACTIVE"
        if streak == 1:
            return "WATCHING"
        return "INACTIVE"

    @staticmethod
    def get_regime(ndi: float | None, threshold: float = 1.5) -> str:
        """Classify *ndi* into a regime without touching persistence."""
        if ndi is None:
            return "INSUFFICIENT_DATA"
        if abs(ndi) < threshold:
            return "ALIGNED"
        if ndi <= -threshold:
            return "ACCUMULATION_DIVERGENCE"
        return "OVERHEATING_DIVERGENCE"

    @property
    def state(self) -> dict:
        """Expose raw state for inspection (read-only view intended)."""
        return self._data
