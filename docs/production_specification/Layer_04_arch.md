# SignalIQ Layer 4: Production Specification

## The Core

> **NDI = sentiment_zscore − momentum_zscore → deterministic classification → readable risk signal**

---

## Module Architecture

```
layer4_measurement.py    4A: Validity gate, NDI calculation, 5-day return
layer4_persistence.py    4B: Streak tracking, stale-gap detection, signal state, regime
layer4_classification.py 4B: Confidence (base + streak boost), NDI trend, price pressure, risk, attention
layer4_orchestrator.py   4C: Pipeline orchestration, batch processing, input validation
```

Dependency direction: `measurement → persistence → classification → orchestrator`. Nothing imports backwards.

---

## Pipeline Steps (9-Step Flow)

```
INPUT: sentiment_zscore, momentum_zscore, price_history (≥ 6 prices)
```

| Step | Component | What happens | Output so far |
|------|-----------|--------------|---------------|
| 1 | `compute_measurements()` | Validity gate — checks for None inputs, insufficient price history | validity_state, ndi, return_5d |
| 2 | Short-circuit | If `validity_state != "VALID"`, return invalid result immediately | — |
| 3 | NDI velocity | Read `last_ndi` from persistence before it's overwritten; compute `ndi_delta = ndi − last_ndi` | ndi_delta, ndi_trend |
| 4 | `get_signal_state()` | Update streak in persistence tracker (with optional stale-gap reset); map to signal state | signal_state |
| 5 | `get_regime()` | Classify NDI into regime (ALIGNED / ACCUMULATION / OVERHEATING) | regime |
| 6 | Confidence | Base confidence from inverted-U + optional streak boost (>=3 days → +1 level) | confidence |
| 7 | `calculate_price_pressure()` | Classify 5-day return into SUPPORTING / NEUTRAL / PRESSURING | price_pressure |
| 8 | `get_risk_level()` | Escalate risk when OVERHEATING_DIVERGENCE + NEUTRAL or PRESSURING | risk_level |
| 9 | `get_attention_text()` | Map risk_level + signal_state to one-line guidance | attention |

```
OUTPUT: 12-field dict (see schema below)
```

### Step detail: validity gate (Step 1–2)

`compute_measurements()` in `layer4_measurement.py` is the single entry point. It centralises all input validation:

- `sentiment_zscore is None` → `INVALID_INPUT`
- `momentum_zscore is None` → `INVALID_INPUT`
- `len(price_history) < 6` → `INSUFFICIENT_PRICE_HISTORY`

No downstream function receives a `None` NDI. The orchestrator exits early before any persistence or classification call.

### Step detail: stale-gap detection (Step 4)

`update()` in `layer4_persistence.py` accepts an optional `date_string`. When provided and a `last_updated` timestamp exists for the ticker, the method computes the calendar-day gap. If the gap exceeds `MAX_GAP_DAYS = 3`, the streak is reset to 0 before applying the normal threshold update.

This prevents a weekend, holiday, or data outage from silently extending a real streak:

```
Fri:  streak=2, last_updated=2026-05-29
Mon:  gap = 3 days (≤ MAX_GAP_DAYS) → OK, streak stays 2
Tue:  gap = 4 days (> MAX_GAP_DAYS) → streak reset to 0
```

Omitting `date_string` skips stale detection entirely (backward compatible).

### Step detail: NDI velocity (Step 3)

`ndi_delta = ndi − last_ndi` captures whether divergence is widening or narrowing. `last_ndi` is read from the persistence tracker *before* `get_signal_state()` overwrites it. The ordering constraint is documented inline in the orchestrator.

`ndi_trend` classifies the delta against a 0.3 threshold:

| `ndi_delta` | `ndi_trend` |
|-------------|-------------|
| `None` | `INSUFFICIENT_DATA` |
| `> 0.3` | `ACCELERATING` |
| `< -0.3` | `DECELERATING` |
| `−0.3 to 0.3` | `STABLE` |

### Step detail: confidence (Step 6)

Two-stage: base confidence from `|NDI|`, then optional streak boost.

**Base (inverted U):**

| `\|NDI\|` | Confidence |
|-----------|------------|
| `< 0.8` | `LOW` |
| `0.8 – 2.2` | `HIGH` |
| `> 2.2` | `MEDIUM` |

Extreme readings are more likely to be sentiment outliers. Mid-range is most reliable.

**Streak boost:** when `streak >= 3`, confidence increases one level: `LOW→MEDIUM`, `MEDIUM→HIGH`. `HIGH` is a ceiling (no further boost). `INSUFFICIENT_DATA` is unchanged.

### Step detail: risk level (Step 8)

Only `OVERHEATING_DIVERGENCE` can produce non-NORMAL risk:

| Regime | Price Pressure | Risk Level |
|--------|---------------|------------|
| Any except OVERHEATING | any | NORMAL |
| OVERHEATING_DIVERGENCE | SUPPORTING | NORMAL |
| OVERHEATING_DIVERGENCE | NEUTRAL | ELEVATED |
| OVERHEATING_DIVERGENCE | PRESSURING | CRITICAL |

### Step detail: attention text (Step 9)

| Condition | Text |
|-----------|------|
| INACTIVE + INSUFFICIENT_DATA | "Insufficient data for reliable signal." |
| INACTIVE | "No divergence signal detected." |
| WATCHING | "Watching for persistence (needs 2nd consecutive day)." |
| NORMAL risk | "No action required." |
| ELEVATED risk | "Narrative optimism with stalling price. Review position." |
| CRITICAL risk | "Narrative optimism despite falling prices. Elevated caution warranted." |

---

## Output Schema

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

12 fields total.

---

## Parameter Table

| Parameter | Value | Scope | Defined in |
|-----------|-------|-------|------------|
| `NDI_THRESHOLD` | 1.5 | Regime boundary | `update()` default |
| `PRICE_FLAT_THRESHOLD` | 0.005 (0.5%) | Price pressure flat zone | `calculate_price_pressure()` default |
| `RETURN_LOOKBACK_DAYS` | 5 | N/A (hardcoded in `calculate_5d_return()`) | `layer4_measurement.py` |
| `PERSISTENCE_REQUIRED` | 2 | Days to reach ACTIVE | `get_signal_state()` |
| `PERSISTENCE_BOOST_STREAK` | 3 | Days to trigger confidence boost | `boost_confidence_by_streak()` |
| `MAX_GAP_DAYS` | 3 | Calendar-day gap before stale reset | Module constant in `layer4_persistence.py` |
| `CONFIDENCE_LOW_MAX` | 0.8 | Inverted U lower bound | `calculate_confidence()` |
| `CONFIDENCE_HIGH_MAX` | 2.2 | Inverted U upper bound | `calculate_confidence()` |
| `NDI_TREND_THRESHOLD` | 0.3 | Classifies ndi_delta into trend | `get_ndi_trend()` default |
| `BATCH_REQUIRED_KEYS` | `{sentiment_zscore, momentum_zscore, price_history}` | Input validation at batch entry | Module constant in `layer4_orchestrator.py` |

---

## State Management

Only one stateful component: `PersistenceTracker` in `layer4_persistence.py`.

### Per-ticker state shape

```python
{
    "NVDA": {
        "streak": 2,          # consecutive days with |NDI| ≥ 1.5
        "last_ndi": 1.82,     # previous day's NDI (for ndi_delta)
        "last_updated": "2026-06-02"  # date of last update (for stale detection)
    }
}
```

### Storage

In-memory `dict` + `persistence_state.json` for restart recovery (daily cron context).

### Save policy

Explicit save — `persistence_tracker.save()` is called once at the end of `process_batch()`, not after every individual update. This avoids N writes per batch (N=500 tickers → 1 file write instead of 500).

### Update rule

```python
if ndi is None:
    streak = 0
elif abs(ndi) >= 1.5:
    streak += 1
else:
    streak = 0
```

Stale override (when `date_string` is provided and gap > 3 days): streak resets to 0 before the rule above.

---

## Key Distinctions

| Concept | Old approach (LLD) | Current approach |
|---------|--------------------|------------------|
| Signal state vs regime | Combined ("Watching" as regime) | Separated: `signal_state` (temporal) + `regime` (semantic) |
| Persistence | Reset counter below threshold | Streak tracking (no reset on sub-threshold) + stale-gap detection |
| Confidence | Monotonic (stronger = higher) | Inverted U (mid-range most reliable) + streak boost |
| Validity | Scattered across components | Centralized gate at 4A entry |
| Price role | Modifier with 3 states | Pressure score SUPPORTING/NEUTRAL/PRESSURING + escalation rule |
| Output | 9 fields | 12 fields including ndi_delta, ndi_trend, price_modifier, persistence_days |
| Save policy | Auto-save on every update | Explicit save at end of batch |
| Input validation | None at batch level | `validate_batch_input()` at entry |

---

## Layer 4 Status: PRODUCTION

> Deterministic. Centralized validity gate. Stale-aware streak persistence. Three regimes. Inverted-U + boosted confidence. NDI velocity. Price escalates risk. Input validated at entry. Core intact.
