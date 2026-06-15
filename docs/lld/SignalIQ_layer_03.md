# SignalIQ Layer 3: Low-Level Design
## Overview

Layer 3 transforms raw inputs from Layer 2 into normalized z-scores for sentiment and momentum. It is the **intelligence layer** — where headlines become quantified sentiment and prices become normalized momentum.

```
Layer 2 (PostgreSQL) → Layer 3 → Layer 4 (NDI Calculator)
                           │
                           ├── headlines + aliases → sentiment_zscore
                           └── prices              → momentum_zscore
```

---

## Design Assumptions (Explicit)

Before defining components, these are the premises that connect Layer 3 to SignalIQ's thesis:

| # | Assumption | Rationale |
|---|------------|-----------|
| 1 | News headlines reflect the market narrative that Keynes called "animal spirits" | Core product thesis |
| 2 | Loughran-McDonald lexicon is sufficient to capture financial sentiment for MVP | Validated in Tetlock (2007) |
| 3 | Daily returns capture short-term momentum sufficiently | 20-day window balances sensitivity and stability |
| 4 | Rolling z-score captures relative deviations, not absolute levels | Layer 4 operates on divergences, not absolute values |
| 5 | The 20-day window (~1 calendar month) is the minimum standard for stable normalization | Consistent with finance literature |

---

## Components (No Code)

| Module | Responsibility | Stateful |
|--------|----------------|----------|
| Configuration | Centralized parameters, thresholds, file paths | No |
| Entity Resolution | Alias loading, headline → ticker matching | No |
| Sentiment | Lexicon scoring, daily aggregation, rolling z-score | Yes (historical window per ticker) |
| Momentum | Daily return calculation, rolling z-score | Yes (historical window per ticker) |
| Orchestrator | Main pipeline, time alignment, state coordination | Yes (last prices, headline buffer) |

---

## Module 1: Configuration

**Purpose:** Single source of truth for all Layer 3 parameters.

### Parameters (Frozen for MVP)

| Parameter | MVP Value | Rationale |
|-----------|-----------|-----------|
| `MIN_HEADLINES_PER_DAY` | 3 | Heuristic to reduce noise in low-coverage assets |
| `SENTIMENT_WINDOW_DAYS` | 20 | Standard finance window (~1 month) |
| `MIN_VALID_DAYS_SENTIMENT` | 10 | Half the window; prevents unstable z-scores |
| `MOMENTUM_WINDOW_DAYS` | 20 | Symmetry with sentiment window |
| `MIN_VALID_DAYS_MOMENTUM` | 10 | Same logic as sentiment |
| `DAILY_CUTOFF_HOUR_ET` | 16 (4:00 PM) | Market close; prevents after-hours news contamination |
| `MIN_ALIAS_LENGTH` | 3 | Prevents false positives from single letters |

### Why 20 Days?

| Alternative | Problem |
|-------------|---------|
| 5 days | Too noisy, overreacts to isolated news |
| 10 days | Still sensitive to outliers |
| **20 days** | Balances sensitivity and stability; literature standard |
| 60 days | Too slow to detect divergences |

### Why Classical Z-Score Instead of Robust Alternatives?

| Method | Problem for MVP |
|--------|-----------------|
| Robust z-score (MAD) | More complexity, marginal benefit |
| Percentile ranking | Loses magnitude information |
| **Classical z-score** | Simple, interpretable, sufficient for divergence detection |

**Note:** For extreme values (>2.2 standard deviations), Layer 4 already reduces confidence (inverted U). Classical z-score is acceptable because outlier risk is handled downstream.

---

## Module 2: Entity Resolution

**Purpose:** Map each headline to one or more tickers.

### Phase 1: URL Parameter (High Precision)

- If headline comes from a ticker-specific feed (e.g., `?s=NVDA`)
- Extract parameter value
- Exact match against alias file keys
- If match found → assign to that ticker, **skip Phase 2**

### Phase 2: Alias Matching (Recall-oriented)

- Normalize headline: lowercase, collapse whitespace
- For each alias in file (minimum 3 characters)
- Check if alias appears as a **whole word** (word boundaries)
- Case-insensitive matching
- Multiple matches possible → assign to ALL matching tickers

### Alias File Format (`config/entity_aliases.json`)

```json
{
  "NVDA": ["NVIDIA", "Nvidia", "NVIDIA CORPORATION"],
  "AAPL": ["Apple", "Apple Inc."],
  "MSFT": ["Microsoft", "Microsoft Corporation"]
}
```

### Quality Contract (MVP Targets)

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| Entity precision | >95% | Manual sample of 200 headlines |
| Entity recall | >85% | Percentage of relevant headlines that match |
| False positives | <2% | Headlines assigned to wrong ticker |

---

## Module 3: Sentiment

**Purpose:** Convert headline text to sentiment z-scores.

### Subcomponent 3A: Lexicon

- **Source:** Loughran-McDonald (2007)
- **Format:** CSV with columns `word`, `sentiment` (positive/negative)
- **Structure:** Two sets: positive words, negative words

### Subcomponent 3B: Per-Headline Scoring

**Formula:** `polarity = (positive_count - negative_count) / total_sentiment_words`

**Rules:**
- Tokenize: split into alphabetic words
- Count positive and negative matches
- If total_sentiment_words == 0 → polarity = 0.0 (neutral)
- Output range: -1.0 (very negative) to +1.0 (very positive)

### Subcomponent 3C: Daily Aggregation

**Input:** List of polarity scores for one asset on one trading day

**Output:** Mean of all scores, or NULL if fewer than `MIN_HEADLINES_PER_DAY`

**Example:**
- Headlines: [0.8, 0.6, 0.7, 0.5] → mean = 0.65
- Headlines: [0.8, 0.6] (only 2) → NULL

### Subcomponent 3D: Rolling Normalization (Z-Score)

**State:** Dictionary `{ticker: [(date, sentiment_raw), ...]}`

**Process per asset per day:**
1. Retrieve last `SENTIMENT_WINDOW_DAYS` of history (excluding today)
2. If fewer than `MIN_VALID_DAYS_SENTIMENT` → return NULL
3. Calculate mean and standard deviation of historical values
4. If standard deviation == 0 → return 0.0 (no variation)
5. Return `(today_raw - mean) / std`

### Quality Contract

| Metric | Target | Notes |
|--------|--------|-------|
| Daily sentiment coverage | >80% of days with ≥3 headlines | Per asset |
| Lexicon accuracy | 65-75% vs human | Standard in literature |
| Days until first valid z-score | 20 days | Full window |

---

## Module 4: Momentum

**Purpose:** Convert daily prices to momentum z-scores.

### Subcomponent 4A: Daily Return

**Formula:** `daily_return = (price_today - price_yesterday) / price_yesterday`

**Rules:**
- If price_yesterday == 0 → return 0.0 (defensive)
- If no previous price (first day for ticker) → return NULL
- Do NOT interpolate missing prices

### Subcomponent 4B: Rolling Normalization (Z-Score)

**State:** Dictionary `{ticker: [(date, daily_return), ...]}`

**Process per asset per day:**
1. Retrieve last `MOMENTUM_WINDOW_DAYS` of history (excluding today)
2. If fewer than `MIN_VALID_DAYS_MOMENTUM` → return NULL
3. Calculate mean and standard deviation of historical returns
4. If standard deviation == 0 → return 0.0
5. Return `(today_return - mean) / std`

### Quality Contract

| Metric | Target |
|--------|--------|
| Price completeness | >99% of trading days |
| Days until first valid z-score | 20 days |

---

## Module 5: Orchestrator

**Purpose:** Coordinate all subcomponents, manage state, produce final output.

### Subcomponent 5A: Time Aligner

**Purpose:** Assign each headline to a trading day based on 4:00 PM ET cutoff.

**Rules:**
1. Convert timestamp to Eastern Time
2. If time < 4:00 PM ET → headline belongs to that calendar day
3. If time ≥ 4:00 PM ET → headline belongs to next trading day
4. If `published_at` is NULL → use `ingested_at` as fallback
5. Weekend headlines → assign to next trading day

**Known limitation:** UTC-4 conversion fails during Daylight Saving Time. Post-MVP use `zoneinfo` or `pytz`.

### Subcomponent 5B: Price Processor

**State:** `last_price[ticker][date] = adj_close`

**Process per price update:**
1. Store current price with date
2. Find most recent previous price (any date before current)
3. If found → calculate daily return → store in momentum history
4. If not found → return NULL (first day for this ticker)

### Subcomponent 5C: Headline Processor

**Process per headline:**
1. Determine trading day (via Time Aligner)
2. Normalize headline text
3. Resolve tickers (via Entity Resolver)
4. If no tickers resolved → discard headline (log for debugging)
5. Score sentiment (via Lexicon)
6. Store in buffer: `(ticker, trading_day, sentiment_score)`

### Subcomponent 5D: Daily Finalization

**Called once per day after all headlines and prices are processed.**

**Process:**
1. For each ticker in the system:
   a. Aggregate buffered headlines for that ticker/day → sentiment_raw (or NULL)
   b. Add sentiment_raw to sentiment history
   c. Calculate sentiment_zscore from history (or NULL)
   d. Retrieve daily_return from momentum history for this day
   e. Calculate momentum_zscore from history (or NULL)
2. Return dictionary to Layer 4

---

## State Management Summary

| Component | State | Persistence | Reset Behavior |
|-----------|-------|-------------|----------------|
| Sentiment | `history[ticker] = [(date, raw)]` | Memory only | Loss of historical window on restart |
| Momentum | `history[ticker] = [(date, return)]` | Memory only | Loss of historical window on restart |
| Orchestrator | `last_price[ticker][date]` | Memory only | Rebuilds from prices |
| Orchestrator | Headline buffer | Memory only | Cleared after daily finalization |

**Design decision:** Layer 3 does NOT persist to disk in MVP because it can recompute from Layer 2 on each restart. For production, add checkpointing.

---

## Output Schema (to Layer 4)

| Field | Type | Description |
|-------|------|-------------|
| ticker | string | Asset identifier |
| date | string (YYYY-MM-DD) | Trading day |
| sentiment_zscore | float or null | Normalized sentiment (rolling z-score) |
| momentum_zscore | float or null | Normalized momentum (rolling z-score) |

**Structure:** Dictionary `{ticker: {date: {sentiment_zscore, momentum_zscore}}}`

**Field rules:**
- Both values are float or None
- None means: insufficient data, invalid input, or normalization not yet possible
- Layer 4 handles None by producing NULL NDI

---

## Edge Cases and Handling

| Edge Case | Detection | Output |
|-----------|-----------|--------|
| Headline with no ticker match | `resolve()` returns empty list | Discard headline, log warning |
| Fewer than 3 headlines per day | `len(headlines) < MIN_HEADLINES` | `sentiment_raw = None` |
| First 19 days of data | History length < window | `sentiment_zscore = None` |
| Missing price for a day | No price record | `daily_return = None` |
| Price exactly 0 | Division by zero | `daily_return = 0.0` |
| Standard deviation = 0 | All returns identical | `zscore = 0.0` |
| published_at is NULL | Missing timestamp | Use ingested_at |
| Weekend headline | Saturday/Sunday timestamp | Trading day = Monday |

---

## Known Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Lexicon doesn't understand context (e.g., "miss" as earnings miss vs "miss" as想念) | False sentiment polarity | Post-MVP: add context rules or fine-tuned model |
| Sarcasm or ironic headlines | Inverted sentiment signal | Accept for MVP; post-MVP sentiment LLM |
| Duplicate headlines across sources | Overweighting of same news | Deduplication in Layer 2 (headline hash) |
| Ambiguous aliases (e.g., "AMD" vs "AMC") | Entity resolution errors | Alias file review; URL param priority helps |
| Uneven coverage across assets (NVDA vs BTC-USD) | Bias toward large caps | Document coverage in pilot offer |

---

## Data Flow Diagram

```
Layer 2
   │
   ├── Headlines ──→ Time Aligner ──→ Entity Resolver ──→ Sentiment Scorer ──→ Daily Buffer
   │                                                                                │
   └── Prices ────→ Price Processor ──→ Daily Return ──→ Momentum History ←────────┘
                                                              │
                                                              ▼
                                              Daily Finalization
                                                      │
                                                      ▼
                                              sentiment_zscore
                                              momentum_zscore
                                                      │
                                                      ▼
                                              Layer 4 (NDI)
```

---

## Quality Contract (Layer 3 Overall)

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| Entity precision | >95% | Manual sample of 200 headlines |
| Daily sentiment coverage | >80% of days with ≥3 headlines | Per asset, 90 trading days |
| Price completeness | >99% of trading days | Per asset, 90 trading days |
| Days until first valid z-score | 20 days | Window completion |
| Determinism | 100% | Same inputs → same outputs |

---

## Computational Budget (MVP)

| Metric | Target |
|--------|--------|
| Headlines processed per day | ~10,000 |
| Supported tickers | 5 (MVP), scalable to 500 |
| Layer 3 batch runtime | <5 minutes |
| Maximum memory | <1 GB |

---

## Integration with Layer 2

Layer 3 expects from Layer 2:

| Data | Table | Fields |
|------|-------|--------|
| Headlines | `raw.news_headlines` | `headline`, `published_at`, `ingested_at`, `source_asset` |
| Prices | `raw.prices` | `ticker`, `date`, `adj_close` |

Layer 3 does NOT write to database in MVP. Output is in-memory to Layer 4.

---

## Integration with Layer 4

Layer 4 expects from Layer 3:

| Field | Type |
|-------|------|
| ticker | string |
| date | string |
| sentiment_zscore | float or null |
| momentum_zscore | float or null |

- Layer 3 runs **before** Layer 4 in the daily batch
- Output passed directly to Layer 4 orchestrator (no intermediate storage)

---

## Setup Prerequisites (Before Implementation)

1. **Download Loughran-McDonald lexicon:**
   - Source: https://sraf.nd.edu/loughranmcdonald-master-dictionary/
   - Save to: `data/lexicons/loughran_mcdonald/loughran_mcdonald.csv`

2. **Create alias file:**
   - Path: `config/entity_aliases.json`
   - Include all tickers from `monitored_assets`

3. **Verify timezone handling:**
   - MVP assumes all timestamps are UTC
   - Post-MVP use `zoneinfo` or `pytz`

---

## Design Decisions (Explicitly Documented)

| Decision | Rejected Alternative | Rationale |
|----------|---------------------|-----------|
| 20-day window | 5, 10, 60 days | Balance between sensitivity and stability |
| Classical z-score | Robust z-score (MAD) | Simplicity; outlier risk handled in Layer 4 |
| UTC-4 for ET | `zoneinfo` | MVP; DST added post-MVP |
| No disk persistence | Checkpointing | MVP can recompute from Layer 2 |
| Minimum 3 headlines per day | 1 or 5 | Heuristic to reduce noise in low-coverage assets |

---

## Layer 3 Status: READY FOR IMPLEMENTATION

> No open decisions. Parameters frozen. Assumptions explicit. Quality contracts defined. Edge cases documented. Known risks acknowledged. Ready for code.

---

**SignalIQ** 🔹

*Layer 3 LLD revised. Sentiment via lexicon. Momentum via prices. Rolling z-scores. No ML. Deterministic. Explicit quality contracts. Known risks documented.*
