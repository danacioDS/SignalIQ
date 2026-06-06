# SignalIQ Layer 3 — Transcript: Build Documentation

## Overview

Layer 3 (NLP intelligence engine) transforms raw headlines and prices into normalised z-scores that Layer 4 consumes to compute NDI. Built as 5 Python modules with zero external dependencies (standard library only), plus 1 architecture doc and 1 test suite.

**Bottom line:** 5 modules (731 lines total), 16 tests, 100+ checks, 0 external packages.

---

## Module Architecture

```
layer3_config.py          Frozen dataclass — all MVP parameters in one place
layer3_entity.py          Two-phase entity resolution (URL param → alias regex)
layer3_sentiment.py       Loughran-McDonald lexicon scoring + rolling z-score
layer3_momentum.py        Daily return calculation + rolling z-score
layer3_orchestrator.py    Pipeline orchestration, time alignment, batch output
```

**Dependency direction:** `config → entity → sentiment → momentum → orchestrator`. Nothing imports backwards.

---

## Module 1: `layer3_config.py` (25 lines)

Frozen dataclass `Layer3Config` with a singleton `CONFIG` instantiated at import time. Every tunable parameter lives here — no magic numbers in any other module.

| Parameter | Value | Purpose |
|-----------|-------|---------|
| `min_headlines_per_day` | 3 | Heuristic threshold for daily sentiment aggregation |
| `sentiment_window_days` | 20 | Rolling z-score window |
| `min_valid_days_sentiment` | 10 | Minimum history before z-score activates |
| `momentum_window_days` | 20 | Rolling z-score window |
| `min_valid_days_momentum` | 10 | Minimum history before z-score activates |
| `daily_cutoff_hour_et` | 16 (4 PM) | Headline → trading day cutoff |
| `min_alias_length` | 3 | Entity resolution filter |
| `max_history_days` | 30 | Deque capacity (window + safety margin) |
| `alias_file_path` | `config/entity_aliases.json` | Entity resolution data |
| `lexicon_path` | `data/lexicons/loughran_mcdonald/...` | Sentiment lexicon CSV |

**Design decision:** Frozen dataclass prevents accidental mutation. Tests override parameters via `dataclasses.replace()`.

---

## Module 2: `layer3_entity.py` (101 lines)

Two-phase entity resolution in `EntityResolver`:

**Phase 1 — URL parameter (high precision):** If the caller provides a `url_param` (e.g. a ticker tag from Yahoo Finance), compare it directly against known ticker keys. If matched, return immediately — skip Phase 2 entirely. This is the fast path for ticker-tagged feeds.

**Phase 2 — Alias matching (recall-oriented):** Scans every known alias against the normalised headline using regex with `(?<!\w)` / `(?!\w)` lookarounds instead of `\b`. This handles punctuation-containing aliases (e.g. `AT&T`) that `\b` would fail on. Matching is case-insensitive. Returns **all** matching tickers (zero, one, or many).

**Alias loading:** Reads `config/entity_aliases.json` at construction time. Filters out aliases shorter than `min_alias_length`. Builds both forward (`ticker → [aliases]`) and reverse (`alias → ticker`) maps.

**Design constraints:**
- Precision > recall for MVP — generic aliases like `"Apple"` alone are intentionally omitted from the alias file to avoid false positives
- Aliases must have word-boundary isolation: `"AT&T"` matches `"at&t stock"` but not `"att"` or `"at&t123"`

---

## Module 3: `layer3_sentiment.py` (171 lines)

Two classes:

### `LoughranMcDonaldLexicon`
- Loads a CSV with `word` and `sentiment` columns (positive/negative)
- `polarity(text)` returns `(pos - neg) / total_tokens`, range [-1, 1]
- Tokenises with `re.findall(r'\b[a-z]+\b', text.lower())`
- Returns 0.0 for empty text or zero sentiment-bearing words

### `SentimentProcessor`
- `score_headline()` → delegates to lexicon polarity
- `aggregate_daily(scores)` → mean if `len >= min_headlines_per_day`, else None
- `add_to_history(ticker, date, raw)` → appends to `deque(maxlen=30)` (skips None)
- `get_rolling_zscore(ticker, date, current_raw)` — critical design:

**Rolling z-score logic:**
1. Collect prior observations strictly before `dt` from the deque
2. Truncate to last `sentiment_window_days` (20)
3. If fewer than `min_valid_days_sentiment` (10) → return None
4. Compute `mean` and `std` from the prior window
5. Return `(current_raw - mean) / std` (or 0.0 if std == 0)

**Key invariant:** The current day's value is never included in the baseline. This prevents look-ahead bias.

---

## Module 4: `layer3_momentum.py` (154 lines)

### `MomentumProcessor`

**Price → return pipeline:**
- `add_price(ticker, date, adj_close)` stores price and returns `(today - yesterday) / yesterday`
- First observation for a ticker always returns None (no prior price)
- Returns are stored in **pending** state — not committed to history until `commit_pending_returns()` is called
- This two-phase commit is the look-ahead bias prevention mechanism

**Two-phase commit design:**
```
add_price() stores price + computes return → placed in pending_returns{}
commit_pending_returns() → moves returns ≤ dt into return_history (deque)
```

This means rolling z-scores computed during `finalize_day()` always use a baseline that excludes the current day's return. The orchestrator calls `commit_pending_returns()` at the start of `finalize_day()`, then computes z-scores — the current day's return has been committed but is filtered out by the `d < dt` condition in `get_rolling_zscore()`.

**Identical z-score logic** to sentiment: same deque structure, same window/min_valid parameters.

---

## Module 5: `layer3_orchestrator.py` (280 lines)

The conductor — `Layer3Orchestrator` wires entity resolution, sentiment, and momentum together.

### Pipeline steps

| # | Step | Component | Detail |
|---|------|-----------|--------|
| 1 | Input validation | `validate_batch_input()` | Checks `HEADLINE_REQUIRED_KEYS` and `PRICE_REQUIRED_KEYS` |
| 2 | Time alignment | `TimeAligner.get_trading_day()` | UTC → ET with 4 PM cutoff; NULL `published_at` falls back to `ingested_at` |
| 3 | Entity resolution | `EntityResolver.resolve()` | URL param first, alias regex second |
| 4 | Sentiment scoring | `SentimentProcessor.score_headline()` | Lexicon polarity on normalised headline |
| 5 | Buffer | Headline buffer | `{ticker: {trading_day: [scores]}}` |
| 6 | Price processing | `MomentumProcessor.add_price()` | Store price, compute return (pending) |
| 7 | Daily finalization | `finalize_day()` | Commit returns, aggregate sentiment, compute both z-scores |

### `TimeAligner`
- Fixed UTC-4 offset (EDT). Documented limitation: undercounts by 1 hour during EST (Nov–Mar). Post-MVP: replace with `zoneinfo`
- 4 PM ET cutoff: headlines received at or after 4 PM ET are assigned to the next trading day

### `finalize_day()` sequence
1. Validate `dt` is a `date` object and chronological order is maintained
2. Commit pending returns for all tickers (moves returns to history)
3. For each ticker:
   - Pop buffered headline scores for this date → aggregate → compute sentiment z-score → add to history
   - Retrieve committed daily return → compute momentum z-score
4. Build output dict: `{ticker: {date.isoformat(): {sentiment_zscore, momentum_zscore, sentiment_raw, momentum_return}}}`
5. Clean up headline buffer for this date

### Chronological order enforcement
- `_last_finalized_date` tracks the most recent finalized day
- Calling `finalize_day()` with `dt <= last_finalized_date` raises `ValueError`
- Prevents accidental re-finalization or out-of-order processing

---

## Key Design Patterns

### 1. Look-ahead bias prevention
The two-phase commit in `MomentumProcessor` (pending → history) ensures rolling z-scores never include the current observation in the baseline. This is tested explicitly in `test_lookahead_bias_prevention()`.

### 2. Deterministic output
No randomness anywhere. Same headlines + same prices + same config = identical output every time. Tested in `test_full_pipeline_determinism()` which runs the entire pipeline twice and asserts identical results.

### 3. Memory-only state
Layer 3 does not persist to disk in MVP. All state lives in `deque(maxlen=30)` structures. On restart, z-scores recompute from Layer 2 data in <5 minutes. This is an explicit tradeoff: simplicity vs cold-start latency.

### 4. Input validation at boundary
`validate_batch_input()` checks Layer 2 fields (headline_text, published_at, ingested_at, url_param / ticker, date, adj_close), not Layer 3 outputs. This catches malformed data before any processing begins.

### 5. Standard library only
Zero external dependencies. CSV parsing uses `csv.DictReader`, regex uses `re`, data structures use `collections.deque`, JSON uses `json`. This keeps the MVP deployable with just `python3`.

---

## Test Suite

**File:** `tests/test_layer3.py` — 901 lines, 16 test functions, 100+ assertions.

| # | Test | Scope | Key Assertions |
|---|------|-------|----------------|
| 1 | `test_config_loading` | Config | All 10 default parameter values |
| 2 | `test_entity_resolution` | Entity | URL param, AT&T word boundaries, Apple Inc., multi-ticker, two-phase |
| 3 | `test_lexicon_loading` | Sentiment | Word loading, missing file, polarity scores (-1, 0, +1), empty text |
| 4 | `test_sentiment_processor` | Sentiment | Score aggregation, daily aggregation threshold, rolling z-score day 1-11 progression |
| 5 | `test_momentum_processor` | Momentum | Daily return calc, div-by-0, pending/commit lifecycle, rolling z-score day progression |
| 6 | `test_time_aligner` | Orchestrator | UTC→ET mapping, 4 PM cutoff, NULL fallback, DST limitation documentation |
| 7 | `test_orchestrator_headlines` | Orchestrator | URL param routing, alias matching, unresolved headline handling, buffer population |
| 8 | `test_orchestrator_prices` | Orchestrator | First price → no return, second price → pending, history empty before commit |
| 9 | `test_orchestrator_finalization` | Orchestrator | 11-day progression, z-score activation on day 11, out-of-order enforcement |
| 10 | `test_full_pipeline_determinism` | Integration | Full 20-day AAPL+MSFT pipeline run twice, identical output |
| 11 | `test_edge_cases` | Integration | NULL published_at, no url_param, AT&T special characters |
| 12 | `test_batch_input_validation` | Orchestrator | Valid passes, missing headline_text, missing published_at key, NULL published_at passes, missing ticker |
| 13 | `test_lookahead_bias_prevention` | Momentum | Z-score before commit = None, after commit still filters current day, day 12 activates |
| 14 | `test_chronological_order` | Orchestrator | First finalize succeeds, earlier date raises ValueError with chronological message |
| 15 | `test_date_handling` | Orchestrator | Date objects used throughout, ISO string output format |
| 16 | `test_alias_word_boundaries` | Entity | AT&T, Apple Inc., NVIDIA — exact, partial, concatenated, punctuation boundary cases |

---

## Integration Points

### Upstream (Layer 2)
- Headlines: `raw.news_headlines` — requires `headline_text`, `published_at` (or `ingested_at`), optionally `url_param` (from `source_asset`)
- Prices: `raw.prices` — requires `ticker`, `date`, `adj_close`
- Layer 3 does **not** read from the database directly — receives data in-memory from the caller

### Downstream (Layer 4)
- Output dict: `{ticker: {date.isoformat(): {sentiment_zscore, momentum_zscore, sentiment_raw, momentum_return}}}`
- Passed directly to `layer4_orchestrator.process_batch()` — no intermediate storage

### MVP integration flow
```
Layer 2 (DB) → Layer 3 (in-memory) → Layer 4 (in-memory)
```

---

## Configuration Checklist

Before running Layer 3:

1. **Loughran-McDonald lexicon CSV** at `data/lexicons/loughran_mcdonald/loughran_mcdonald.csv`
   - Columns: `word`, `sentiment` (positive/negative)
   - Source: https://sraf.nd.edu/loughranmcdonald-master-dictionary/

2. **Entity aliases JSON** at `config/entity_aliases.json`
   - Format: `{"NVDA": ["NVIDIA", "Nvidia Corp"], ...}`
   - Conservative aliases — prefer specific over generic

3. **At least 10 days** of price and headline data for each ticker (20 recommended)

---

## File Inventory

| File | Lines | Role |
|------|-------|------|
| `layers/layer3_config.py` | 25 | Frozen configuration dataclass |
| `layers/layer3_entity.py` | 101 | Entity resolution (URL param + alias regex) |
| `layers/layer3_sentiment.py` | 171 | Loughran-McDonald lexicon + rolling sentiment z-score |
| `layers/layer3_momentum.py` | 154 | Daily returns + rolling momentum z-score |
| `layers/layer3_orchestrator.py` | 280 | Pipeline orchestration, time alignment, output |
| `docs/architecture/Layer_03_arch.md` | 449 | Production specification |
| `tests/test_layer3.py` | 901 | 16 tests, 100+ checks |
| `config/entity_aliases.json` | 1 | Placeholder (empty — populated per-deployment) |

---

## Design Invariants

1. **No external packages** — standard library only (csv, re, json, collections.deque, math, datetime)
2. **No disk writes** — memory-only state, recomputable from Layer 2
3. **Deterministic** — same inputs always produce same outputs
4. **No look-ahead bias** — current day's value never contaminates the rolling baseline
5. **Chronological order required** — `finalize_day()` rejects out-of-order calls
6. **Input validation before processing** — malformed data caught at the boundary
7. **URL param beats alias** — high-precision fast path short-circuits recall-oriented matching
8. **Source metadata at ingestion time** — sentiment uses current config, not historical snapshots
