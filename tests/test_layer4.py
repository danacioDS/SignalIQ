"""Integration test suite for SignalIQ Layer 4 (all sublayers)."""

import json
import os
from pathlib import Path

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from layers.layer4_measurement import (
    validate_input,
    calculate_ndi,
    calculate_5d_return,
    compute_measurements,
)
from layers.layer4_persistence import PersistenceTracker
from layers.layer4_classification import (
    boost_confidence_by_streak,
    calculate_confidence,
    calculate_price_pressure,
    get_ndi_trend,
    get_risk_level,
    get_attention_text,
)
from layers.layer4_orchestrator import (
    process_asset,
    process_batch,
    validate_batch_input,
    OUTPUT_FIELDS,
)

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


def _cleanup():
    p = Path("persistence_state.json")
    if p.exists():
        os.remove(p)


# ---------------------------------------------------------------------------
# TEST 1: Validity Gate
# ---------------------------------------------------------------------------
def test_validity_gate():
    print("\n=== TEST 1: Validity Gate ===")

    state, reason = validate_input(1.0, 0.5, [100.0] * 6)
    _check("Valid inputs → VALID", state, "VALID")
    _check("Valid inputs → reason None", reason, None)

    state, reason = validate_input(None, 0.5, [100.0] * 6)
    _check("None sentiment → INVALID_INPUT", state, "INVALID_INPUT")

    state, reason = validate_input(1.0, None, [100.0] * 6)
    _check("None momentum → INVALID_INPUT", state, "INVALID_INPUT")

    state, reason = validate_input(1.0, 0.5, [100.0] * 5)
    _check("5 prices → INSUFFICIENT_PRICE_HISTORY", state, "INSUFFICIENT_PRICE_HISTORY")
    _check("5 prices → reason mentions 5", reason, "need 6 prices, got 5")


# ---------------------------------------------------------------------------
# TEST 2: NDI Calculation
# ---------------------------------------------------------------------------
def test_ndi_calculation():
    print("\n=== TEST 2: NDI Calculation ===")

    ndi = calculate_ndi(2.0, 0.5)
    _check("sentiment=2.0, momentum=0.5 → ndi=1.5", ndi, 1.5)

    ndi = calculate_ndi(None, 0.5)
    _check("sentiment=None → ndi=None", ndi, None)

    ndi = calculate_ndi(2.0, None)
    _check("momentum=None → ndi=None", ndi, None)

    ndi = calculate_ndi(None, None)
    _check("both None → ndi=None", ndi, None)


# ---------------------------------------------------------------------------
# TEST 3: Persistence Streak (sequential, same tracker)
# ---------------------------------------------------------------------------
def test_persistence_streak():
    print("\n=== TEST 3: Persistence Streak ===")

    _cleanup()
    tracker = PersistenceTracker()

    # Day 1: ndi=1.6 → above threshold → streak=1 → WATCHING
    state = tracker.get_signal_state("TEST3", 1.6)
    _check("Day 1 signal_state", state, "WATCHING")

    # Day 2: ndi=1.7 → above threshold → streak=2 → ACTIVE
    state = tracker.get_signal_state("TEST3", 1.7)
    _check("Day 2 signal_state", state, "ACTIVE")

    # Day 3: ndi=0.5 → below threshold → streak=0 → INACTIVE
    state = tracker.get_signal_state("TEST3", 0.5)
    _check("Day 3 signal_state", state, "INACTIVE")

    # Day 4: ndi=1.6 → above threshold → streak=1 → WATCHING
    state = tracker.get_signal_state("TEST3", 1.6)
    _check("Day 4 signal_state", state, "WATCHING")


# ---------------------------------------------------------------------------
# TEST 4: Regime Classification
# ---------------------------------------------------------------------------
def test_regime_classification():
    print("\n=== TEST 4: Regime Classification ===")

    r = PersistenceTracker.get_regime(0.5)
    _check("ndi=0.5 → ALIGNED", r, "ALIGNED")

    r = PersistenceTracker.get_regime(-2.0)
    _check("ndi=-2.0 → ACCUMULATION_DIVERGENCE", r, "ACCUMULATION_DIVERGENCE")

    r = PersistenceTracker.get_regime(2.0)
    _check("ndi=2.0 → OVERHEATING_DIVERGENCE", r, "OVERHEATING_DIVERGENCE")

    r = PersistenceTracker.get_regime(None)
    _check("ndi=None → INSUFFICIENT_DATA", r, "INSUFFICIENT_DATA")


# ---------------------------------------------------------------------------
# TEST 5: Confidence (Inverted U)
# ---------------------------------------------------------------------------
def test_confidence():
    print("\n=== TEST 5: Confidence (Inverted U) ===")

    c = calculate_confidence(0.5)
    _check("ndi=0.5 → LOW", c, "LOW")

    c = calculate_confidence(1.5)
    _check("ndi=1.5 → HIGH", c, "HIGH")

    c = calculate_confidence(2.5)
    _check("ndi=2.5 → MEDIUM", c, "MEDIUM")

    c = calculate_confidence(None)
    _check("ndi=None → INSUFFICIENT_DATA", c, "INSUFFICIENT_DATA")


# ---------------------------------------------------------------------------
# TEST 6: Price Pressure
# ---------------------------------------------------------------------------
def test_price_pressure():
    print("\n=== TEST 6: Price Pressure ===")

    p = calculate_price_pressure(0.01)
    _check("return=0.01 → SUPPORTING", p, "SUPPORTING")

    p = calculate_price_pressure(0.002)
    _check("return=0.002 → NEUTRAL", p, "NEUTRAL")

    p = calculate_price_pressure(-0.01)
    _check("return=-0.01 → PRESSURING", p, "PRESSURING")

    p = calculate_price_pressure(None)
    _check("return=None → NEUTRAL", p, "NEUTRAL")


# ---------------------------------------------------------------------------
# TEST 7: Risk Level Escalation
# ---------------------------------------------------------------------------
def test_risk_level():
    print("\n=== TEST 7: Risk Level Escalation ===")

    r = get_risk_level("OVERHEATING_DIVERGENCE", "PRESSURING")
    _check("Overheating + PRESSURING → CRITICAL", r, "CRITICAL")

    r = get_risk_level("OVERHEATING_DIVERGENCE", "NEUTRAL")
    _check("Overheating + NEUTRAL → ELEVATED", r, "ELEVATED")

    r = get_risk_level("OVERHEATING_DIVERGENCE", "SUPPORTING")
    _check("Overheating + SUPPORTING → NORMAL", r, "NORMAL")

    r = get_risk_level("ACCUMULATION_DIVERGENCE", "PRESSURING")
    _check("Accumulation + PRESSURING → NORMAL", r, "NORMAL")

    r = get_risk_level("ACCUMULATION_DIVERGENCE", "SUPPORTING")
    _check("Accumulation + SUPPORTING → NORMAL", r, "NORMAL")

    r = get_risk_level("ALIGNED", "NEUTRAL")
    _check("Aligned + any → NORMAL", r, "NORMAL")


# ---------------------------------------------------------------------------
# TEST 8: Full Integration — 5 days of NVDA
# ---------------------------------------------------------------------------
def test_full_integration():
    print("\n=== TEST 8: Full Integration (NVDA, 5 days) ===")

    _cleanup()
    tracker = PersistenceTracker()

    days = [
        # (day_label, sentiment, momentum, prices_6, expected_checks)
        (
            "Day1",
            1.8, 0.2,
            [100.0, 100.0, 100.0, 100.0, 100.0, 101.0],  # +1%
            {"signal_state": "WATCHING", "regime": "OVERHEATING_DIVERGENCE"},
        ),
        (
            "Day2",
            1.9, 0.1,
            [100.0, 100.0, 100.0, 100.0, 100.0, 100.3],  # +0.3% → flat
            {"signal_state": "ACTIVE", "risk_level": "ELEVATED"},
        ),
        (
            "Day3",
            2.0, 0.0,
            [100.0, 100.0, 100.0, 100.0, 100.0, 99.2],   # -0.8% → falling
            {"signal_state": "ACTIVE", "risk_level": "CRITICAL"},
        ),
        (
            "Day4",
            0.5, 0.3,
            [100.0, 100.0, 100.0, 100.0, 100.0, 100.5],  # +0.5% → flat (boundary)
            {"signal_state": "INACTIVE", "regime": "ALIGNED"},
        ),
        (
            "Day5",
            1.7, 0.2,
            [100.0, 100.0, 100.0, 100.0, 100.0, 100.1],  # +0.1% → flat
            {"signal_state": "WATCHING"},
        ),
    ]

    for label, sentiment, momentum, prices, checks in days:
        result = process_asset("NVDA", sentiment, momentum, prices, tracker, "2026-06-02")
        for key, expected in checks.items():
            _check(f"{label} {key}", result[key], expected)


# ---------------------------------------------------------------------------
# TEST 9: JSON Output Format
# ---------------------------------------------------------------------------
def test_json_output():
    print("\n=== TEST 9: JSON Output Format ===")

    _cleanup()
    tracker = PersistenceTracker()
    prices = [100.0, 101.0, 102.0, 103.0, 104.0, 105.0]
    result = process_asset("FMT", 1.0, 0.5, prices, tracker, "2026-06-02")

    # Exactly 12 fields, no extras
    keys = sorted(result.keys())
    expected_keys = sorted(OUTPUT_FIELDS)
    _check("Exactly 12 output fields", keys, expected_keys)

    # JSON serializable
    try:
        dumped = json.dumps(result)
        _check("JSON serializable", True, True)
    except (TypeError, ValueError) as e:
        _check(f"JSON serializable (raised {e})", False, True)

    # All values are the right types
    _check("ticker is str", isinstance(result["ticker"], str), True)
    _check("date is str", isinstance(result["date"], str), True)
    _check("regime is str", isinstance(result["regime"], str), True)
    _check("signal_state is str", isinstance(result["signal_state"], str), True)
    _check("confidence is str", isinstance(result["confidence"], str), True)
    _check("price_modifier is str", isinstance(result["price_modifier"], str), True)
    _check("persistence_days is int", isinstance(result["persistence_days"], int), True)
    _check("risk_level is str", isinstance(result["risk_level"], str), True)
    _check("attention is str", isinstance(result["attention"], str), True)
    _check("ndi is float or None", result["ndi"] is None or isinstance(result["ndi"], float), True)
    _check("ndi_delta is float or None", result["ndi_delta"] is None or isinstance(result["ndi_delta"], float), True)
    _check("ndi_trend is str", isinstance(result["ndi_trend"], str), True)

    # Also test invalid path
    invalid_result = process_asset("BAD", None, 0.5, prices, tracker, "2026-06-02")
    keys_inv = sorted(invalid_result.keys())
    _check("Invalid output also has 12 fields", keys_inv, expected_keys)
    _check("Invalid ndi is None", invalid_result["ndi"], None)
    _check("Invalid ndi_delta is None", invalid_result["ndi_delta"], None)
    _check("Invalid ndi_trend is INSUFFICIENT_DATA", invalid_result["ndi_trend"], "INSUFFICIENT_DATA")


# ---------------------------------------------------------------------------
# TEST 10: Edge Cases
# ---------------------------------------------------------------------------
def test_edge_cases():
    print("\n=== TEST 10: Edge Cases ===")

    _cleanup()
    tracker = PersistenceTracker()

    # ndi exactly 1.5 → threshold met (>= includes equality)
    streak = tracker.update("EDGE", 1.5)
    _check("ndi=1.5 exactly → streak incremented", streak, 1)

    # ndi exactly -1.5 → threshold met
    streak = tracker.update("EDGE2", -1.5)
    _check("ndi=-1.5 exactly → streak incremented", streak, 1)

    # price_return exactly 0.005 → NEUTRAL (<= includes equality)
    p = calculate_price_pressure(0.005)
    _check("return=0.005 exactly → NEUTRAL", p, "NEUTRAL")

    # Empty price_history → INSUFFICIENT_PRICE_HISTORY
    state, reason = validate_input(1.0, 0.5, [])
    _check("Empty price_history → INSUFFICIENT_PRICE_HISTORY", state, "INSUFFICIENT_PRICE_HISTORY")
    _check("Empty price_history → reason says 0", reason, "need 6 prices, got 0")


# ---------------------------------------------------------------------------
# TEST 11: Confidence Boost (streak >= 3)
# ---------------------------------------------------------------------------
def test_confidence_boost():
    print("\n=== TEST 11: Confidence Boost (streak >= 3) ===")

    c = boost_confidence_by_streak("LOW", 0)
    _check("streak=0, LOW → LOW", c, "LOW")

    c = boost_confidence_by_streak("LOW", 2)
    _check("streak=2, LOW → LOW (no boost)", c, "LOW")

    c = boost_confidence_by_streak("LOW", 3)
    _check("streak=3, LOW → MEDIUM", c, "MEDIUM")

    c = boost_confidence_by_streak("MEDIUM", 3)
    _check("streak=3, MEDIUM → HIGH", c, "HIGH")

    c = boost_confidence_by_streak("HIGH", 3)
    _check("streak=3, HIGH → HIGH (ceiling)", c, "HIGH")

    c = boost_confidence_by_streak("INSUFFICIENT_DATA", 5)
    _check("streak=5, INSUFFICIENT_DATA stays", c, "INSUFFICIENT_DATA")


# ---------------------------------------------------------------------------
# TEST 12: NDI Delta
# ---------------------------------------------------------------------------
def test_ndi_delta():
    print("\n=== TEST 12: NDI Delta ===")

    _cleanup()
    tracker = PersistenceTracker()
    prices = [100.0, 101.0, 102.0, 103.0, 104.0, 105.0]

    # Day 1: no previous NDI → ndi_delta = None
    r1 = process_asset("NDIDELTA", 2.0, 0.5, prices, tracker, "2026-06-01")
    _check("Day 1 ndi_delta is None", r1["ndi_delta"], None)

    # Day 2: previous NDI was 1.5 → ndi_delta = 2.0 - 1.5 = 0.5
    r2 = process_asset("NDIDELTA", 2.5, 0.5, prices, tracker, "2026-06-02")
    _check("Day 2 ndi_delta is float", isinstance(r2["ndi_delta"], float), True)
    _check("Day 2 ndi_delta = 0.5", r2["ndi_delta"], 0.5)


# ---------------------------------------------------------------------------
# TEST 13: Batch Input Validation
# ---------------------------------------------------------------------------
def test_batch_validation():
    print("\n=== TEST 13: Batch Input Validation ===")

    prices = [100.0, 101.0, 102.0, 103.0, 104.0, 105.0]

    # Valid batch
    valid = {"AAPL": {"sentiment_zscore": 1.0, "momentum_zscore": 0.5, "price_history": prices}}
    errs = validate_batch_input(valid)
    _check("Valid batch → no errors", errs, [])

    # Missing momentum
    no_mom = {"AAPL": {"sentiment_zscore": 1.0, "price_history": prices}}
    errs = validate_batch_input(no_mom)
    _check("Missing momentum → 1 error", len(errs), 1)
    _check("Missing momentum mentions key", "momentum_zscore" in errs[0], True)

    # Missing all keys
    empty = {"AAPL": {}}
    errs = validate_batch_input(empty)
    _check("Empty dict → 1 error", len(errs), 1)

    # Not a dict
    bad_val = {"AAPL": "not_a_dict"}
    errs = validate_batch_input(bad_val)
    _check("Not a dict → 1 error", len(errs), 1)
    _check("Not a dict mentions problem", "not a dict" in errs[0], True)

    # process_batch raises on bad input
    _cleanup()
    tracker = PersistenceTracker()
    try:
        process_batch({"BAD": {"sentiment_zscore": 1.0}}, tracker, "2026-06-02")
        _check("process_batch raises ValueError", False, True)
    except ValueError:
        _check("process_batch raises ValueError", True, True)


# ---------------------------------------------------------------------------
# TEST 14: NDI Trend
# ---------------------------------------------------------------------------
def test_ndi_trend():
    print("\n=== TEST 14: NDI Trend ===")

    t = get_ndi_trend(None)
    _check("ndi_delta=None → INSUFFICIENT_DATA", t, "INSUFFICIENT_DATA")

    t = get_ndi_trend(0.0)
    _check("ndi_delta=0.0 → STABLE", t, "STABLE")

    t = get_ndi_trend(0.2)
    _check("ndi_delta=0.2 → STABLE (below threshold)", t, "STABLE")

    t = get_ndi_trend(0.3)
    _check("ndi_delta=0.3 → STABLE (at threshold boundary)", t, "STABLE")

    t = get_ndi_trend(0.31)
    _check("ndi_delta=0.31 → ACCELERATING", t, "ACCELERATING")

    t = get_ndi_trend(-0.31)
    _check("ndi_delta=-0.31 → DECELERATING", t, "DECELERATING")


# ---------------------------------------------------------------------------
# TEST 15: Stale Persistence (gap detection)
# ---------------------------------------------------------------------------
def test_stale_persistence():
    print("\n=== TEST 15: Stale Persistence ===")

    _cleanup()
    tracker = PersistenceTracker()

    # Day 1: normal update on Monday
    s = tracker.get_signal_state("STALE", 1.6, "2026-06-01")
    _check("Mon signal_state", s, "WATCHING")
    _check("Mon streak", tracker.get_streak("STALE"), 1)

    # Day 2: normal update on Tuesday
    s = tracker.get_signal_state("STALE", 1.7, "2026-06-02")
    _check("Tue signal_state", s, "ACTIVE")
    _check("Tue streak", tracker.get_streak("STALE"), 2)

    # Gap: no data for Wed/Thu/Fri. Next run on Monday (5 day gap).
    # Streak should reset to 0 before applying today's threshold check.
    s = tracker.get_signal_state("STALE", 1.8, "2026-06-08")
    _check("Mon after gap signal_state", s, "WATCHING")
    _check("Mon after gap streak", tracker.get_streak("STALE"), 1)

    # No date_string → stale detection skipped (backward compat)
    s = tracker.get_signal_state("STALE", 1.9)
    _check("No date signal_state", s, "ACTIVE")
    _check("No date streak (no reset)", tracker.get_streak("STALE"), 2)

    # --- Boundary: Fri→Mon gap = 3, should NOT reset ---
    _cleanup()
    t2 = PersistenceTracker()
    t2.get_signal_state("BOUNDARY", 1.6, "2026-05-29")  # Fri
    _check("Fri streak before weekend", t2.get_streak("BOUNDARY"), 1)
    t2.get_signal_state("BOUNDARY", 1.7, "2026-06-01")  # Mon, gap=3
    _check("Mon after weekend streak (gap=3, no reset)", t2.get_streak("BOUNDARY"), 2)

    # --- Boundary: Fri→Tue gap = 4, SHOULD reset ---
    _cleanup()
    t3 = PersistenceTracker()
    t3.get_signal_state("BOUNDARY2", 1.6, "2026-05-29")  # Fri
    _check("Fri streak before long gap", t3.get_streak("BOUNDARY2"), 1)
    t3.get_signal_state("BOUNDARY2", 1.7, "2026-06-02")  # Tue, gap=4
    _check("Tue after long gap streak (gap=4, reset)", t3.get_streak("BOUNDARY2"), 1)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    global _FAILURES
    _FAILURES = 0

    # Clean slate
    _cleanup()

    test_validity_gate()
    test_ndi_calculation()
    test_persistence_streak()
    test_regime_classification()
    test_confidence()
    test_price_pressure()
    test_risk_level()
    test_full_integration()
    test_json_output()
    test_edge_cases()
    test_confidence_boost()
    test_ndi_delta()
    test_batch_validation()
    test_ndi_trend()
    test_stale_persistence()

    # Final cleanup
    _cleanup()

    print()
    if _FAILURES == 0:
        print("ALL TESTS PASSED")
    else:
        print(f"SOME TESTS FAILED ({_FAILURES} failure(s))")


if __name__ == "__main__":
    main()
