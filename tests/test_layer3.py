"""Integration test suite for SignalIQ Layer 3 (all sublayers)."""

import json
import os
import sys
from collections import deque
from datetime import date, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from layers.layer3_config import CONFIG
from layers.layer3_entity import EntityResolver, normalize_headline
from layers.layer3_momentum import MomentumProcessor
from layers.layer3_orchestrator import (
    HEADLINE_REQUIRED_KEYS,
    PRICE_REQUIRED_KEYS,
    Layer3Orchestrator,
    TimeAligner,
)
from layers.layer3_sentiment import SentimentProcessor, polarity

_FAILURES = 0


def _check(label, actual, expected):
    global _FAILURES
    if actual != expected:
        print(f"  FAIL: {label}")
        print(f"    expected: {expected!r}")
        print(f"    actual:   {actual!r}")
        _FAILURES += 1
    else:
        print(f"  PASS: {label}")


def _approx(a, b, eps=0.01):
    return abs(a - b) < eps


# ---------------------------------------------------------------------------
# TEST 1: Configuration Loading
# ---------------------------------------------------------------------------
def test_config_loading():
    print("\n=== TEST 1: Configuration Loading ===")

    _check("min_headlines_per_day default", CONFIG.min_headlines_per_day, 3)
    _check("sentiment_window_days default", CONFIG.sentiment_window_days, 20)
    _check("min_valid_days_sentiment default", CONFIG.min_valid_days_sentiment, 10)
    _check("momentum_window_days default", CONFIG.momentum_window_days, 20)
    _check("min_valid_days_momentum default", CONFIG.min_valid_days_momentum, 10)
    _check("daily_cutoff_hour_et default", CONFIG.daily_cutoff_hour_et, 16)
    _check("min_alias_length default", CONFIG.min_alias_length, 3)
    _check("max_history_days default", CONFIG.max_history_days, 30)
    _check("min_valid_days_sentiment == 10", CONFIG.min_valid_days_sentiment, 10)
    _check("min_valid_days_momentum == 10", CONFIG.min_valid_days_momentum, 10)


# ---------------------------------------------------------------------------
# TEST 2: Entity Resolution with Proper Word Boundaries
# ---------------------------------------------------------------------------
def test_entity_resolution():
    print("\n=== TEST 2: Entity Resolution with Proper Word Boundaries ===")

    resolver = EntityResolver(min_alias_length=3)

    # URL param resolution
    _check("url exact match", resolver.resolve_by_url_param("NVDA"), "NVDA")
    _check("url no match", resolver.resolve_by_url_param("UNKNOWN"), None)

    # Hardcoded alias: nvidia → NVDA
    matched = resolver.resolve_by_alias("nvidia beats earnings")
    _check("nvidia matches 'nvidia beats earnings'", matched, {"NVDA"})

    # Hardcoded alias: apple inc → AAPL
    matched = resolver.resolve_by_alias("apple inc announces new product")
    _check("apple inc matches 'apple inc announces'", matched, {"AAPL"})

    # Short alias "apple" matches; longer non-match word does not
    matched = resolver.resolve_by_alias("apples stock rises")
    _check("apples does NOT match 'apple' alias", matched, set())

    matched = resolver.resolve_by_alias("nvda123")
    _check("nvda123 does NOT match 'nvda'", matched, set())

    # Multiple tickers
    matched = resolver.resolve_by_alias("apple inc and microsoft partnership")
    _check("apple inc + microsoft matches both", matched, {"AAPL", "MSFT"})

    # Short alias (< 3 chars) filtered
    matched = resolver.resolve_by_alias("msft reports earnings")
    _check("msft (len=4) matches 'msft reports'", matched, {"MSFT"})

    # Two-phase resolve
    result = resolver.resolve("nvidia and microsoft", url_param="NVDA")
    _check("resolve with url_param returns [NVDA]", result, ["NVDA"])

    result = resolver.resolve("nvidia and microsoft")
    _check("resolve without url_param returns both", set(result), {"NVDA", "MSFT"})


# ---------------------------------------------------------------------------
# TEST 3: Sentiment Polarity Function
# ---------------------------------------------------------------------------
def test_sentiment_polarity():
    print("\n=== TEST 3: Sentiment Polarity Function ===")

    p = polarity("strong profit growth")
    _check("positive words → polarity > 0", p > 0, True)

    p = polarity("weak loss decline")
    _check("negative words → polarity < 0", p < 0, True)

    p = polarity("the company reported results")
    _check("neutral words → polarity = 0.0", p, 0.0)

    p = polarity("")
    _check("empty string → polarity = 0.0", p, 0.0)


# ---------------------------------------------------------------------------
# TEST 4: Sentiment Processor
# ---------------------------------------------------------------------------
def test_sentiment_processor():
    print("\n=== TEST 4: Sentiment Processor ===")

    spinner = SentimentProcessor()

    # score_headline
    s = spinner.score_headline("strong profit growth")
    _check("score_headline positive", 0 < s <= 1.0, True)

    s = spinner.score_headline("weak loss decline")
    _check("score_headline negative", -1.0 <= s < 0, True)

    s = spinner.score_headline("the company reported results")
    _check("score_headline neutral = 0.0", s, 0.0)

    # aggregate_daily
    agg = spinner.aggregate_daily([0.5, 0.6, 0.7])
    _check("aggregate 3 scores mean=0.6", agg, 0.6)

    agg = spinner.aggregate_daily([0.5])
    _check("aggregate 1 score returns None", agg, None)

    # Rolling z-score: 10 PRIOR days required
    for day in range(1, 11):
        dt = date(2026, 2, day)
        raw = 0.2 + 0.01 * day
        spinner.add_to_history("TEST4", dt, raw)
        z = spinner.get_rolling_zscore("TEST4", dt, raw)
        _check(f"Day {day} z-score is None ({day-1} prior)", z, None)

    dt11 = date(2026, 2, 11)
    raw11 = 0.2 + 0.01 * 11
    z = spinner.get_rolling_zscore("TEST4", dt11, raw11)
    _check("Day 11 z-score is not None (10 prior)", z is not None, True)

    hist_before = spinner.get_history_length("TEST4")
    _check("history length before add_to_history", hist_before, 10)
    spinner.add_to_history("TEST4", dt11, raw11)
    hist_after = spinner.get_history_length("TEST4")
    _check("history length after add_to_history", hist_after, 11)


# ---------------------------------------------------------------------------
# TEST 5: Momentum Processor
# ---------------------------------------------------------------------------
def test_momentum_processor():
    print("\n=== TEST 5: Momentum Processor ===")

    mp = MomentumProcessor()

    r = mp.calculate_daily_return(105.0, 100.0)
    _check("return 105/100 = 0.05", r, 0.05)

    r = mp.calculate_daily_return(100.0, 0.0)
    _check("return div by 0 = 0.0", r, 0.0)

    r1 = mp.add_price("TEST5", date(2026, 3, 1), 100.0)
    _check("first price return None", r1, None)
    _check("pending_returns empty after first", len(mp.pending_returns.get("TEST5", {})), 0)

    r2 = mp.add_price("TEST5", date(2026, 3, 2), 105.0)
    _check("second price return 0.05", r2, 0.05)
    _check("pending_returns has day 2", mp.pending_returns["TEST5"][date(2026, 3, 2)], 0.05)
    _check("return_history empty before commit", mp.get_history_length("TEST5"), 0)

    mp.commit_pending_returns("TEST5", date(2026, 3, 2))
    _check("return_history has 1 after commit", mp.get_history_length("TEST5"), 1)
    _check("pending_returns empty after commit", mp.pending_returns.get("TEST5"), None)

    ret = mp.get_return_for_date("TEST5", date(2026, 3, 2))
    _check("get_return_for_date day 2", ret, 0.05)

    ret = mp.get_return_for_date("TEST5", date(2026, 3, 1))
    _check("get_return_for_date day 1 (no return)", ret, None)

    # Rolling z-score: 10 PRIOR days required
    dt2 = date(2026, 3, 2)
    mp.commit_pending_returns("TEST5", dt2)

    for day in range(3, 13):
        dt = date(2026, 3, day)
        price = 100.0 + day * 0.5
        daily_return = mp.add_price("TEST5", dt, price)
        mp.commit_pending_returns("TEST5", dt)
        prior_count = day - 2
        z = mp.get_rolling_zscore("TEST5", dt, daily_return)
        if prior_count < 10:
            _check(f"Day {day} z-score None ({prior_count} prior)", z, None)
        else:
            _check(f"Day {day} z-score not None ({prior_count} prior)", z is not None, True)


# ---------------------------------------------------------------------------
# TEST 6: Time Aligner
# ---------------------------------------------------------------------------
def test_time_aligner():
    print("\n=== TEST 6: Time Aligner ===")

    ts = datetime(2026, 6, 2, 11, 59)
    td = TimeAligner.get_trading_day(ts)
    _check("11:59 UTC → same day", td, date(2026, 6, 2))

    ts = datetime(2026, 6, 2, 20, 1)
    td = TimeAligner.get_trading_day(ts)
    _check("20:01 UTC → next day", td, date(2026, 6, 3))

    ts = datetime(2026, 6, 2, 20, 0)
    td = TimeAligner.get_trading_day(ts)
    _check("20:00 UTC → next day (>= 16)", td, date(2026, 6, 3))

    ingested = datetime(2026, 6, 2, 14, 0)
    td = TimeAligner.get_trading_day(ingested)
    _check("14:00 UTC → same day (fallback)", td, date(2026, 6, 2))


# ---------------------------------------------------------------------------
# TEST 7: Orchestrator Headline Processing
# ---------------------------------------------------------------------------
def test_orchestrator_headlines():
    print("\n=== TEST 7: Orchestrator Headline Processing ===")

    from dataclasses import replace

    cfg = replace(CONFIG, min_headlines_per_day=1)
    orch = Layer3Orchestrator(cfg)

    td = orch.process_headline(
        "good news for apple inc",
        datetime(2026, 4, 1, 14, 0),
        datetime(2026, 4, 1, 14, 5),
        url_param="AAPL",
    )
    _check("trading_day from headline", td, date(2026, 4, 1))

    buf = orch._headline_buffer.get("AAPL", {}).get(date(2026, 4, 1), [])
    _check("buffer has 1 score for AAPL", len(buf), 1)

    td2 = orch.process_headline(
        "nvidia reports good results",
        datetime(2026, 4, 1, 15, 0),
        datetime(2026, 4, 1, 15, 5),
    )
    _check("trading_day from alias headline", td2, date(2026, 4, 1))

    buf2 = orch._headline_buffer.get("NVDA", {}).get(date(2026, 4, 1), [])
    _check("buffer has 1 score for NVDA", len(buf2), 1)

    td3 = orch.process_headline(
        "some random stock news",
        datetime(2026, 4, 1, 16, 0),
        datetime(2026, 4, 1, 16, 5),
    )
    _check("unresolved headline still gets trading day", isinstance(td3, date), True)


# ---------------------------------------------------------------------------
# TEST 8: Orchestrator Price Processing
# ---------------------------------------------------------------------------
def test_orchestrator_prices():
    print("\n=== TEST 8: Orchestrator Price Processing ===")

    from dataclasses import replace

    cfg = replace(CONFIG)
    orch = Layer3Orchestrator(cfg)

    r1 = orch.process_price("NVDA", date(2026, 5, 1), 100.0)
    _check("first price return None", r1, None)
    _check("price stored", orch._momentum.price_history["NVDA"][date(2026, 5, 1)], 100.0)
    _check("pending empty", len(orch._momentum.pending_returns.get("NVDA", {})), 0)

    r2 = orch.process_price("NVDA", date(2026, 5, 2), 105.0)
    _check("second price return 0.05", r2, 0.05)
    _check("pending has return", orch._momentum.pending_returns["NVDA"][date(2026, 5, 2)], 0.05)
    _check("history still empty", orch._momentum.get_history_length("NVDA"), 0)


# ---------------------------------------------------------------------------
# TEST 9: Orchestrator Daily Finalization with 10 PRIOR Days
# ---------------------------------------------------------------------------
def test_orchestrator_finalization():
    print("\n=== TEST 9: Orchestrator Daily Finalization ===")

    from dataclasses import replace

    cfg = replace(CONFIG, min_headlines_per_day=1)
    orch = Layer3Orchestrator(cfg)

    orch.process_price("NVDA", date(2025, 12, 31), 100.0)

    for day in range(1, 12):
        dt = date(2026, 6, day)
        orch.process_price("NVDA", dt, 100.0 + day * 0.5 + (0.1 if day % 2 == 0 else 0.0))
        orch.process_headline(
            "strong profit and good growth" if day % 2 == 0 else "weak loss and bad results",
            datetime(2026, 6, day, 14, 0),
            datetime(2026, 6, day, 14, 5),
            url_param="NVDA",
        )
        result = orch.finalize_day(dt)

        inner = result["NVDA"][dt.isoformat()]

        if day < 11:
            _check(f"Day {day} sentiment_z is None", inner["sentiment_zscore"], None)
            _check(f"Day {day} momentum_z is None", inner["momentum_zscore"], None)
        else:
            _check(f"Day {day} sentiment_z not None", inner["sentiment_zscore"] is not None, True)
            _check(f"Day {day} momentum_z not None", inner["momentum_zscore"] is not None, True)
            _check("output key is ISO string", dt.isoformat() in result["NVDA"], True)

    try:
        orch.finalize_day(date(2026, 5, 1))
        _check("out-of-order raises ValueError", False, True)
    except ValueError:
        _check("out-of-order raises ValueError", True, True)


# ---------------------------------------------------------------------------
# TEST 10: Full Pipeline Determinism
# ---------------------------------------------------------------------------
def test_full_pipeline_determinism():
    print("\n=== TEST 10: Full Pipeline Determinism ===")

    from dataclasses import replace

    cfg = replace(CONFIG, min_headlines_per_day=1)

    def run_pipeline():
        orch = Layer3Orchestrator(cfg)
        orch.process_price("AAPL", date(2025, 12, 31), 100.0)
        orch.process_price("MSFT", date(2025, 12, 31), 200.0)

        results = []
        for day in range(1, 21):
            dt = date(2026, 7, day)
            orch.process_price("AAPL", dt, 100.0 + day * 0.5)
            orch.process_price("MSFT", dt, 200.0 + day * 0.3)

            headline = "good profit growth" if day % 2 == 0 else "bad weak decline"
            orch.process_headline(headline, datetime(2026, 7, day, 14, 0), datetime(2026, 7, day, 14, 5))
            result = orch.finalize_day(dt)
            results.append(result)
        return results

    r1 = run_pipeline()
    r2 = run_pipeline()

    _check("same pipeline output (run 1 vs run 2)", r1, r2)


# ---------------------------------------------------------------------------
# TEST 11: Edge Cases
# ---------------------------------------------------------------------------
def test_edge_cases():
    print("\n=== TEST 11: Edge Cases ===")

    from dataclasses import replace

    cfg = replace(CONFIG, min_headlines_per_day=1)
    orch = Layer3Orchestrator(cfg)

    td = orch.process_headline(
        "good news",
        None,
        datetime(2026, 8, 1, 14, 0),
        url_param="NVDA",
    )
    _check("published_at=None uses ingested_at", td, date(2026, 8, 1))

    td = orch.process_headline(
        "apple inc reports results",
        datetime(2026, 8, 1, 15, 0),
        datetime(2026, 8, 1, 15, 5),
    )
    _check("no url_param, alias match still resolves", td, date(2026, 8, 1))


# ---------------------------------------------------------------------------
# TEST 12: Batch Input Validation
# ---------------------------------------------------------------------------
def test_batch_input_validation():
    print("\n=== TEST 12: Batch Input Validation ===")

    valid_h = {"headline_text": "text", "published_at": None, "ingested_at": datetime(2026, 1, 1, 12, 0), "url_param": None}
    valid_p = {"ticker": "AAPL", "date": date(2026, 1, 1), "adj_close": 100.0}

    Layer3Orchestrator.validate_batch_input([valid_h], [valid_p])
    _check("valid inputs pass", True, True)

    try:
        Layer3Orchestrator.validate_batch_input(
            [{"published_at": None, "ingested_at": datetime(2026, 1, 1, 12, 0), "url_param": None}],
            [valid_p],
        )
        _check("missing headline_text raises ValueError", False, True)
    except ValueError:
        _check("missing headline_text raises ValueError", True, True)

    try:
        Layer3Orchestrator.validate_batch_input(
            [{"headline_text": "text", "ingested_at": datetime(2026, 1, 1, 12, 0), "url_param": None}],
            [valid_p],
        )
        _check("missing published_at key raises ValueError", False, True)
    except ValueError:
        _check("missing published_at key raises ValueError", True, True)

    h_with_none = {**valid_h, "published_at": None}
    Layer3Orchestrator.validate_batch_input([h_with_none], [valid_p])
    _check("published_at=None passes validation", True, True)

    try:
        Layer3Orchestrator.validate_batch_input(
            [valid_h],
            [{"date": date(2026, 1, 1), "adj_close": 100.0}],
        )
        _check("missing ticker raises ValueError", False, True)
    except ValueError:
        _check("missing ticker raises ValueError", True, True)


# ---------------------------------------------------------------------------
# TEST 13: Look-Ahead Bias Prevention (Critical)
# ---------------------------------------------------------------------------
def test_lookahead_bias_prevention():
    print("\n=== TEST 13: Look-Ahead Bias Prevention ===")

    mp = MomentumProcessor()

    for day in range(1, 11):
        dt = date(2026, 9, day)
        mp.add_price("BIAS", dt, 100.0 + day * 0.5)
        mp.commit_pending_returns("BIAS", dt)

    dt10 = date(2026, 9, 10)
    hist_before = mp.get_history_length("BIAS")
    _check("history has 9 returns before day 10 z-score", hist_before, 9)

    dt11 = date(2026, 9, 11)
    r11 = mp.add_price("BIAS", dt11, 105.5)

    z_before = mp.get_rolling_zscore("BIAS", dt11, r11)
    _check("z-score before commit is None (< 10 prior)", z_before, None)

    mp.commit_pending_returns("BIAS", dt11)
    hist_after = mp.get_history_length("BIAS")
    _check("history has 10 returns after commit", hist_after, 10)

    z11 = mp.get_rolling_zscore("BIAS", dt11, r11)
    _check("day 11 z-score still None (only 9 prior)", z11, None)

    dt12 = date(2026, 9, 12)
    r12 = mp.add_price("BIAS", dt12, 106.0)
    mp.commit_pending_returns("BIAS", dt12)
    z12 = mp.get_rolling_zscore("BIAS", dt12, r12)
    _check("day 12 z-score IS computed (10 prior returns: days 2-11)", z12 is not None, True)


# ---------------------------------------------------------------------------
# TEST 14: Chronological Order Enforcement
# ---------------------------------------------------------------------------
def test_chronological_order():
    print("\n=== TEST 14: Chronological Order Enforcement ===")

    from dataclasses import replace

    cfg = replace(CONFIG)
    orch = Layer3Orchestrator(cfg)

    orch.process_price("AAPL", date(2025, 12, 31), 100.0)
    orch.process_price("AAPL", date(2026, 6, 1), 101.0)
    orch.process_price("AAPL", date(2026, 6, 2), 102.0)

    orch.finalize_day(date(2026, 6, 2))
    _check("first finalize (day 2) succeeds", True, True)

    try:
        orch.finalize_day(date(2026, 6, 1))
        _check("earlier date raises ValueError", False, True)
    except ValueError as e:
        _check("earlier date raises ValueError", True, True)
        _check("error mentions chronological", "chronological" in str(e).lower() or "out of order" in str(e).lower(), True)


# ---------------------------------------------------------------------------
# TEST 15: Date Handling Consistency
# ---------------------------------------------------------------------------
def test_date_handling():
    print("\n=== TEST 15: Date Handling Consistency ===")

    d = date(2026, 10, 15)
    _check("date object created", isinstance(d, date), True)
    _check("not datetime", type(d).__name__, "date")

    iso = d.isoformat()
    _check("isoformat returns string", isinstance(iso, str), True)
    _check("isoformat correct", iso, "2026-10-15")

    ts = datetime(2026, 10, 15, 14, 0)
    td = TimeAligner.get_trading_day(ts)
    _check("get_trading_day returns date", isinstance(td, date), True)
    _check("get_trading_day not datetime", type(td).__name__, "date")

    from dataclasses import replace

    cfg = replace(CONFIG, min_headlines_per_day=1)
    orch = Layer3Orchestrator(cfg)

    orch.process_price("AAPL", date(2025, 12, 31), 100.0)
    orch.process_price("AAPL", date(2026, 10, 15), 101.0)
    orch.process_headline("good news", datetime(2026, 10, 15, 14, 0), datetime(2026, 10, 15, 14, 5), url_param="AAPL")
    result = orch.finalize_day(date(2026, 10, 15))

    for ticker, data in result.items():
        for key in data:
            _check("output key is ISO string", isinstance(key, str), True)
            _check("output key format YYYY-MM-DD", len(key), 10)


# ---------------------------------------------------------------------------
# TEST 16: Alias Word Boundary Edge Cases
# ---------------------------------------------------------------------------
def test_alias_word_boundaries():
    print("\n=== TEST 16: Alias Word Boundary Edge Cases ===")

    resolver = EntityResolver(min_alias_length=3)

    matched = resolver.resolve_by_alias("nvidia reports earnings")
    _check("'nvidia reports earnings' → NVDA", matched, {"NVDA"})

    matched = resolver.resolve_by_alias("nvidia123")
    _check("'nvidia123' does NOT match", matched, set())

    matched = resolver.resolve_by_alias("nvidia")
    _check("'nvidia' exact match", matched, {"NVDA"})

    matched = resolver.resolve_by_alias("apple inc announces new product")
    _check("'apple inc. announces' → AAPL", matched, {"AAPL"})

    matched = resolver.resolve_by_alias("applesauce")
    _check("'applesauce' does NOT match 'apple'", matched, set())

    matched = resolver.resolve_by_alias("apple inc")
    _check("'apple inc' matches exactly", matched, {"AAPL"})

    matched = resolver.resolve_by_alias("nvda")
    _check("'nvda' matches NVDA", matched, {"NVDA"})

    matched = resolver.resolve_by_alias("nvda123")
    _check("'nvda123' does NOT match 'nvda'", matched, set())


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    global _FAILURES
    _FAILURES = 0

    test_config_loading()
    test_entity_resolution()
    test_sentiment_polarity()
    test_sentiment_processor()
    test_momentum_processor()
    test_time_aligner()
    test_orchestrator_headlines()
    test_orchestrator_prices()
    test_orchestrator_finalization()
    test_full_pipeline_determinism()
    test_edge_cases()
    test_batch_input_validation()
    test_lookahead_bias_prevention()
    test_chronological_order()
    test_date_handling()
    test_alias_word_boundaries()

    print()
    if _FAILURES == 0:
        print("ALL TESTS PASSED")
    else:
        print(f"SOME TESTS FAILED ({_FAILURES} failure(s))")


if __name__ == "__main__":
    main()
