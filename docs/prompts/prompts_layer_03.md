# SignalIQ Layer 3: Final Production Prompts (with Word Boundary Fix)

## Word Boundary Improvement

**Issue:** `\b` fails for aliases containing punctuation like `AT&T`.

**Fix:** Use `(?<!\w)` (not preceded by word char) and `(?!\w)` (not followed by word char) instead of `\b`.

**Before:** `rf"\b{re.escape(alias.lower())}\b"`

**After:** `rf"(?<!\w){re.escape(alias.lower())}(?!\w)"`

This handles:
- `AT&T` ✓
- `Apple Inc.` ✓  
- `Berkshire Hathaway` ✓
- `NVIDIA` ✓

---

## Prompt 1: Configuration + Entity Resolution (UPDATED)

```
Build the foundation for SignalIQ Layer 3.

Create TWO modules:

MODULE A: `layers/layer3_config.py`
- A dataclass `Layer3Config` with ALL parameters frozen for MVP:
  - min_headlines_per_day: int = 3
  - sentiment_window_days: int = 20
  - min_valid_days_sentiment: int = 10  # Requires 10 PRIOR observations
  - momentum_window_days: int = 20
  - min_valid_days_momentum: int = 10   # Requires 10 PRIOR observations
  - daily_cutoff_hour_et: int = 16      # 4:00 PM ET
  - min_alias_length: int = 3
  - max_history_days: int = 30
  - alias_file_path: str = "config/entity_aliases.json"
  - lexicon_path: str = "data/lexicons/loughran_mcdonald/loughran_mcdonald.csv"

- A singleton instance `CONFIG = Layer3Config()`

MODULE B: `layers/layer3_entity.py`
- Class `EntityResolver` with:
  - `__init__(self, alias_file_path: str, min_alias_length: int = 3)`
    - Loads JSON alias file (format: `{"TICKER": ["alias1", "alias2"]}`)
    - Builds reverse index `_alias_to_ticker`
    - Filters aliases shorter than min_alias_length
    - **IMPORTANT:** Store aliases as-is for regex building
  - `resolve_by_url_param(self, url_param: str | None) -> str | None`
    - If url_param exists and matches a ticker key → return ticker
    - Else return None
  - `resolve_by_alias(self, normalized_headline: str) -> set[str]`
    - Build pattern: `rf"(?<!\w){re.escape(alias.lower())}(?!\w)"`
    - This uses negative lookbehind/lookahead for word boundaries
    - **Why not \b:** `\b` fails for aliases with punctuation like "AT&T"
    - `(?<!\w)` and `(?!\w)` work correctly for all alphanumeric + underscore boundaries
    - Case-insensitive matching using `re.IGNORECASE`
    - Returns set of matching tickers
  - `resolve(self, normalized_headline: str, url_param: str | None = None) -> list[str]`
    - Phase 1: try url_param → if found, return [ticker]
    - Phase 2: alias matching → return sorted list
  - `get_all_tickers(self) -> list[str]` - returns all known tickers

- Helper function `normalize_headline(text: str) -> str`:
  - Lowercase
  - Collapse multiple spaces
  - Strip leading/trailing whitespace

- **IMPORTANT:** All dates in Layer 3 are stored as `date` objects (from `datetime.date`). String conversion only at input/output boundaries.

Add docstrings, type hints, and example usage in `if __name__ == "__main__"`.
```

---

## Prompt 2: Sentiment Processor (UNCHANGED)

```
Build the sentiment processor for SignalIQ Layer 3.

Create `layers/layer3_sentiment.py` with:

1. Class `LoughranMcDonaldLexicon`:
   - `__init__(self, lexicon_path: str)`
     - Loads CSV with columns "word", "sentiment"
     - Populates `self.positive: set[str]` and `self.negative: set[str]`
     - Raises FileNotFoundError if lexicon file missing
   - `score(self, text: str) -> tuple[int, int, int]`
     - Tokenize: `re.findall(r'\b[a-z]+\b', text.lower())`
     - Count positive, negative matches
     - Returns (pos_count, neg_count, total)
   - `polarity(self, text: str) -> float`
     - pos, neg, total = self.score(text)
     - If total == 0: return 0.0
     - Return (pos - neg) / total

2. Class `SentimentProcessor`:
   - `__init__(self, lexicon: LoughranMcDonaldLexicon, config: Layer3Config)`
   - `score_headline(self, headline_text: str) -> float`
     - Returns lexicon.polarity(headline_text)
   - `aggregate_daily(self, scores: list[float]) -> float | None`
     - If len(scores) < config.min_headlines_per_day: return None
     - Return mean(scores)
   - `add_to_history(self, ticker: str, dt: date, sentiment_raw: float | None)`
     - dt is `date` object (YYYY-MM-DD)
     - Stores (dt, sentiment_raw) as tuple (date, float)
     - Uses deque with maxlen=config.max_history_days
     - Only stores if sentiment_raw is not None
   - `get_rolling_zscore(self, ticker: str, dt: date, current_raw: float | None) -> float | None`
     - **CRITICAL:** Calculates z-score using history EXCLUDING the current date
     - Requires min_valid_days_sentiment = 10 PRIOR observations (not including today)
     - If current_raw is None: return None
     - Get history entries where entry.dt < dt (strictly before)
     - Take last config.sentiment_window_days entries
     - If len(history) < config.min_valid_days_sentiment: return None
     - Calculate mean and std of historical raw values
     - If std == 0: return 0.0
     - Return (current_raw - mean) / std
   - `get_history_length(self, ticker: str) -> int` (for testing)

3. Constants:
   - Import CONFIG from layer3_config
   - Import `date` from `datetime`

4. Example usage showing:
   - FIRST VALID Z-SCORE APPEARS ON DAY 11 (requires 10 PRIOR observations)
   - Days 1-10: insufficient history (0-9 prior days) → None
   - Day 11: sufficient (10 prior days) → z-score calculated

Add docstrings, type hints, and error handling for missing lexicon file.
```

---

## Prompt 3: Momentum Processor (UNCHANGED)

```
Build the momentum processor for SignalIQ Layer 3.

Create `layers/layer3_momentum.py` with:

1. Class `MomentumProcessor`:
   - `__init__(self, config: Layer3Config)`
     - Stores config
     - Initializes `self.return_history: dict[str, deque] = {}` for (date, return) pairs
     - Initializes `self.price_history: dict[str, dict[date, float]] = {}` for price lookup
     - **CRITICAL - Prevents look-ahead bias:** 
       - `self.pending_returns: dict[str, dict[date, float]] = {}` for returns not yet moved to history
   - `calculate_daily_return(self, price_today: float, price_yesterday: float) -> float`
     - If price_yesterday == 0: return 0.0 (defensive)
     - Return (price_today - price_yesterday) / price_yesterday
   - `add_price(self, ticker: str, dt: date, adj_close: float) -> float | None`
     - dt is `date` object
     - Store price in `self.price_history[ticker][dt] = adj_close`
     - Find previous price: `max(d for d in self.price_history[ticker].keys() if d < dt)`
     - If no previous price exists → return None (first day)
     - Else: calculate daily_return using current and previous price
     - **Store return in `pending_returns[ticker][dt] = daily_return` (NOT in history yet)**
     - Return daily_return
   - `commit_pending_returns(self, ticker: str, dt: date) -> None`
     - **Called by orchestrator during finalize_day**
     - Moves returns from `pending_returns` to `return_history` for all dates <= dt
     - This ensures historical baseline does NOT include the current day's return
   - `get_return_for_date(self, ticker: str, dt: date) -> float | None`
     - Check `pending_returns` first, then `return_history`
     - Returns None if not found
   - `get_rolling_zscore(self, ticker: str, dt: date, current_return: float | None) -> float | None`
     - **CRITICAL:** Calculates z-score using history EXCLUDING the current date
     - Requires min_valid_days_momentum = 10 PRIOR observations
     - If current_return is None: return None
     - Get return_history entries where entry.dt < dt (strictly before)
     - Take last config.momentum_window_days entries
     - If len(history) < config.min_valid_days_momentum: return None
     - Calculate mean and std of historical returns
     - If std == 0: return 0.0
     - Return (current_return - mean) / std
   - `get_history_length(self, ticker: str) -> int` (for testing)
   - `has_previous_price(self, ticker: str, dt: date) -> bool` (for testing)

2. Constants:
   - Import CONFIG from layer3_config
   - Import `date` from `datetime`

3. Example usage showing:
   - FIRST VALID Z-SCORE APPEARS ON DAY 11 (requires 10 PRIOR observations)
   - Adding first price → returns None, stores price
   - Adding second price → finds nearest prior date, stores in pending_returns
   - During finalize_day, returns committed to history

Add docstrings and type hints.
```

---

## Prompt 4: Orchestrator (UNCHANGED)

```
Build the main orchestrator for SignalIQ Layer 3.

Create `layers/layer3_orchestrator.py` with:

1. Import from:
   - `layer3_config` (CONFIG)
   - `layer3_entity` (EntityResolver, normalize_headline)
   - `layer3_sentiment` (LoughranMcDonaldLexicon, SentimentProcessor)
   - `layer3_momentum` (MomentumProcessor)
   - `collections` (defaultdict)
   - `datetime` (datetime, date)
   - `re`

2. Class `TimeAligner`:
   - `to_eastern(self, dt: datetime) -> datetime`
     - Simplified: subtract 4 hours (UTC-4) for MVP
     - **WARNING:** This fails during DST (mid-March to early November when US is UTC-4).
     - Post-MVP: use `zoneinfo` or `pytz`
   - `get_trading_day(self, timestamp: datetime, cutoff_hour: int = 16) -> date`
     - Convert to ET using `to_eastern`
     - If time < cutoff_hour → return date of same day
     - Else → return date of next day (add 1 day)
     - If timestamp has no timezone, assume UTC
     - Returns `date` object (not string)

3. Class `Layer3Orchestrator`:
   - `__init__(self, config = CONFIG)`
     - Loads lexicon (handle FileNotFoundError with clear message)
     - Creates EntityResolver, SentimentProcessor, MomentumProcessor, TimeAligner
     - Initializes:
       - `_headline_buffer: dict[str, dict[date, list[float]]]` (ticker → date → scores)
       - `_last_finalized_date: date | None` (tracks chronological order)
   - `validate_batch_input(self, headlines: list[dict], prices: list[dict]) -> None`
     - HEADLINE_REQUIRED_KEYS = {"headline_text", "published_at", "ingested_at", "url_param"}
       - **Note:** `published_at` key must exist, value may be None
     - PRICE_REQUIRED_KEYS = {"ticker", "date", "adj_close"}
     - Raise ValueError with details if any missing
   - `process_headline(self, headline_text: str, published_at: datetime | None, ingested_at: datetime, url_param: str | None = None) -> None`
     - Determine trading day using TimeAligner (fallback to ingested_at if published_at None)
     - Returns `date` object
     - Normalize headline
     - Resolve tickers using EntityResolver
     - For each ticker:
       - Score sentiment
       - Add to buffer: `_headline_buffer[ticker][trading_day].append(score)`
   - `process_price(self, ticker: str, dt: date, adj_close: float) -> None`
     - Call momentum_processor.add_price(ticker, dt, adj_close)
     - This stores price and pending return (or None for first day)
   - `finalize_day(self, dt: date, tickers: list[str] | None = None) -> dict`
     - PRECONDITION: dt must be a `date` object
     - PRECONDITION: Must be called in chronological order (dt increasing)
     - If _last_finalized_date exists and dt <= _last_finalized_date: raise ValueError
     - If tickers None, use entity_resolver.get_all_tickers()
     - **Step 1: Commit pending returns to history (prevents look-ahead bias)**
       - For each ticker in tickers:
         - momentum.commit_pending_returns(ticker, dt)
     - **Step 2: Process each ticker**
       - For each ticker:
         - **Sentiment path (CRITICAL ORDERING):**
           1. Get scores from buffer for this date (pop them)
           2. daily_raw = sentiment.aggregate_daily(scores) or None
           3. Calculate sentiment_zscore using `get_rolling_zscore` 
              (uses history EXCLUDING today, requires 10 PRIOR days)
           4. THEN add_to_history(ticker, dt, daily_raw)
         - **Momentum path:**
           1. Get daily_return = momentum.get_return_for_date(ticker, dt)
           2. Calculate momentum_zscore using `get_rolling_zscore`
              (uses history EXCLUDING today, requires 10 PRIOR days)
         - Build result dict
     - **Step 3: Cleanup**
       - Clear `_headline_buffer` for this date
       - Update `_last_finalized_date = dt`
     - Return `{ticker: {dt.isoformat(): {"sentiment_zscore": float|None, "momentum_zscore": float|None}}}`

4. Example usage showing:
   - FIRST VALID Z-SCORE ON DAY 11 (requires 10 PRIOR observations)
   - Chronological finalization enforced
   - Pending returns committed before z-score calculation

Add docstrings and type hints.
```

---

## Prompt 5: Integration Test Suite (UPDATED)

```
Build the integration test suite for SignalIQ Layer 3.

Create `tests/test_layer3.py` with the following test cases:

TEST 1: Configuration Loading
- Verify CONFIG has correct default values
- Verify min_valid_days = 10 (requires 10 PRIOR observations)

TEST 2: Entity Resolution with Proper Word Boundaries
- Create temp alias file with test data including:
  - "AT&T" (punctuation)
  - "Apple Inc." (period)
  - "NVIDIA" (normal)
- Test url_param resolution (exact match)
- Test alias matching with `(?<!\w)` and `(?!\w)` word boundaries
- Verify "AT&T" matches "AT&T stock rises" but NOT "ATT" or "AT&T123"
- Verify "Apple Inc." matches "Apple Inc. announces" but NOT "Apple" alone
- Test multiple tickers ("Apple Inc. and Microsoft")
- Test filtering of short aliases (<3 chars)
- Clean up temp file

TEST 3: Lexicon Loading
- Test loading valid lexicon file
- Test missing file raises FileNotFoundError
- Test polarity scoring on sample headlines

TEST 4: Sentiment Processor
- Test score_headline returns float between -1 and 1
- Test aggregate_daily with ≥3 scores → returns mean
- Test aggregate_daily with <3 scores → returns None
- Test rolling z-score: 10 PRIOR days required
  - Days 1-10: add history, z-score returns None (0-9 prior days)
  - Day 11: calculate z-score using days 1-10 (10 prior days) → returns value
  - THEN add day 11 to history
  - Verify day 11's own value does NOT contaminate baseline

TEST 5: Momentum Processor
- Test calculate_daily_return with valid prices
- Test add_price first day returns None
- Test add_price second day finds nearest prior date
- Test pending_returns vs return_history separation
- Test commit_pending_returns moves returns to history
- Test get_return_for_date retrieves from pending first, then history
- Test rolling z-score: 10 PRIOR days required (same as sentiment)

TEST 6: Time Aligner
- Test before 4:00 PM ET → same day
- Test after 4:00 PM ET → next day
- Test published_at None → uses ingested_at
- Document DST limitation (test passes but known issue)

TEST 7: Orchestrator - Headline Processing
- Process headline, verify buffer contains score
- Process headline with URL param, verify entity resolution
- Process headline with no ticker match → discarded (no error)

TEST 8: Orchestrator - Price Processing
- Process first price → verify stored, pending_returns empty
- Process second price → verify pending_returns contains return
- Verify commit not yet called

TEST 9: Orchestrator - Daily Finalization with 10 PRIOR Days
- Simulate 11 days of data for NVDA:
  - Days 1-10: sentiment_zscore = None, momentum_zscore = None
  - Day 11: both z-scores become non-None
- Verify pending returns committed BEFORE z-score calculation
- Verify chronological order enforcement (out-of-order raises error)
- Verify z-score on day 11 does NOT include day 11's own value
- Verify output structure: dates as ISO strings

TEST 10: Integration - Full Pipeline
- Create sample headlines and prices for 20 days
- Run through complete orchestrator in chronological order
- Verify determinism: same input → same output

TEST 11: Edge Cases
- Empty headline list
- Empty price list
- published_at key exists with None value (valid)
- published_at key missing (invalid → raises error)
- Missing url_param (uses alias matching only)
- Alias with special characters (AT&T, Apple Inc.)

TEST 12: Batch Input Validation
- Test missing required keys raise ValueError
- Test published_at key missing raises error
- Test published_at key exists with None passes validation
- Test valid inputs pass

TEST 13: Look-Ahead Bias Prevention (Critical)
- Direct test of get_rolling_zscore with pending_returns:
  - Add price for day 10 → pending_returns has return, history empty
  - Call get_rolling_zscore for day 10 → must return None (no prior history)
  - Commit pending for day 10 → history now contains day 10
  - Call get_rolling_zscore for day 11 with new return → uses day 10 only (1 prior, needs 10)
  - Verify day 10's own return was never used in its own baseline

TEST 14: Chronological Order Enforcement
- Create orchestrator
- Finalize day 2026-06-02
- Attempt to finalize day 2026-06-01 (earlier) → raise ValueError
- Verify error message indicates chronological violation

TEST 15: Date Handling Consistency
- Verify all internal operations use `date` objects
- Verify output converts to ISO-8601 strings
- Verify string comparison not used internally

TEST 16: Alias Word Boundary Edge Cases
- Direct test of pattern `(?<!\w){alias}(?!\w)`:
  - "AT&T" matches "AT&T reports earnings"
  - "AT&T" does NOT match "ATT"
  - "AT&T" does NOT match "AT&T123"
  - "Apple Inc." matches "Apple Inc. announces"
  - "Apple Inc." does NOT match "Apple"

Use pytest style or simple assert functions. Include setup/teardown for temp files. Print "ALL TESTS PASSED" at the end.
```

---

## Summary of Changes

| Component | Change |
|-----------|--------|
| EntityResolver | `\b` → `(?<!\w)` and `(?!\w)` for proper punctuation handling |
| Tests | Added Test 16 for word boundary edge cases |
| All other modules | Unchanged from previous version |

---

## Word Boundary Pattern Reference

```python
# OLD (fails for AT&T, Apple Inc., etc.)
pattern = rf"\b{re.escape(alias.lower())}\b"

# NEW (works for all alphanumeric + punctuation)
pattern = rf"(?<!\w){re.escape(alias.lower())}(?!\w)"
```

**How it works:**
- `(?<!\w)` = not preceded by a word character (letter, digit, underscore)
- `(?!\w)` = not followed by a word character
- This correctly handles boundaries even when aliases contain punctuation

---

**SignalIQ** 🔹

*Layer 3 prompts final. Word boundaries using `(?<!\w)` and `(?!\w)`. Handles AT&T, Apple Inc., and all punctuation-containing aliases. Ready for implementation.*