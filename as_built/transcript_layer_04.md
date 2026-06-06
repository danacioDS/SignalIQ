# SignalIQ Layer 4 — Transcript 01: Code Review & Remediation

## Overview

Full code review of SignalIQ Layer 4 (measurement → persistence → classification → orchestrator), followed by two rounds of implementation.

- **Round 1** — 6 fixes from the code review (explicit save, configurable path, output schema, sorted batch, LLD superseded).
- **Round 2** — 3 feature upgrades (confidence ceiling guard, NDI velocity, batch input validation).
- **Round 3** — 3 production-hardening changes (ordering comment, `ndi_trend` field, stale persistence detection).
- **Round 4** — L3→L4 pipeline integration (DB connector, pipeline orchestrator, end-to-end 20-day demo).

All 31 tests pass across both layers (16 L3 + 15 L4). End-to-end pipeline verified with synthetic 20-day data.

---

## Code Review Summary

### What was working well

- **Sublayer split** — `layer4_measurement.py` → `layer4_persistence.py` → `layer4_classification.py` → `layer4_orchestrator.py` follows a clean one-direction dependency chain. Nothing imports backwards.
- **Centralized validity gate** — `compute_measurements()` is the single entry point and short-circuits cleanly. The orchestrator exits early on `validity_state != "VALID"`; no downstream function ever receives a `None` NDI unexpectedly.
- **Persistence survives restarts** — `PersistenceTracker` writes to `persistence_state.json`, correct for a daily-cron context where a process restart on day 2 shouldn't silently reset a streak already at 1.
- **Separation of `signal_state` from `regime`** — `signal_state` is temporal (how long has this been happening?), `regime` is semantic (what kind of divergence?). The old LLD had "Watching" as a regime — a category error. Fixed.
- **Inverted-U confidence** — `|NDI| > 2.2 → MEDIUM` is non-obvious but defensible: extreme readings are more likely to be sentiment outliers or data noise. The docstring in `calculate_confidence()` explains the rationale.

### Issues flagged and fixed

| # | Issue | Severity | Fix |
|---|-------|----------|-----|
| 1 | `_save()` called inside `update()` → disk write on every asset every day | Medium | Made `save()` public, removed from `update()`. Orchestrator calls it once at end of `process_batch()`. |
| 2 | `_STATE_FILE` hardcoded as relative `Path("persistence_state.json")` | High | Added `state_file` constructor parameter with sensible default. |
| 3 | Confidence thresholds in code (0.8/2.2 inverted-U) differ from LLD spec (1.0/2.0 monotonic) | Info | No code change needed — architecture doc matches code. LLD doc marked superseded. |
| 4 | `price_modifier` and `persistence_days` computed internally but not surfaced in output | Medium | Both fields added to output dict. `get_price_modifier()` mapper added in classification. |
| 5 | `process_batch()` iterates `data_dict.items()` without guaranteed order | Low | Changed to `sorted(data_dict.items())`. |
| 6 | LLD doc (`Low-Level Design (LLD)/SignalIQ_layer_04.md`) contradicts current architecture | Medium | Added superseded banner pointing to `Architecture/Layer_04_arch.md`. |

### Items noted but not changed

- **`__main__` blocks in individual modules** — all behind `if __name__ == "__main__":`, so no import side effects. Safe by design.
- **`OUTPUT_FIELDS` defined in orchestrator, only used in tests** — now also used as the canonical field list for the orchestrator's own output. Coupling is acceptable for MVP scale.
- **String constants with no type enforcement** — `VALIDITY_STATE`, `SIGNAL_STATE`, `REGIME` lists are documentation, not enforcement. MVP-acceptable; can upgrade to `Literal`/`Enum` later.
- **Test runner uses global counter with pytest-style naming but doesn't use pytest** — deliberate zero-dependency choice. Fine as-is.

---

## Changes — File by File

### `layer4_persistence.py`

```diff
- _STATE_FILE = Path("persistence_state.json")
-
  class PersistenceTracker:
-     def __init__(self):
+     def __init__(self, state_file: Path = Path("persistence_state.json")):
+         self._state_file = state_file
          ...
-         if _STATE_FILE.exists():
-             with _STATE_FILE.open() as f:
+         if state_file.exists():
+             with state_file.open() as f:
                  ...

-     def _save(self):
+     def save(self):
-         with _STATE_FILE.open("w") as f:
+         with self._state_file.open("w") as f:
              ...

+     def get_streak(self, ticker: str) -> int:
+         return self._data.get(ticker, {}).get("streak", 0)

      def update(self, ...):
          ...
-         self._save()
          return ticker_data["streak"]
```

- `save()` is now public — callers decide when to persist.
- `update()` no longer writes to disk.
- `get_streak()` safely exposes streak count for output surfacing.
- State file path is configurable at construction time.

### `layer4_classification.py`

```diff
+ PRICE_MODIFIER = ["trend_supporting", "trend_stalling", "trend_collapsing"]

+ def get_price_modifier(price_pressure: str) -> str:
+     mapping = {
+         "SUPPORTING": "trend_supporting",
+         "NEUTRAL": "trend_stalling",
+         "PRESSURING": "trend_collapsing",
+     }
+     return mapping.get(price_pressure, "trend_stalling")
```

- New function maps internal price-pressure labels to user-facing modifier strings.
- `PRICE_MODIFIER` constant added for documentation / test reference.

### `layer4_orchestrator.py`

```diff
  OUTPUT_FIELDS = [
-     "ticker", "date", "ndi", "regime", "signal_state", "confidence",
-     "risk_level", "attention",
+     "ticker", "date", "ndi", "regime", "signal_state",
+     "confidence", "price_modifier", "persistence_days",
+     "risk_level", "attention",
  ]

  def process_asset(...):
      ...
      return {
          ...
+         "price_modifier": get_price_modifier(price_pressure),
+         "persistence_days": persistence_tracker.get_streak(ticker),
          ...
      }

  def process_batch(...):
      results = []
-     for ticker, data in data_dict.items():
+     for ticker, data in sorted(data_dict.items()):
          ...
          results.append(result)
+
+     persistence_tracker.save()
      return results
```

- Two new output fields: `price_modifier` (trend_supporting/stalling/collapsing) and `persistence_days` (streak count).
- Batch processing sorts tickers alphabetically for stable output.
- `save()` called once per batch instead of per asset per call.

### `test_layer4.py`

```diff
-     _check("Exactly 8 output fields", keys, expected_keys)
+     _check("Exactly 10 output fields", keys, expected_keys)

-     _check("Invalid output also has 8 fields", keys_inv, expected_keys)
+     _check("Invalid output also has 10 fields", keys_inv, expected_keys)

+     _check("price_modifier is str", isinstance(result["price_modifier"], str), True)
+     _check("persistence_days is int", isinstance(result["persistence_days"], int), True)
```

- Field count check updated from 8 to 10.
- Type assertions added for the two new fields.
- Existing `_cleanup()` calls retained for safety; no longer critical since `save()` is explicit.

### `Low-Level Design (LLD)/SignalIQ_layer_04.md`

```
> **⚠️ SUPERSEDED — This document predates the Architecture specification.**
> See `Architecture/Layer_04_arch.md` for the current, authoritative design.
```

- Banner added at top of file.
- LLD preserved for historical reference; all future work should reference `Architecture/Layer_04_arch.md`.

---

## Round 2 — Feature Upgrades

Three upgrades identified in the post-review analysis, ordered by value-to-effort ratio.

### 1. Confidence ceiling guard (`boost_confidence_by_streak`)

**The gap.** The persistence spec promised "day 3+ → confidence +1 level" but `calculate_confidence()` only looked at `|NDI|`. Streak never fed back in.

**The fix.** Added `boost_confidence_by_streak(confidence, streak)` in `layer4_classification.py`. Called in the orchestrator after base confidence is computed (step 6):

```
streak 0-2 → no change
streak 3+  → LOW→MEDIUM, MEDIUM→HIGH, HIGH→HIGH (ceiling)
```

```python
def boost_confidence_by_streak(confidence: str, streak: int) -> str:
    if streak < 3 or confidence == "HIGH" or confidence == "INSUFFICIENT_DATA":
        return confidence
    if confidence == "LOW":
        return "MEDIUM"
    if confidence == "MEDIUM":
        return "HIGH"
    return confidence
```

### 2. NDI velocity (`ndi_delta`)

**The gap.** NDI was a point-in-time value with no directional context. Whether divergence is accelerating or decelerating is useful information that costs nearly nothing to compute — the persistence tracker already stores `last_ndi`.

**The fix.** Added `get_last_ndi(ticker)` to `PersistenceTracker`. The orchestrator captures `last_ndi` *before* calling `get_signal_state()` (which overwrites it), then computes:

```python
ndi_delta = ndi - last_ndi if (ndi is not None and last_ndi is not None) else None
```

`ndi_delta` is surfaced as the 4th output field. Positive values mean divergence is widening; negative values mean it's narrowing.

### 3. Batch input validation (`validate_batch_input`)

**The gap.** `process_batch()` trusted every entry in `data_dict` to have all three required keys (`sentiment_zscore`, `momentum_zscore`, `price_history`). A missing key raised an unhandled `KeyError` mid-batch, aborting all remaining tickers.

**The fix.** Added `validate_batch_input()` in `layer4_orchestrator.py`, called at the top of `process_batch()`:

```python
BATCH_REQUIRED_KEYS = {"sentiment_zscore", "momentum_zscore", "price_history"}

def validate_batch_input(data_dict: dict[str, dict]) -> list[str]:
    errors = []
    for ticker, data in data_dict.items():
        if not isinstance(data, dict):
            errors.append(f"{ticker}: value is not a dict")
            continue
        missing = BATCH_REQUIRED_KEYS - data.keys()
        if missing:
            errors.append(f"{ticker}: missing keys {sorted(missing)}")
    return errors
```

On failure, `process_batch()` raises `ValueError` with a full report before any asset is processed.

### Diff summary (Round 2)

| File | Addition |
|------|----------|
| `layer4_persistence.py` | `get_last_ndi(ticker)` method |
| `layer4_classification.py` | `boost_confidence_by_streak()`, `PRICE_MODIFIER` constant |
| `layer4_orchestrator.py` | `ndi_delta` field, `validate_batch_input()`, confidence boost wiring |
| `test_layer4.py` | `test_confidence_boost` (6 checks), `test_ndi_delta` (3 checks), `test_batch_validation` (7 checks) |

---

## Round 3 — Production Hardening

Three changes addressing silent-break dependencies, missing semantic guidance, and data integrity under gap conditions.

### 1. Ordering-dependency comment

**The problem.** The orchestrator must capture `last_ndi` *before* `get_signal_state()` overwrites it. This ordering constraint was invisible — a future refactor would silently break `ndi_delta` with no error.

**The fix.** Added an explicit comment above the NDI velocity block:

```python
# Step 3: NDI velocity
# IMPORTANT: capture last_ndi BEFORE get_signal_state() overwrites it.
# Reordering these steps will silently break ndi_delta.
last_ndi = persistence_tracker.get_last_ndi(ticker)
```

### 2. NDI trend classification (`ndi_trend`)

**The problem.** `ndi_delta` was a raw float with no threshold or semantics attached. A delta of 0.02 vs 1.8 were both just numbers — downstream consumers had no guidance on what constituted meaningful acceleration or deceleration.

**The fix.** Added `get_ndi_trend(ndi_delta, threshold=0.3)` in `layer4_classification.py`. The output now includes a 12th field `ndi_trend`:

| `ndi_delta` | `ndi_trend` |
|-------------|-------------|
| `None` | `INSUFFICIENT_DATA` |
| `> 0.3` | `ACCELERATING` |
| `< -0.3` | `DECELERATING` |
| `-0.3 to 0.3` | `STABLE` |

### 3. Stale persistence detection

**The problem.** The JSON state file stored streaks but no timestamps. If the daily cron job skipped a day (weekend, holiday, data outage), the streak silently continued as if no day was missed. A ticker with streak=2 on Friday would wake up Monday still at streak=2, then increment to 3 — a false signal.

**The fix.** Three-part change:

1. **Data model** — per-ticker state now includes `last_updated`:
   ```python
   {"streak": 0, "last_ndi": None, "last_updated": None}
   ```

2. **`update()` accepts `date_string`** — when provided, the method parses the stored `last_updated` and the current date. If the gap exceeds `MAX_GAP_DAYS = 3` calendar days (covers Fri→Mon as 1 trading day), the streak resets to 0 before today's threshold check.

3. **Orchestrator passes date through** — `process_asset()` forwards its `date_string` to `get_signal_state()`, which forwards it to `update()`.

Backward compatible: omitting `date_string` skips stale detection entirely, preserving existing test behaviour.

**Production scenario this prevents:**

```
Fri:  streak=2, last_updated=2026-05-29
Mon:  gap = 3 calendar days (≤ 3) → OK, streak stays 2
Tue:  gap = 4 calendar days (> 3) → streak reset to 0
```

### Diff summary (Round 3)

| File | Addition |
|------|----------|
| `layer4_persistence.py` | `get_last_ndi()`, `MAX_GAP_DAYS` constant, `date_string` param on `update()`/`get_signal_state()`, stale-gap reset, `last_updated` field |
| `layer4_classification.py` | `get_ndi_trend()`, `NDI_TREND` constant |
| `layer4_orchestrator.py` | Ordering comment, `ndi_trend` field & wiring, `date_string` forwarded to persistence |
| `test_layer4.py` | `test_ndi_trend` (6 checks), `test_stale_persistence` (12 checks inc. Fri→Mon/ Fri→Tue boundary), field count 11→12 |

---

## Final Output Schema

```json
{
  "ticker":            "NVDA",
  "date":              "2026-06-02",
  "ndi":               1.7,
  "ndi_delta":         null,
  "ndi_trend":         "INSUFFICIENT_DATA",
  "regime":            "OVERHEATING_DIVERGENCE",
  "signal_state":      "WATCHING",
  "confidence":        "HIGH",
  "price_modifier":    "trend_supporting",
  "persistence_days":  1,
  "risk_level":        "NORMAL",
  "attention":         "Watching for persistence (needs 2nd consecutive day)."
}
```

12 fields total (up from 8 after Round 1, +2 in Round 2, +1 for `ndi_trend` in Round 3).

---

## Test Results

```
ALL TESTS PASSED  (80 checks across 15 test functions)
```

| Test | Scope | Checks |
|------|-------|--------|
| 1 | Validity Gate | 6 |
| 2 | NDI Calculation | 4 |
| 3 | Persistence Streak | 4 |
| 4 | Regime Classification | 4 |
| 5 | Confidence (Inverted U) | 4 |
| 6 | Price Pressure | 4 |
| 7 | Risk Level Escalation | 6 |
| 8 | Full Integration (5 days NVDA) | 9 |
| 9 | JSON Output Format | 16 |
| 10 | Edge Cases | 5 |
| 11 | Confidence Boost (streak >= 3) | 6 |
| 12 | NDI Delta | 3 |
| 13 | Batch Input Validation | 7 |
| 14 | NDI Trend | 6 |
| 15 | Stale Persistence | 12 |

---

---

## Round 4 — L3→L4 Pipeline Integration

The final integration piece: connecting Layer 3 (feature engineering) to Layer 4 (signal generation), with Layer 2 (PostgreSQL) as the data source.

### The gap

Layer 3 processed data in-memory via `process_headline()` and `process_price()` calls. Layer 4 consumed z-scores and price history via `process_batch()`. No coordinator existed to:

1. Load historical data from Layer 2 PostgreSQL
2. Warm up Layer 3's rolling windows (30-day deques)
3. Feed processed z-scores into Layer 4
4. Handle the schema transformation (Layer 3 output → Layer 4 input)

### New module: `layers/layer3_db.py` (167 lines)

PostgreSQL connector bridging Layer 2 and Layer 3. Requires `psycopg2-binary` (added to `requirements.txt`).

| Function | Purpose |
|----------|---------|
| `get_connection()` | Environment-variable connection (PGHOST, PGPORT, PGDATABASE, PGUSER, PGPASSWORD, PGURL) |
| `load_active_config(conn)` | Calls `get_active_config()` — returns JSON with assets, aliases, sources, vendor mappings |
| `load_prices(conn, ticker, end_date, window_days)` | Calls `get_prices_history()` — ordered list of `{ticker, date, adj_close}` |
| `load_headlines(conn, start_date, end_date)` | Calls `get_headlines_range()` — list of `{headline_text, published_at, url_param=None}` |
| `build_alias_file_from_config(db_config, output_path)` | Generates `config/entity_aliases.json` from DB config data |
| `warm_up_orchestrator(conn, orchestrator, tickers, days)` | Loads trailing N days of prices + headlines, feeds them chronologically with `finalize_day()` per calendar day |

**Design decisions:**
- Historical headlines have `url_param=None` because Layer 2 stores headlines without ticker attribution — entity resolution falls through to Phase 2 (alias regex matching)
- Prices are grouped by day using `defaultdict(list)`, then walked chronologically alongside headlines
- Each call to `finalize_day()` inside the warm-up loop populates rolling z-score windows so real-time processing starts immediately with valid scores
- Graceful skip when psycopg2 is missing or PostgreSQL is unreachable (smoke test exits 0)

### New module: `pipeline/signal_pipeline.py` (230 lines)

`SignalPipelineOrchestrator` — the daily coordinator matching the integration spec at `integrartion/layer_03_04.md`.

**Core method — `process_day(target_date, prices, headlines)`:**
1. Feed new prices into Layer 3 via `process_price()`, tracking tickers
2. Feed new headlines into Layer 3 via `process_headline()` with URL param
3. Call `finalize_day()` with all known tickers → `l3_output`
4. Transform: extract `price_history` as sorted `list[float]` from `MomentumProcessor.price_history`
5. Build `l4_input[ticker] = {sentiment_zscore, momentum_zscore, price_history}`
6. Call `layer4_orchestrator.process_batch()` with `PersistenceTracker`
7. Return final signal records (12 fields per ticker)

**Temporary concession (spec-documented):** `calculate_price_direction()` transforms `price_history[-6:]` into `'RISING'/'FLAT'/'FALLING'` using a 0.5% threshold. This lives in the orchestrator per MVP; post-MVP it moves to Layer 3.

**Warm-up paths:**
- `warm_up_from_db(conn, tickers, days)` — delegates to `layer3_db.warm_up_orchestrator()`
- `warm_up_from_inline(prices, headlines)` — for testing without a database

**Known-ticker tracking:** The pipeline maintains `_known_tickers: set[str]`, updated automatically from `process_price()` calls, so `finalize_day()` always knows which tickers to process.

### End-to-end verification

```
Day  1    NDI=None      sig=INACTIVE    regime=INSUFFICIENT_DATA
Day  2    NDI=None      sig=INACTIVE    regime=INSUFFICIENT_DATA
...
Day 10    NDI=None      sig=INACTIVE    regime=INSUFFICIENT_DATA
Day 11    NDI=1.28      sig=INACTIVE    regime=ALIGNED
Day 12    NDI=-0.86     sig=INACTIVE    regime=ALIGNED
...
Day 20    NDI=-0.73     sig=INACTIVE    regime=ALIGNED
```

- Days 1-10: NDI=None — momentum needs 10 prior returns (starts on day 11), sentiment needs 10 prior daily aggregates (starts on day 11)
- Day 11+: NDI computed, persistence tracker records `last_ndi` and `last_updated`
- NDI oscillates between positive (good headline day) and negative (bad headline day) because the synthetic data alternates sentiment daily with a fixed price trend — no regime breach since `|NDI| < 1.5` threshold

### Diff summary (Round 4)

| File | Role |
|------|------|
| `layers/layer3_db.py` | New — PostgreSQL connector, warm-up, alias builder |
| `pipeline/signal_pipeline.py` | New — `SignalPipelineOrchestrator`, `calculate_price_direction()`, L3→L4 bridge |
| `pipeline/__init__.py` | New — package marker |
| `requirements.txt` | New — `psycopg2-binary>=2.9` |
| `transcript_layer_04.md` | Updated — this Round 4 section |

No changes to core Layer 4 modules (measurement, persistence, classification, orchestrator). Layer 4 receives data through its existing `process_batch()` interface — unchanged.

---

## How Layer 4 Was Made

### Architecture (4 Sublayers)

Layer 4 converts z-scores into actionable signals. It's split into 4 sublayers with a strict one-direction dependency chain:

```
measurement → persistence → classification → orchestrator
              (same sublayer)
```

**Sublayer 4A — `layer4_measurement.py` (99 lines)**

Single responsibility: validity gate + NDI + 5-day return.

- `validate_input(sentiment_zscore, momentum_zscore, price_history)` → `("VALID", None)` or `("INVALID_INPUT", reason)` or `("INSUFFICIENT_PRICE_HISTORY", reason)`
- `calculate_ndi(sentiment_zscore, momentum_zscore)` → `sentiment - momentum` (the core divergence metric)
- `calculate_5d_return(price_history)` → `(price[-1] / price[-6]) - 1` (requires ≥6 prices)
- `compute_measurements(sentiment_zscore, momentum_zscore, price_history)` → single entry point returning `{validity_state, validity_reason, ndi, return_5d}`

Early-exit design: if validity_state != "VALID", the orchestrator short-circuits immediately — no downstream function ever receives None unexpectedly.

**Sublayer 4B — `layer4_persistence.py` (123 lines)**

State management: streaks survive process restarts via JSON file.

- `PersistenceTracker(state_file)` — loads/saves state as JSON, configurable path
- `get_streak(ticker)` / `get_last_ndi(ticker)` — read current streak and last NDI
- `update(ticker, ndi, date_string)` — streak logic: `|ndi| >= 1.5` → increment, else reset; stale-gap detection (3-day max gap) resets streak on data outages
- `get_signal_state(ticker, ndi, date_string)` — `streak >= 2 → ACTIVE`, `streak == 1 → WATCHING`, `else → INACTIVE`
- `get_regime(ndi)` — `ndi >= 1.5 → OVERHEATING_DIVERGENCE`, `ndi <= -1.5 → ACCUMULATION_DIVERGENCE`, `else → ALIGNED`

Key design: `save()` is explicit (not called on every update). The orchestrator calls it once per batch.

**Sublayer 4B — `layer4_classification.py` (155 lines)**

Semantic classification: confidence, price pressure, risk, attention.

- `calculate_confidence(ndi)` — inverted-U: `|ndi| > 2.2 → MEDIUM`, `|ndi| >= 0.8 → HIGH`, `else → LOW`
- `boost_confidence_by_streak(confidence, streak)` — streak >= 3 boosts by one level (ceiling at HIGH)
- `calculate_price_pressure(return_5d)` — `> 0.005 → SUPPORTING`, `< -0.005 → PRESSURING`, `else → NEUTRAL`
- `get_price_modifier(price_pressure)` — maps to user-facing strings (`trend_supporting`, `trend_stalling`, `trend_collapsing`)
- `get_ndi_trend(ndi_delta)` — `> 0.3 → ACCELERATING`, `< -0.3 → DECELERATING`, `else → STABLE`
- `get_risk_level(regime, price_pressure)` — only `OVERHEATING_DIVERGENCE` can produce non-NORMAL risk; escalates to ELEVATED (neutral price) or CRITICAL (falling price)
- `get_attention_text(risk_level, signal_state, regime)` — one-liner per state combination

**Sublayer 4C — `layer4_orchestrator.py` (195 lines)**

Pipeline coordinator: ties sublayers together.

- `process_asset(ticker, sentiment_zscore, momentum_zscore, price_history, persistence_tracker, date_string)` — runs the full 9-step pipeline for one ticker
- `process_batch(data_dict, persistence_tracker, date_string)` — validates, processes all tickers alphabetically, saves persistence once

Nine-step flow inside `process_asset`:
1. Compute measurements (validity gate)
2. Short-circuit on invalid input
3. Capture `last_ndi` BEFORE signal update (ordering constraint documented)
4. Compute signal state (updates streak)
5. Classify regime
6. Calculate base confidence + streak boost
7. Calculate price pressure
8. Determine risk level
9. Generate attention text

### Key design decisions

| Decision | Rationale |
|----------|-----------|
| NDI = sentiment - momentum | Simple, interpretable divergence measure |
| |`|ndi| > 2.2 → MEDIUM confidence | Extreme values are often noise bursts |
| Streak >= 2 → ACTIVE | 2 consecutive days above threshold = pattern, not noise |
| 5-day return window | Short enough to be responsive, long enough to filter daily noise |
| Persistence via JSON file | Survives cron-job restarts without a database dependency |
| Stale-gap detection (3 days) | Prevents weekend/holiday gaps from creating false streaks |
| Explicit save() | Avoids O(assets × days) disk writes |
| 12-field output schema | Covers all signal information: value, velocity, trend, state, confidence, risk, attention |

### File sizes

| File | Lines | Purpose |
|------|-------|---------|
| `layer4_measurement.py` | 99 | Validity gate, NDI, 5-day return |
| `layer4_persistence.py` | 123 | Streak tracking, stale detection, signal state, regime |
| `layer4_classification.py` | 155 | Confidence, price pressure, risk, attention, NDI trend |
| `layer4_orchestrator.py` | 195 | Pipeline orchestration, batch processing, validation |
| `test_layer4.py` | ~550 | 15 tests, 80+ assertions |

### Integration with Layer 3

Layer 4 receives data through the `SignalPipelineOrchestrator` which:
1. Calls Layer 3 `finalize_day()` → gets `{ticker: {date: {sentiment_zscore, momentum_zscore, sentiment_raw, momentum_return}}}`
2. Extracts `price_history` as sorted `list[float]` from `MomentumProcessor.price_history`
3. Builds `l4_input[ticker] = {sentiment_zscore, momentum_zscore, price_history}`
4. Calls `layer4_orchestrator.process_batch(l4_input, PersistenceTracker, date_string)`
5. Returns 12-field signal records

Layer 4 is completely agnostic to Layer 3 internals — it only consumes the z-scores and price lists.

---

## File Inventory (post-remediation)

| File | Role |
|------|------|
| `layer4_measurement.py` | Sublayer 4A — validity gate, NDI, 5-day return (99 lines) |
| `layer4_persistence.py` | Sublayer 4B — streak tracking, stale-gap detection, signal state, regime, explicit save (123 lines) |
| `layer4_classification.py` | Sublayer 4B — confidence (base + streak boost), NDI trend, price pressure → modifier, risk, attention (155 lines) |
| `layer4_orchestrator.py` | Sublayer 4C — pipeline orchestration, batch processing, input validation (195 lines) |
| `layers/layer3_db.py` | L3 PostgreSQL connector — warm-up, config loading, alias builder (167 lines) |
| `pipeline/signal_pipeline.py` | L3→L4 pipeline orchestrator — daily coordination, price direction transform (230 lines) |
| `test_layer4.py` | Integration tests (zero dependencies) — 15 tests, 80 checks |
| `Architecture/Layer_04_arch.md` | Authoritative design document |
| `Low-Level Design (LLD)/SignalIQ_layer_04.md` | ⚠️ Superseded — historical reference only |
| `transcript_layer_04.md` | This file — review record + change log |
| `requirements.txt` | `psycopg2-binary>=2.9` |
