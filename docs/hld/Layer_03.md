
---

# SignalIQ: Layer 3 Contract v1 (Frozen)

## No Open Decisions. Only Parameter Slots with Defaults.

---

## The Contract

Layer 3 receives:
- Daily closing prices from Layer 2
- Raw headlines with timestamps and URL parameter values from Layer 2
- Shared alias configuration from `config/entity_aliases.json`

Layer 3 produces for each asset on each trading day:
- `sentiment_zscore`
- `momentum_zscore`

Layer 4 consumes these to compute NDI and regime classification.

---

## Frozen Decision 1: Sentiment Lexicon

**Choice:** Loughran-McDonald financial sentiment lexicon

**Why frozen:** Finance-specific. Academically validated in Tetlock (2007) and subsequent literature. Available as pre-built word list.

**Parameter slot:** Not configurable in MVP.

---

## Frozen Decision 2: Score per Headline

**Choice:** Count-based polarity: (`positive_words - negative_words`) / (`total_sentiment_words`)

**Output range:** -1.0 to +1.0 continuous

**Neutral headline (zero positive, zero negative):** Score = 0.0

**Why frozen:** Simple, interpretable, matches academic precedent. No weighted or probabilistic scoring in MVP.

**Parameter slot:** Not configurable in MVP.

---

## Frozen Decision 3: Aggregation Across Headlines (Per Asset, Per Day)

**Choice:** Mean of all headline scores for that asset on that trading day

**Why frozen:** Simple. Median would discard information. Weighted aggregation requires source influence scoring (post-MVP).

**Parameter slot:** Not configurable in MVP.

---

## Frozen Decision 4: Minimum Headlines Required

**Choice:** If fewer than 3 headlines for an asset on a trading day → `sentiment_raw = NULL`

**Why frozen:** Prevents false signal from low-coverage days. 3 is a minimal statistical threshold.

**Parameter slot:** `MIN_HEADLINES_PER_DAY = 3` (configurable post-MVP)

---

## Frozen Decision 5: Sentiment Normalization Window

**Choice:** 20-day rolling window for mean and standard deviation

**Formula:** `sentiment_zscore = (daily_sentiment - rolling_mean_20d) / rolling_std_20d`

**Why frozen:** Matches momentum window (see below). Creates symmetric normalization. 20 trading days ≈ 1 calendar month.

**Parameter slot:** `SENTIMENT_WINDOW_DAYS = 20` (configurable post-MVP)

---

## Frozen Decision 6: Minimum Days for Valid Z-Score

**Choice:** Require at least 10 valid daily sentiment values in the 20-day window

**If insufficient:** `sentiment_zscore = NULL`

**Why frozen:** Prevents unstable z-scores from tiny samples.

**Parameter slot:** `MIN_VALID_DAYS_SENTIMENT = 10` (configurable post-MVP)

---

## Frozen Decision 7: Return Type for Momentum

**Choice:** Simple daily return: `(price_today - price_yesterday) / price_yesterday`

**Why frozen:** Simple. Log returns are mathematically preferable but add complexity without clear MVP benefit.

**Parameter slot:** Not configurable in MVP.

---

## Frozen Decision 8: Momentum Lookback Window

**Choice:** 20-day rolling window for mean and standard deviation

**Formula:** `momentum_zscore = (daily_return - rolling_mean_20d) / rolling_std_20d`

**Why frozen:** Matches sentiment window. Tetlock validated signals over 5, 10, and 20 days. 20 is the most conservative and stable for MVP.

**Parameter slot:** `MOMENTUM_WINDOW_DAYS = 20` (configurable post-MVP)

---

## Frozen Decision 9: Minimum Days for Valid Momentum Z-Score

**Choice:** Require at least 10 valid daily return values in the 20-day window

**If insufficient:** `momentum_zscore = NULL`

**Why frozen:** Same logic as sentiment.

**Parameter slot:** `MIN_VALID_DAYS_MOMENTUM = 10` (configurable post-MVP)

---

## Frozen Decision 10: Time Alignment (Headline → Trading Day)

**Choice:** Cutoff at 4:00 PM Eastern Time (market close)

**Rules:**
- If `published_at` has timezone → convert to ET
- If `published_at` has no timezone → assume UTC, convert to ET
- If `published_at` is NULL → use `ingested_at`, same conversion
- If timestamp < 4:00 PM ET → belongs to that trading day
- If timestamp ≥ 4:00 PM ET → belongs to next trading day
- Weekend/holiday headlines → assigned to next trading day

**Why frozen:** Matches market close. Prevents after-hours news from polluting same-day sentiment.

**Parameter slot:** `DAILY_CUTOFF_HOUR_ET = 16` (configurable post-MVP)

---

## Frozen Decision 11: Entity Resolution — URL Parameter Priority

**Choice:** If `url_param_value` is non-empty and matches a ticker in `entity_aliases.json` keys → assign headline to that ticker (exact match only)

**Why frozen:** URL parameters from ticker feeds are high-precision signals. Exact match prevents false positives.

**Parameter slot:** Not configurable in MVP.

---

## Frozen Decision 12: Entity Resolution — Alias Matching

**Choice:** Word-boundary substring matching (case-insensitive)

**Rule:** Normalized headline must contain the alias surrounded by non-alphanumeric characters or string boundaries.

**Example:** "NVIDIA" matches "NVIDIA beats earnings" but not "NVIDIAcompetitor"

**Why frozen:** Prevents false positives from partial matches.

**Parameter slot:** Not configurable in MVP.

---

## Frozen Decision 13: Entity Resolution — Conflict Resolution

**Choice:** If multiple aliases from different tickers match the same headline, assign headline to ALL matching tickers

**Why frozen:** A headline about "Apple and Microsoft" should affect both. Layer 4 can decide how to handle multi-asset signals.

**Parameter slot:** Not configurable in MVP.

---

## Frozen Decision 14: Entity Resolution — Minimum Alias Length

**Choice:** Aliases shorter than 3 characters are ignored

**Why frozen:** Prevents single-letter false positives (e.g., "A" matching everything).

**Parameter slot:** `MIN_ALIAS_LENGTH = 3` (configurable post-MVP)

---

## Frozen Decision 15: NULL Handling — Missing Prices

**Choice:** If `adj_close` is missing for a trading day, `daily_return = NULL` (do not interpolate)

**Why frozen:** No data is better than fabricated data.

---

## Frozen Decision 16: NULL Handling — Missing Timestamps

**Choice:** If `published_at` is NULL, use `ingested_at` as fallback, then apply 4:00 PM ET cutoff rule

**Why frozen:** Ingestion timestamp is the next best proxy.

---

## Summary: Parameter Slots (Configurable Post-MVP)

| Parameter | MVP Value |
|-----------|-----------|
| `MIN_HEADLINES_PER_DAY` | 3 |
| `SENTIMENT_WINDOW_DAYS` | 20 |
| `MIN_VALID_DAYS_SENTIMENT` | 10 |
| `MOMENTUM_WINDOW_DAYS` | 20 |
| `MIN_VALID_DAYS_MOMENTUM` | 10 |
| `DAILY_CUTOFF_HOUR_ET` | 16 |
| `MIN_ALIAS_LENGTH` | 3 |

**All other decisions frozen. Not configurable in MVP.**

---

## What Layer 3 Does NOT Produce in MVP (Reinforced)

| Excluded | Reason |
|----------|--------|
| Source influence weighting | Post-MVP |
| Narrative consensus scores | Post-MVP |
| Confidence intervals | Post-MVP |
| Intraday signals | Post-MVP |
| Bubble risk scores | Layer 4 post-MVP |

---

## Output Schema (What Layer 4 Receives)

Layer 3 outputs an in-memory data structure (no database write in MVP):

```python
{
    "NVDA": {
        "2026-06-01": {"sentiment_zscore": 0.32, "momentum_zscore": -0.15},
        "2026-06-02": {"sentiment_zscore": 0.45, "momentum_zscore": 0.02},
        "2026-06-03": {"sentiment_zscore": None, "momentum_zscore": -0.08}
    },
    "AAPL": {...},
    "MSFT": {...},
    "SPX": {...},
    "BTC-USD": {...}
}
```

---

## Layer 3 Status: FROZEN

> No open decisions. All choices specified. Parameter slots explicitly labeled with MVP defaults. Ready to co-design Layer 2.

---
