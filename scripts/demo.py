"""SignalIQ demo — end-to-end synthetic run with no external dependencies."""

import json
from datetime import date, datetime, timedelta
from pathlib import Path

from layers.layer3_config import CONFIG
from layers.layer3_orchestrator import Layer3Orchestrator
from layers.layer4_orchestrator import PersistenceTracker, process_batch
from synthetic.data_generator import generate

TICKERS = ["NVDA", "AAPL", "MSFT"]
DAYS = 20
PERSISTENCE_FILE = "persistence_state.json"


def _get_price_history_list(
    momentum_processor, ticker: str, today: date, window: int = 20
) -> list[float]:
    prices = momentum_processor.price_history.get(ticker, {})
    sorted_dates = sorted(d for d in prices if d <= today)
    sorted_dates = sorted_dates[-window:]
    return [prices[d] for d in sorted_dates]


def main():
    print("=" * 60)
    print("SignalIQ Demo — Synthetic Data, No External Dependencies")
    print("=" * 60)

    # Remove any prior persistence state
    # p = Path(PERSISTENCE_FILE)
    # if p.exists():
    #     p.unlink()

    from dataclasses import replace
    cfg = replace(CONFIG, min_headlines_per_day=1)
    orch = Layer3Orchestrator(cfg)
    persistence = PersistenceTracker()

    # Generate synthetic data (higher drift/vol to create regime changes)
    print(f"\nGenerating {DAYS} days of synthetic data for {TICKERS}...")
    all_data = {}
    for ticker in TICKERS:
        all_data[ticker] = generate(ticker, days=DAYS, drift=0.15, volatility=0.35)

    # Seed initial prices (day 0) so day 1 has a prior
    base_date = date(2025, 12, 31)
    for ticker in TICKERS:
        data = all_data[ticker]
        first_date = min(data.keys())
        first_price = data[first_date]["prices"][0]
        orch.process_price(ticker, base_date, first_price)

    # Process days in chronological order
    all_results = []
    dates_sorted = sorted(all_data[TICKERS[0]].keys())

    for dt in dates_sorted:
        # Add prices for this day
        for ticker in TICKERS:
            prices = all_data[ticker][dt]["prices"]
            current_price = prices[-1]
            orch.process_price(ticker, dt, current_price)

        # Add headlines for this day
        for ticker in TICKERS:
            for headline_text in all_data[ticker][dt]["headlines"]:
                orch.process_headline(
                    headline_text,
                    datetime(dt.year, dt.month, dt.day, 12, 0),
                    datetime(dt.year, dt.month, dt.day, 12, 5),
                    url_param=ticker,
                )

        # Finalize the day
        l3_output = orch.finalize_day(dt, tickers=TICKERS)

        # Build Layer 4 input
        l4_input = {}
        for ticker in TICKERS:
            inner = l3_output[ticker][dt.isoformat()]
            price_list = _get_price_history_list(
                orch._momentum, ticker, dt
            )
            l4_input[ticker] = {
                "sentiment_zscore": inner["sentiment_zscore"],
                "momentum_zscore": inner["momentum_zscore"],
                "price_history": price_list,
            }

        results = process_batch(l4_input, persistence, dt.isoformat())
        all_results.append(results)

    # Output final signals
    print(f"\n=== FINAL SIGNALS (last day: {dates_sorted[-1]}) ===")
    final = all_results[-1]
    print(json.dumps(final, indent=2))

    # Summary
    total_signals = sum(
        1 for day_results in all_results for r in day_results if r["ndi"] is not None
    )
    total_active = sum(
        1 for day_results in all_results for r in day_results
        if r["signal_state"] == "ACTIVE" and r["ndi"] is not None
    )

    print(f"\n=== SUMMARY ===")
    print(f"  Days processed:        {len(dates_sorted)}")
    print(f"  Tickers:               {TICKERS}")
    print(f"  Total NDI signals:     {total_signals}")
    print(f"  ACTIVE signals:        {total_active}")
    print(f"  Persistence file:      {PERSISTENCE_FILE}")
    print(f"  External deps:         None (stdlib only)")
    print(f"\nDone. Run `python demo.py` again for identical output (seed=42).")


if __name__ == "__main__":
    main()
