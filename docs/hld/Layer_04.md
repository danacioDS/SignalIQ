
---

# SignalIQ: Layer 4 Specification

## Signal Generation (NDI + Regime Classification)

---

## Design Philosophy

Layer 4 consumes the outputs of Layer 3 (`sentiment_zscore` and `momentum_zscore` per asset per day) and produces:

1. **Narrative Divergence Index (NDI)** — the core metric
2. **Regime classification** — actionable interpretation
3. **Attention signal** — not a prediction, a measurement

Layer 4 is **deterministic given Layer 3 outputs**. No training. No optimization. No fitting to historical outcomes.

> Layer 4 does not predict. Layer 4 measures divergence and classifies regimes.

---

## Input: From Layer 3

Layer 3 provides an in-memory structure (per asset, per day):

```python
{
    "NVDA": {
        "2026-06-01": {"sentiment_zscore": 0.32, "momentum_zscore": -0.15},
        "2026-06-02": {"sentiment_zscore": 0.45, "momentum_zscore": 0.02},
        ...
    },
    "AAPL": {...},
    "MSFT": {...},
    "SPX": {...},
    "BTC-USD": {...}
}
```

**Note:** Either `sentiment_zscore` or `momentum_zscore` may be `NULL` if insufficient data.

---

## Output 1: Narrative Divergence Index (NDI)

### Formula

```
NDI(t) = sentiment_zscore(t) − momentum_zscore(t)
```

### Range

Theoretical range: approximately -6 to +6 (since each z-score typically ranges -3 to +3)

### Interpretation of NDI Sign

| NDI Sign | Meaning |
|----------|---------|
| **Positive NDI** | Sentiment is more positive than momentum. Narrative is ahead of price reality. |
| **NDI near zero** | Sentiment and momentum are aligned. Healthy trend. |
| **Negative NDI** | Momentum is stronger than sentiment. Price moving without narrative support. |

### Handling NULL Values

| Scenario | NDI Output |
|----------|------------|
| Both z-scores available | NDI = sentiment_zscore − momentum_zscore |
| Either z-score is NULL | NDI = NULL |

**Why:** No signal is better than a fabricated signal.

---

## Output 2: Regime Classification

Layer 4 classifies each (asset, day) into one of five regimes based on NDI and price action.

### Price Action Input

Layer 4 requires one additional input from Layer 3: **price direction over the past 5 days**.

| Price Direction | Definition |
|----------------|------------|
| Rising | 5-day simple return > 0.5% |
| Flat | 5-day simple return between -0.5% and +0.5% |
| Falling | 5-day simple return < -0.5% |

**Why 5 days:** Matches Tetlock's short-term reversal horizon.

---

### Regime Taxonomy

| Regime | NDI Condition | Price Condition | Interpretation |
|--------|---------------|-----------------|----------------|
| 🔵 **Silent Accumulation** | NDI < -1.5 | Rising or Flat | Prices moving without narrative support. Potential entry opportunity. |
| ⚪ **Aligned** | -1.5 ≤ NDI ≤ 1.5 | Any | Narrative and price in sync. Healthy trend. |
| 🟡 **Narrative Exhaustion** | NDI > 1.5 | Flat or Rising slowly | Optimism persists but momentum weakening. Story running out of buyers. |
| 🟠 **Divergence Warning** | NDI > 1.5 | Flat (0 to -0.5% over 5 days) | Institutional money may be exiting while public enthusiasm remains high. |
| 🔴 **Severe Divergence** | NDI > 1.5 | Falling (< -0.5%) | Maximum-risk environment. Historically associated with abrupt corrections. |

### Regime Decision Flow

```
1. Is NDI NULL? → Yes → Output "Insufficient Data"
2. Is NDI < -1.5? → Yes → Check price direction → "Silent Accumulation" if rising/flat
3. Is NDI > 1.5? → Yes → Check price direction:
   - Falling (< -0.5%) → "Severe Divergence"
   - Flat (0 to -0.5%) → "Divergence Warning"
   - Rising or Flat > -0.5% → "Narrative Exhaustion"
4. Else → "Aligned"
```

---

## Output 3: Attention Signal (The Commercial Product)

Layer 4 produces a **daily attention signal** for each asset:

| Signal Level | Meaning | Recommended Action |
|--------------|---------|--------------------|
| **Green** | Aligned or Silent Accumulation | No action required |
| **Yellow** | Narrative Exhaustion | Review position; narrative may be peaking |
| **Orange** | Divergence Warning | Investigate; potential risk emerging |
| **Red** | Severe Divergence | Elevated risk; consider portfolio adjustment |

### Signal Logic

| Regime | Signal Color |
|--------|--------------|
| Silent Accumulation | 🟢 Green |
| Aligned | 🟢 Green |
| Narrative Exhaustion | 🟡 Yellow |
| Divergence Warning | 🟠 Orange |
| Severe Divergence | 🔴 Red |
| Insufficient Data | ⚪ Gray |

---

## Example Output (Per Asset, Per Day)

```json
{
  "ticker": "NVDA",
  "date": "2026-06-02",
  "sentiment_zscore": 0.45,
  "momentum_zscore": 0.02,
  "ndi": 0.43,
  "price_direction_5d": "rising",
  "regime": "Aligned",
  "signal_color": "Green",
  "attention": "No action required"
}
```

```json
{
  "ticker": "SPX",
  "date": "2026-06-02",
  "sentiment_zscore": 2.10,
  "momentum_zscore": 0.30,
  "ndi": 1.80,
  "price_direction_5d": "flat",
  "regime": "Narrative Exhaustion",
  "signal_color": "Yellow",
  "attention": "Review position; narrative may be peaking"
}
```

---

## What Layer 4 Does NOT Do

| ❌ Not in Layer 4 | Reason |
|------------------|--------|
| Predict future prices | Violates "measurement, not prediction" |
| Output buy/sell signals | Commercial product is risk intelligence, not trading signals |
| Backtest optimization | No parameter fitting to historical outcomes |
| Probabilistic forecasts | Post-MVP (confidence intervals, probability of correction) |
| Portfolio-level aggregation | Post-MVP (combine signals across assets) |
| Bubble risk scoring | Post-MVP (requires macro feeds) |

---

## Parameter Slots (Frozen for MVP)

| Parameter | MVP Value | Rationale |
|-----------|-----------|-----------|
| NDI threshold for divergence | 1.5 | Approximately top 10% of distribution |
| NDI threshold for accumulation | -1.5 | Approximately bottom 10% |
| Price direction lookback | 5 days | Matches Tetlock reversal horizon |
| Price direction threshold | 0.5% | Avoids noise in flat markets |

**All parameters frozen in MVP.** Configurable post-MVP based on empirical validation.

---

## Validation Approach (Post-MVP)

Layer 4's usefulness is tested by asking:

> Does NDI > 1.5 with flat/falling prices precede a higher-than-random probability of continued decline?

**Validation method (post-MVP, not in Layer 4):**
- Compare forward returns after divergence signals vs baseline
- Measure precision, recall, and lift
- Do not optimize thresholds based on historical data (prevents overfitting)

---

## Layer 4 Status: FROZEN

> Deterministic regime classification based on NDI and price action. No training. No optimization.
> No prediction. Outputs are measurements, not forecasts.

---

## Next Step

All four layers are now specified:

| Layer | Status | Output |
|-------|--------|--------|
| Layer 1 | Frozen | Raw prices + headlines |
| Layer 2 | Frozen | Structured storage |
| Layer 3 | Frozen | sentiment_zscore + momentum_zscore |
| Layer 4 | Frozen | NDI + Regime + Signal Color |

Do you want me to produce a **single unified specification document** that consolidates all four layers, 
or proceed to **validation framework design** (how to test whether SignalIQ actually works)?
