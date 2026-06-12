"""Layer 3 sentiment — Loughran-McDonald lexicon and daily z-score processor."""

import math
import re
from collections import deque
from datetime import date

from layers.layer3_config import CONFIG
from layers.lm_lexicon import POSITIVE as LM_POSITIVE, NEGATIVE as LM_NEGATIVE

# Merge LM lexicon with original hardcoded words for backward compatibility.
# Original words not in LM: surge, gain, rise, beat, up, positive (positive);
# fall, drop, miss, down, slump, bad, negative (negative).
_OLD_POSITIVE = {"surge", "gain", "rise", "beat", "up", "positive"}
_OLD_NEGATIVE = {"fall", "drop", "miss", "down", "slump", "bad", "negative"}

POSITIVE_WORDS = LM_POSITIVE | _OLD_POSITIVE
NEGATIVE_WORDS = LM_NEGATIVE | _OLD_NEGATIVE


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

