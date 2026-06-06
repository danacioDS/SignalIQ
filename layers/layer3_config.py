"""Layer 3 configuration — frozen dataclass with all MVP parameters."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Layer3Config:
    """Frozen configuration for Layer 3 (NLP Intelligence).

    All parameters are set at import time via the singleton ``CONFIG``.
    """

    min_headlines_per_day: int = 3
    sentiment_window_days: int = 20
    min_valid_days_sentiment: int = 10
    momentum_window_days: int = 20
    min_valid_days_momentum: int = 10
    daily_cutoff_hour_et: int = 16
    min_alias_length: int = 3
    max_history_days: int = 30


CONFIG = Layer3Config()
