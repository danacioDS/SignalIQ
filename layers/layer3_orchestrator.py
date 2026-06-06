"""Layer 3 orchestrator — coordinates entity resolution, sentiment, and momentum."""

import re
import sys
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, str(Path(__file__).parent.parent))

from layers.layer3_config import CONFIG
from layers.layer3_entity import EntityResolver, normalize_headline
from layers.layer3_momentum import MomentumProcessor
from layers.layer3_sentiment import SentimentProcessor


HEADLINE_REQUIRED_KEYS = {"headline_text", "published_at", "ingested_at", "url_param"}
PRICE_REQUIRED_KEYS = {"ticker", "date", "adj_close"}


class TimeAligner:

    UTC_OFFSET_HOURS = 4

    @staticmethod
    def to_eastern(dt: datetime) -> datetime:
        return dt.replace(microsecond=0) - __import__("datetime").timedelta(
            hours=TimeAligner.UTC_OFFSET_HOURS
        )

    @staticmethod
    def get_trading_day(timestamp: datetime, cutoff_hour: int = 16) -> date:
        eastern = TimeAligner.to_eastern(timestamp)
        if eastern.hour < cutoff_hour:
            return eastern.date()
        return (eastern + __import__("datetime").timedelta(days=1)).date()


class Layer3Orchestrator:

    def __init__(self, config=CONFIG):
        self._config = config
        self._resolver = EntityResolver(config.min_alias_length)
        self._sentiment = SentimentProcessor(config)
        self._momentum = MomentumProcessor(config)
        self._aligner = TimeAligner()

        self._headline_buffer: dict[str, dict[date, list[float]]] = defaultdict(
            lambda: defaultdict(list)
        )
        self._last_finalized_date: date | None = None

    @staticmethod
    def validate_batch_input(headlines: list[dict], prices: list[dict]) -> None:
        for i, h in enumerate(headlines):
            missing = HEADLINE_REQUIRED_KEYS - set(h)
            if missing:
                raise ValueError(f"headlines[{i}] missing keys: {sorted(missing)}")

        for i, p in enumerate(prices):
            missing = PRICE_REQUIRED_KEYS - set(p)
            if missing:
                raise ValueError(f"prices[{i}] missing keys: {sorted(missing)}")

    def process_headline(
        self,
        headline_text: str,
        published_at: datetime | None,
        ingested_at: datetime,
        url_param: str | None = None,
    ) -> date:
        ts = published_at if published_at is not None else ingested_at
        trading_day = self._aligner.get_trading_day(ts, self._config.daily_cutoff_hour_et)

        norm = normalize_headline(headline_text)
        tickers = self._resolver.resolve(norm, url_param)

        if not tickers:
            tickers = ["__UNRESOLVED__"]

        for ticker in tickers:
            score = self._sentiment.score_headline(norm)
            self._headline_buffer[ticker][trading_day].append(score)

        return trading_day

    def process_price(self, ticker: str, dt: date, adj_close: float) -> float | None:
        return self._momentum.add_price(ticker, dt, adj_close)

    def finalize_day(self, dt: date, tickers: list[str] | None = None) -> dict:
        if not isinstance(dt, date):
            raise ValueError(f"dt must be a date object, got {type(dt).__name__}")

        if self._last_finalized_date is not None and dt <= self._last_finalized_date:
            raise ValueError(
                f"finalize_day called out of order: {dt} <= {self._last_finalized_date}"
            )

        if tickers is None:
            tickers = self._resolver.get_all_tickers()

        for ticker in tickers:
            self._momentum.commit_pending_returns(ticker, dt)

        result: dict = {}

        for ticker in tickers:
            daily_scores = self._headline_buffer[ticker].pop(dt, [])
            daily_raw = self._sentiment.aggregate_daily(daily_scores)
            sentiment_zscore = self._sentiment.get_rolling_zscore(ticker, dt, daily_raw)
            if daily_raw is not None:
                self._sentiment.add_to_history(ticker, dt, daily_raw)

            daily_return = self._momentum.get_return_for_date(ticker, dt)
            momentum_zscore = self._momentum.get_rolling_zscore(ticker, dt, daily_return)

            result[ticker] = {
                dt.isoformat(): {
                    "sentiment_zscore": sentiment_zscore,
                    "momentum_zscore": momentum_zscore,
                    "sentiment_raw": daily_raw,
                    "momentum_return": daily_return,
                }
            }

        self._headline_buffer.pop(dt, None)
        self._last_finalized_date = dt

        return result


if __name__ == "__main__":
    from dataclasses import replace

    cfg = replace(CONFIG, min_headlines_per_day=1)
    orch = Layer3Orchestrator(cfg)

    prices_aapl = [100.0 + i * 0.5 + (0.1 if i % 2 == 0 else 0.0) for i in range(12)]
    prices_msft = [200.0 + i * 0.3 + (0.1 if i % 2 == 0 else 0.0) for i in range(12)]

    orch.process_price("AAPL", date(2025, 12, 31), prices_aapl[0])
    orch.process_price("MSFT", date(2025, 12, 31), prices_msft[0])

    for day in range(1, 12):
        dt = date(2026, 1, day)

        orch.process_price("AAPL", dt, prices_aapl[day])
        orch.process_price("MSFT", dt, prices_msft[day])

        orch.process_headline(
            "strong profit growth for apple this quarter",
            datetime(2026, 1, day, 14, 0),
            datetime(2026, 1, day, 14, 5),
            url_param="AAPL",
        )
        orch.process_headline(
            "microsoft shows weak growth outlook",
            datetime(2026, 1, day, 14, 30),
            datetime(2026, 1, day, 14, 35),
            url_param="MSFT",
        )

        result = orch.finalize_day(dt)
        for ticker, data in result.items():
            inner = data[dt.isoformat()]
            print(
                f"  Day {day:2d}  {ticker:5s}  "
                f"sentiment_z={inner['sentiment_zscore']!s:>8s}  "
                f"momentum_z={inner['momentum_zscore']!s:>8s}  "
                f"return={inner['momentum_return']!s:>10s}"
            )

    print("\n  → First z-scores appear on Day 11 (10 prior observations)")
