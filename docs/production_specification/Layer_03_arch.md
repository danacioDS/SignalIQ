# SignalIQ Layer 3: Production Specification

## The Core

> **sentiment_zscore = f(Loughran-McDonald lexicon, rolling 20-day window)**
> **momentum_zscore = f(simple daily return, rolling 20-day window)**

Layer 3 transforms raw headlines and prices into normalized z-scores that Layer 4 consumes to compute NDI.

**Status: IMPLEMENTATION READY (MVP Production Candidate)**

---

## Module Architecture

```
layer3_config.py          Configuration: parameters, thresholds, file paths
layer3_entity.py          Entity resolution: alias loading, headline → ticker matching
layer3_sentiment.py       Sentiment: lexicon scoring, daily aggregation, rolling z-score
layer3_momentum.py        Momentum: daily return calculation, rolling z-score
layer3_orchestrator.py    Pipeline orchestration: time alignment, state coordination, batch output
```

**Dependency direction:** `config → entity → sentiment → momentum → orchestrator`. Nothing imports backwards.

**Note on "Production" status:** This specification is MVP-ready but not full production. Production systems would additionally require: persistence (checkpointing), monitoring, retries, audit logs, idempotency, schema versioning, and alerting. Those are explicitly post-MVP.

---

## Pipeline Steps (10-Step Flow)

```
INPUT: 
  - Headlines: headline_text, published_at (or ingested_at), url_param (optional)
  - Prices: ticker, date, adj_close
```

| Step | Component | What happens | Output so far |
|------|-----------|--------------|---------------|
| 1 | `validate_batch_input()` | Check all required keys present in batch dict | validation errors or proceed |
| 2 | Time Aligner | Convert timestamp to ET, apply 4:00 PM cutoff → trading_day | trading_day (YYYY-MM-DD) |
| 3 | Entity Resolver | URL param first (exact), then alias matching (word-boundary) | list of tickers (may be empty) |
| 4 | Sentiment Scorer | Lexicon polarity: (pos - neg) / total_sentiment_words | sentiment_raw (-1.0 to +1.0) |
| 5 | Buffer | Store (ticker, trading_day, sentiment_raw) in daily buffer | — |
| 6 | Price Processor | Store price, find previous price, calculate daily_return | daily_return (float or None) |
| 7 | Momentum History | Append daily_return to rolling history (keep last 30 days) | — |
| 8 | Daily Finalization (sentiment) | Aggregate buffer → daily_sentiment_raw (or None if <3 headlines) → compute rolling z-score | sentiment_zscore (float or None) |
| 9 | Daily Finalization (momentum) | Retrieve daily_return for this day → compute rolling z-score | momentum_zscore (float or None) |
| 10 | Output | Build dictionary for Layer 4 | `{ticker: {date: {sentiment_zscore, momentum_zscore}}}` |

---

### Step detail: batch input validation (Step 1)

`validate_batch_input()` in `layer3_orchestrator.py` checks every entry against expected data **from Layer 2** (not Layer 3 outputs):

```python
HEADLINE_REQUIRED_KEYS = {"headline_text", "published_at", "ingested_at", "url_param"}
PRICE_REQUIRED_KEYS = {"ticker", "date", "adj_close"}
```

**Not:** `sentiment_zscore` or `momentum_zscore` — those are outputs, not inputs.

If any record is missing a required key → raise `ValueError` with details. No downstream processing occurs on malformed input.

---

### Step detail: time alignment (Step 2)

`TimeAligner.get_trading_day()` in `layer3_orchestrator.py` applies the 4:00 PM ET cutoff.

**Single source of truth:** TimeAligner owns trading day assignment. No other component modifies or overrides this decision.

| Condition | Trading day assignment |
|-----------|------------------------|
| timestamp < 4:00 PM ET | Same calendar day |
| timestamp ≥ 4:00 PM ET | Next calendar day |
| `published_at` is NULL | Use `ingested_at` as fallback, then apply same rules |
| Weekend/holiday timestamp | TimeAligner still returns a calendar day; caller (Layer 2) is responsible for mapping to trading days if needed |

**Known limitation:** MVP assumes UTC input, subtracts 4 hours. No DST handling. Post-MVP use `zoneinfo`.

---

### Step detail: entity resolution (Step 3)

`EntityResolver.resolve()` in `layer3_entity.py` implements two-phase matching.

**Phase 1: URL Parameter (High Precision)**
- If `url_param` is non-empty and matches a ticker key in alias file → return `[ticker]`
- **Skip Phase 2 entirely**

**Phase 2: Alias Matching (Recall-oriented)**
- Normalize headline: lowercase, collapse whitespace
- Word-boundary regex: `\b{alias}\b`
- Case-insensitive matching
- Return **all** tickers whose aliases appear

**Known limitation:** Word-boundary matching fails for ambiguous cases:
- "Apple supplier reports slowdown" → matches AAPL (desired? maybe not)
- "Amazon rainforest" → matches AMZN (false positive)
- "Meta analysis" (research paper) → matches META (false positive)

For MVP these are acceptable. Post-MVP: add negative alias lists or context rules.

**Alias file format (`config/entity_aliases.json`) — MVP conservative approach:**

```json
{
  "NVDA": ["NVIDIA", "Nvidia", "NVIDIA CORPORATION", "Nvidia Corp"],
  "AAPL": ["Apple Inc", "Apple shares", "Apple stock"],
  "MSFT": ["Microsoft", "Microsoft Corporation", "MSFT"]
}
```

**Note:** Generic aliases like `"Apple"` alone are intentionally omitted to reduce false positives. For MVP, precision is prioritized over recall.

**Quality targets:**
- Precision >95% (manual sample of 200 headlines)
- Recall >85%
- False positives <2%

---

### Step detail: sentiment scoring (Step 4)

`SentimentProcessor.score_headline()` in `layer3_sentiment.py` uses Loughran-McDonald lexicon.

**Formula:**
```
polarity = (positive_word_count - negative_word_count) / total_sentiment_words
```

**Rules:**
- Tokenize: `re.findall(r'\b[a-z]+\b', text.lower())`
- Count matches in `positive_words` and `negative_words` sets
- If `total_sentiment_words == 0` → polarity = 0.0 (neutral)
- Output range: -1.0 (very negative) to +1.0 (very positive)

**Example:**
- "NVIDIA beats earnings with strong growth"
- Positive matches: "beats", "strong" → 2
- Negative matches: none → 0
- Total = 2
- Polarity = (2 - 0) / 2 = 1.0

---

### Step detail: daily sentiment aggregation (Step 8)

`SentimentProcessor.aggregate_daily()` applies `MIN_HEADLINES_PER_DAY` threshold:

| Headline count | Output |
|----------------|--------|
| ≥ 3 | Mean of all polarity scores |
| < 3 | None (insufficient data) |

**Rationale:** Heuristic threshold to reduce noise in low-coverage assets. 3 is a pragmatic choice — enough to smooth outliers, low enough to maintain coverage. This is not a statistical claim; it is an engineering heuristic.

---

### Step detail: rolling normalization (sentiment + momentum)

Both sentiment and momentum use identical rolling z-score logic with 20-day windows.

**State:** `history[ticker] = deque(maxlen=30)` (stores last 30 days, window=20, buffer=10)

**Process per asset per day:**
1. Retrieve last `WINDOW_DAYS` of history (excluding today)
2. If fewer than `MIN_VALID_DAYS` → return None
3. Calculate mean and standard deviation
4. If standard deviation == 0 → return 0.0 (no variation)
5. Return `(today_value - mean) / std`

**Parameters:**

| Parameter | Sentiment | Momentum |
|-----------|-----------|----------|
| `WINDOW_DAYS` | 20 | 20 |
| `MIN_VALID_DAYS` | 10 | 10 |
| `MAX_HISTORY_DAYS` | 30 | 30 |

**Why 20 days?** Balances sensitivity and stability; matches Tetlock (2007) and finance literature.

**Why classical z-score?** Simple, interpretable, sufficient for divergence detection. Extreme outliers (>2.2σ) have confidence reduced in Layer 4.

**Clarification on MIN_VALID_DAYS = 10:**
- With 10 valid days, z-score calculation begins on day 10, **not** day 20
- This is intentional: 10 days provides a statistically plausible mean and variance
- The specification previously contained contradictory text ("First 19 days → None"). That was an error. The correct behavior is:
  - Days 1-9: insufficient history → None
  - Day 10 onward: sufficient history (≥10 days) → z-score calculated
  - Day 20 onward: full 20-day window

---

### Step detail: momentum (Steps 6-7)

`MomentumProcessor.calculate_daily_return()`:

**Formula:** `daily_return = (price_today - price_yesterday) / price_yesterday`

**Rules:**
- If `price_yesterday == 0` → return 0.0 (defensive)
- If no previous price (first day) → return None
- Do NOT interpolate missing prices

**Alternative considered:** Log returns: `log(price_today / price_yesterday)`. Rejected for MVP because simple returns are more interpretable for non-quant users. Post-MVP, evaluate whether log returns improve signal stability.

**State:** `history[ticker] = deque(maxlen=30)` (stores last 30 days)

---

### Step detail: daily finalization (Steps 8-9)

Called once per day after all headlines and prices are processed.

**Sentiment path:**
1. Retrieve all buffered headlines for (ticker, trading_day)
2. If count < `MIN_HEADLINES_PER_DAY` → `sentiment_raw = None`
3. Else → `sentiment_raw = mean(scores)`
4. Append to sentiment history (deque)
5. Compute `sentiment_zscore` via rolling normalization

**Momentum path:**
1. Retrieve `daily_return` for (ticker, trading_day) from price processor
2. Append to momentum history (deque)
3. Compute `momentum_zscore` via rolling normalization

**Output structure:**
```python
{
    "NVDA": {
        "2026-06-02": {"sentiment_zscore": 0.45, "momentum_zscore": 0.02}
    }
}
```

---

## Output Schema

| Field | Type | Description |
|-------|------|-------------|
| ticker | string | Asset identifier |
| date | string (YYYY-MM-DD) | Trading day |
| sentiment_zscore | float or null | Normalized sentiment (rolling z-score, available from day 10) |
| momentum_zscore | float or null | Normalized momentum (rolling z-score, available from day 10) |

**Structure:** Nested dictionary `{ticker: {date: {sentiment_zscore, momentum_zscore}}}`

**Field rules:**
- Both values are float or None
- None means: insufficient data (<10 days history) or invalid input
- Day 10 onward: z-scores are available (may still be None if standard deviation is zero)
- Layer 4 handles None by producing NULL NDI

---

## Parameter Table

| Parameter | Value | Scope | Defined in |
|-----------|-------|-------|------------|
| `MIN_HEADLINES_PER_DAY` | 3 | Daily sentiment aggregation (heuristic) | `layer3_config.py` |
| `SENTIMENT_WINDOW_DAYS` | 20 | Rolling normalization window | `layer3_config.py` |
| `MIN_VALID_DAYS_SENTIMENT` | 10 | Minimum history for valid z-score | `layer3_config.py` |
| `MOMENTUM_WINDOW_DAYS` | 20 | Rolling normalization window | `layer3_config.py` |
| `MIN_VALID_DAYS_MOMENTUM` | 10 | Minimum history for valid z-score | `layer3_config.py` |
| `DAILY_CUTOFF_HOUR_ET` | 16 (4:00 PM) | Headline time alignment | `layer3_config.py` |
| `MIN_ALIAS_LENGTH` | 3 | Entity resolution filter | `layer3_config.py` |
| `MAX_HISTORY_DAYS` | 30 | Buffer size (window + margin) | Module constants |
| `HEADLINE_REQUIRED_KEYS` | `{headline_text, published_at, ingested_at, url_param}` | Input validation | `layer3_orchestrator.py` |
| `PRICE_REQUIRED_KEYS` | `{ticker, date, adj_close}` | Input validation | `layer3_orchestrator.py` |

---

## State Management

### Stateful components

| Component | State | Data structure | Persistence | Reset behavior |
|-----------|-------|----------------|-------------|----------------|
| `SentimentProcessor` | `history[ticker]` | `deque(maxlen=30)` of `(date, raw)` | Memory only | Loss of historical window on restart |
| `MomentumProcessor` | `history[ticker]` | `deque(maxlen=30)` of `(date, return)` | Memory only | Loss of historical window on restart |
| `Orchestrator` | `_last_price[ticker][date]` | `dict` of `date → price` | Memory only | Rebuilds from prices |
| `Orchestrator` | `_headline_buffer[ticker][date]` | `dict` of `date → list[scores]` | Memory only | Cleared after each `finalize_day()` |

**Design decision:** Layer 3 does NOT persist to disk in MVP because it can recompute from Layer 2 on each restart (prices are immutable, headlines are replayable). For production with 500+ tickers, add checkpointing to avoid recomputing 20-day windows on every restart.

### Deque configuration

```python
from collections import deque

self.history[ticker] = deque(maxlen=MAX_HISTORY_DAYS)  # 30 days
```

When appending beyond 30, oldest entries drop automatically. This bounds memory usage to O(tickers × 30).

---

## Integration with Layer 2 (Input Contract)

Layer 3 expects from Layer 2:

| Data | Table | Required Fields | Notes |
|------|-------|-----------------|-------|
| Headlines | `raw.news_headlines` | `headline`, `published_at`, `ingested_at`, `source_asset` (URL param) | `published_at` may be NULL; `ingested_at` is fallback |
| Prices | `raw.prices` | `ticker`, `date`, `adj_close` | Need at least 10 days of history for z-score calculation |

**Query pattern (daily batch):**
- Headlines: `WHERE ingested_at >= yesterday AND ingested_at < today`
- Prices: `WHERE date >= (today - 30 days) AND ticker IN (monitored_assets)`

Layer 3 does **not** write to database in MVP. Output is in-memory to Layer 4.

---

## Integration with Layer 4 (Output Contract)

Layer 4 expects from Layer 3:

```python
{
    "NVDA": {
        "2026-06-02": {"sentiment_zscore": 0.45, "momentum_zscore": 0.02}
    }
}
```

- Layer 3 runs **before** Layer 4 in the daily batch
- Output passed directly to `layer4_orchestrator.process_batch()`
- No intermediate storage (files or database)

---

## Quality Contract

| Metric | Target | Measurement Method | Responsibility |
|--------|--------|-------------------|----------------|
| Entity precision | >95% | Manual sample of 200 headlines | `layer3_entity.py` |
| Entity recall | >85% | Percentage of relevant headlines that match | `layer3_entity.py` |
| False positives | <2% | Headlines assigned to wrong ticker | `layer3_entity.py` |
| Daily sentiment coverage | >80% | Days with ≥3 headlines per asset | `layer3_sentiment.py` |
| Price completeness | >99% | Trading days with valid price records | Layer 2 + `layer3_momentum.py` |
| Determinism | 100% | Same inputs → same outputs | All modules |
| Lexicon accuracy | 65-75% | Against human-labeled sample | `layer3_sentiment.py` |

---

## Edge Cases and Handling

| Edge Case | Detection | Output | Owner |
|-----------|-----------|--------|-------|
| Headline with no ticker match | `resolve()` returns empty list | Discard headline, log warning | EntityResolver |
| Fewer than 3 headlines per day | `len(headlines) < MIN_HEADLINES_PER_DAY` | `sentiment_raw = None` | SentimentProcessor |
| First 9 days of data | History length < 10 | `sentiment_zscore = None`, `momentum_zscore = None` | Rolling normalization |
| Day 10 onward | History length ≥ 10 | Z-score calculated (with available window) | Rolling normalization |
| Missing price for a day | No price record in batch | `daily_return = None` (not interpolated) | MomentumProcessor |
| Price exactly 0 | Division by zero | `daily_return = 0.0` (defensive) | MomentumProcessor |
| Standard deviation = 0 | All historical values identical | `zscore = 0.0` (neutral) | Rolling normalization |
| `published_at` is NULL | Timestamp missing | Use `ingested_at` as fallback | TimeAligner |
| Weekend/holiday timestamp | Saturday/Sunday | TimeAligner returns calendar day; caller maps if needed | TimeAligner (owns assignment) |
| Alias shorter than 3 chars | `len(alias) < MIN_ALIAS_LENGTH` | Skip alias entirely | EntityResolver |
| Multiple tickers same alias | Duplicate in alias file | Last one wins (documented, acceptable for MVP) | EntityResolver |
| Generic alias like "Apple" alone | Broad matching | Omitted from alias file; precision prioritized | EntityResolver |

---

## Known Risks

| Risk | Impact | Mitigation | Owner |
|------|--------|------------|-------|
| Lexicon doesn't understand context (e.g., "miss" as earnings miss vs想念) | False sentiment polarity | Accept for MVP; post-MVP: add context rules or fine-tuned model | Product |
| Sarcasm or ironic headlines | Inverted sentiment signal | Accept for MVP; document limitation | Product |
| Duplicate headlines across sources | Overweighting of same news | Layer 2 deduplication (headline_hash) | Layer 2 |
| Ambiguous aliases ("Apple" vs "Apple supplier") | Entity resolution errors | URL param priority helps; conservative alias file (no generic "Apple") | EntityResolver |
| Uneven coverage across assets (NVDA vs BTC-USD) | Bias toward large caps | Document coverage in pilot offer | Product |
| UTC-4 DST failure | Incorrect trading day assignment for 2 weeks/year | Accept for MVP; post-MVP use `zoneinfo` | TimeAligner |
| No disk persistence on restart | Loss of 10-30 day history | Accept for MVP (recomputable from Layer 2 in <5 min) | Architecture |
| Word-boundary false positives ("Amazon rainforest" → AMZN) | Entity resolution errors | Accept for MVP; conservative alias file; post-MVP add negative alias lists | EntityResolver |
| Simple returns vs log returns | Small bias in momentum | Accept for MVP; post-MVP evaluate log returns | MomentumProcessor |

---

## Computational Budget (MVP - Estimates, Not Guarantees)

| Metric | Target (estimated) | Notes |
|--------|---------------------|-------|
| Headlines processed per day | ~10,000 | 6 sources × 4-6 updates × 5 assets |
| Supported tickers | 5 (MVP) | Scales to 500 post-MVP with same logic |
| Layer 3 batch runtime | Target <5 minutes | Not yet measured; lexicon scoring is O(n); history deques are O(1) append |
| Maximum memory | <500 MB (estimated) | History buffers: 5 tickers × 30 days × 2 (sentiment+momentum) |
| Storage (persistence) | None | No disk writes in MVP |

**Note:** Runtime targets are estimates. Actual performance will be measured during implementation and may require optimization.

---

## Setup Prerequisites

Before running Layer 3:

1. **Download Loughran-McDonald lexicon:**
   - Source: https://sraf.nd.edu/loughranmcdonald-master-dictionary/
   - Format: CSV with columns `word`, `sentiment`
   - Save to: `data/lexicons/loughran_mcdonald/loughran_mcdonald.csv`

2. **Create alias file:**
   - Path: `config/entity_aliases.json`
   - Include all tickers from Layer 2 `monitored_assets`
   - **Conservative approach:** Prefer specific aliases ("Apple Inc") over generic ones ("Apple")
   - Minimum alias length: 3 characters

3. **Verify Layer 2 data availability:**
   - Prices: at least 10 days of history for each ticker (20 days recommended)
   - Headlines: at least 10 days of coverage for sentiment normalization

---

## Design Decisions (Explicitly Documented)

| Decision | Rejected Alternative | Rationale |
|----------|---------------------|-----------|
| 20-day rolling window | 5, 10, 60 days | Balance between sensitivity and stability; matches Tetlock (2007) |
| MIN_VALID_DAYS = 10 (not 20) | 20 days | 10 days provides statistically plausible mean; earlier signal availability |
| Classical z-score | Robust z-score (MAD) | Simplicity; extreme outliers handled in Layer 4 (inverted-U confidence) |
| Min 3 headlines per day (heuristic) | 1 or 5 | Pragmatic noise reduction; not a statistical claim |
| URL param first, then alias | Alias-only or ML-based | URL param is high precision; alias provides recall |
| Conservative aliases (no generic "Apple") | Broad aliases with post-filtering | Precision prioritized over recall for MVP |
| Word-boundary matching | Fuzzy matching (Levenshtein) | Simpler, deterministic, sufficient for MVP |
| UTC-4 for ET (no DST) | `zoneinfo` or `pytz` | MVP simplification; DST added post-MVP |
| No disk persistence | Checkpointing to database | MVP can recompute from Layer 2 in <5 minutes |
| Memory-only state with `deque` | Redis or file-backed | Acceptable for 5 tickers × 30 days |
| TimeAligner owns trading day | Caller ownership | Single source of truth |
| Simple returns for momentum | Log returns | More interpretable for non-quant users; post-MVP evaluate |
| Input validation checks Layer 2 fields | Checks Layer 3 outputs | Validation is for inputs, not outputs |

---

## Layer 3 Status: IMPLEMENTATION READY (MVP Production Candidate)

> Deterministic. Two-phase entity resolution with conservative aliases (precision > recall). Lexicon-based sentiment. Simple daily returns (log returns considered, deferred). Rolling 20-day z-scores (min 10 valid days, not 20). Centralized input validation (checks Layer 2 fields, not Layer 3 outputs). Memory-only state with deques. TimeAligner owns trading day assignment. Edge cases documented. Known risks acknowledged. Performance targets are estimates, not guarantees. Ready for implementation.

---

**SignalIQ** 🔹

*Layer 3 transforms headlines → sentiment_zscore. Prices → momentum_zscore. No ML. Deterministic. Ready for Layer 4 consumption.*
