"""Synthetic data generator for demo — prices and headlines, no external deps."""

import math
import random
from datetime import date, timedelta

POSITIVE_WORDS = ["surge", "gain", "rise", "beat", "up", "growth", "strong",
                  "profit", "good", "upgrade", "positive", "outperform"]
NEGATIVE_WORDS = ["fall", "drop", "miss", "decline", "down", "weak", "slump",
                  "loss", "bad", "downgrade", "negative", "underperform"]

STARTING_PRICES = {
    "NVDA": 100.0,
    "AAPL": 150.0,
    "MSFT": 300.0,
}

BASE_DATE = date(2026, 1, 1)


def _random_headline(return_val: float, flip_sentiment: bool = False) -> str:
    is_positive = return_val >= 0
    if flip_sentiment:
        is_positive = not is_positive

    if is_positive:
        w1 = random.choice(POSITIVE_WORDS)
        w2 = random.choice(POSITIVE_WORDS)
        return f"{w1} {w2} in quarterly report"
    else:
        w1 = random.choice(NEGATIVE_WORDS)
        w2 = random.choice(NEGATIVE_WORDS)
        return f"{w1} {w2} in quarterly report"


random.seed(42)


def generate(ticker: str, days: int = 20, drift: float = 0.05, volatility: float = 0.20) -> dict:
    start_price = STARTING_PRICES.get(ticker, 100.0)

    dt = BASE_DATE
    prices: list[float] = []
    dates: list[date] = []
    result: dict[date, dict] = {}

    price = start_price
    for i in range(days):
        daily_drift = drift / 252
        daily_vol = volatility / math.sqrt(252)

        # Every 15th day: 2x volatility spike
        vol = daily_vol * 2 if (i + 1) % 15 == 0 else daily_vol

        raw_return = random.gauss(0, 1)
        daily_return = daily_drift + vol * raw_return
        price *= (1 + daily_return)

        prices.append(price)
        dates.append(dt)

        # Headlines: 1-3 per day, sentiment aligned 70% of the time
        flip = (i + 1) % 9 == 0
        num_headlines = random.randint(1, 3)
        headlines: list[str] = []
        for _ in range(num_headlines):
            if random.random() < 0.7:
                headlines.append(_random_headline(daily_return, flip_sentiment=flip))
            else:
                headlines.append(_random_headline(-daily_return, flip_sentiment=flip))

        result[dt] = {
            "prices": [round(p, 4) for p in prices],
            "headlines": headlines,
        }

        dt += timedelta(days=1)

    return result
