"""Layer 3 sentiment — inline word lists and daily z-score processor."""

import math
import re
import sys
from collections import deque
from datetime import date
from pathlib import Path

if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, str(Path(__file__).parent.parent))

from layers.layer3_config import CONFIG

POSITIVE_WORDS = {"surge", "gain", "rise", "beat", "up", "growth", "strong",
                  "profit", "good", "upgrade", "positive", "outperform"}
NEGATIVE_WORDS = {"fall", "drop", "miss", "decline", "down", "weak", "slump",
                  "loss", "bad", "downgrade", "negative", "underperform"}


def polarity(text: str) -> float:
    tokens = re.findall(r"\b[a-z]+\b", text.lower())
    if not tokens:
        return 0.0
    pos = sum(1 for t in tokens if t in POSITIVE_WORDS)
    neg = sum(1 for t in tokens if t in NEGATIVE_WORDS)
    return (pos - neg) / len(tokens)


class SentimentProcessor:

    def __init__(self, config=CONFIG):
        self._config = config
        self._history: dict[str, deque] = {}

    def score_headline(self, headline_text: str) -> float:
        return polarity(headline_text)

    def aggregate_daily(self, scores: list[float]) -> float | None:
        if len(scores) < self._config.min_headlines_per_day:
            return None
        return sum(scores) / len(scores)

    def add_to_history(self, ticker: str, dt: date, sentiment_raw: float | None) -> None:
        if sentiment_raw is None:
            return
        if ticker not in self._history:
            self._history[ticker] = deque(maxlen=self._config.max_history_days)
        self._history[ticker].append((dt, sentiment_raw))

    def get_rolling_zscore(self, ticker: str, dt: date, current_raw: float | None) -> float | None:
        if current_raw is None:
            return None

        prior = [(d, v) for d, v in self._history.get(ticker, []) if d < dt]
        prior = prior[-self._config.sentiment_window_days:]

        if len(prior) < self._config.min_valid_days_sentiment:
            return None

        values = [v for _, v in prior]
        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        std = math.sqrt(variance)

        if std == 0:
            return 0.0

        return (current_raw - mean) / std

    def get_history_length(self, ticker: str) -> int:
        return len(self._history.get(ticker, []))


if __name__ == "__main__":
    processor = SentimentProcessor()

    print("=== SentimentProcessor Demo: FIRST Z-SCORE ON DAY 11 ===\n")

    headline = "strong profit growth offsets weak quarterly loss"
    raw = polarity(headline)
    print(f"  headline: {headline}")
    print(f"  raw polarity: {raw:+.4f}\n")

    for day in range(1, 12):
        dt = date(2026, 1, day)
        daily_raw = 0.1 + 0.02 * day + (0.05 if day % 2 == 0 else -0.05)

        processor.add_to_history("AAPL", dt, daily_raw)
        z = processor.get_rolling_zscore("AAPL", dt, daily_raw)
        hist_len = processor.get_history_length("AAPL")

        print(f"  Day {day:2d}  | raw={daily_raw:+.4f}  | hist={hist_len:2d} prior  | z-score={z}")
        print(f"           | (history count available for z-score: {sum(1 for d,_ in processor._history.get('AAPL',[]) if d < dt)})")

    print("\n  → First z-score appears on Day 11 (10 prior observations)")
