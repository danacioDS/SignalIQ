# SignalIQ: Layer 1 Specification (Final - Production-Grade MVP)

## Version 2.0 — Updated with Runtime Observations

---

## The Operating Principle (Correctly Stated)

> Layer 1 understands **format and schema structure** (RSS fields, URL parameters, timestamps). It does **not** understand **semantic meaning or financial relevance** (sentiment, entity resolution, content filtering, probabilistic interpretation).

---

## Spec Authority Rule

This document is authoritative for Layer 1 implementation.

When implementation conflicts with spec:
1. If implementation passes all tests and spec is outdated → update spec
2. If implementation fails tests but works "accidentally" → fix implementation
3. Spec changes require: (a) test update, (b) implementation update, (c) changelog entry

**Runtime behavior overrides spec only when:**
- Behavior is observable (logs, database state, test output)
- Behavior is repeatable (not a one-off anomaly)
- Behavior is documented in this spec post-observation

This prevents "drift by convenience" while allowing "correction by evidence."

---

## What Layer 1 Is Allowed to Understand

| ✅ Structural Understanding | ❌ Business Inference |
|----------------------------|----------------------|
| RSS field names and types | Sentiment of headline |
| URL query parameters (e.g., `?s={TICKER}`) | Whether news is "good" or "bad" |
| Timestamp formats and timezone conversion | Which asset a headline refers to (beyond explicit URL parameter) |
| Text normalization (case, whitespace) | Relevance filtering |
| SHA256 hashing | Source weighting |
| HTTP status codes | Political/editorial leaning |
| Feed metadata as provided by source | Any probabilistic or semantic judgment |

---

## The Core Distinction

| Layer 1 Sees | Layer 1 Does Not See |
|--------------|---------------------|
| "There is a URL parameter named `s` with value `NVDA`" | "NVDA is a stock ticker for NVIDIA" |
| "The feed returned a field called `pubDate`" | "This timestamp means the news was published" |
| "This headline text is a string" | "This headline is positive about the market" |

**Layer 1 extracts structure. It never interprets meaning.**

---

## Idempotency Contract

Layer 1 guarantees that for a given `(run_id, source_type, target_date)`:

- Running the orchestration twice produces identical database state
- No duplicate records in `raw.prices` or `raw.news_headlines`
- Idempotency is enforced by Layer 2's unique constraints, not Layer 1 logic
- Layer 1 does **not** attempt to detect duplicates before writing
- Retry scenarios: if first write succeeded but commit failed, second write will hit `UniqueViolation` and be safely ignored

**Enforcement mechanism:**
- `raw.prices`: partial unique index `(ticker, vendor, date) WHERE is_correction = FALSE`
- `raw.news_headlines`: `UNIQUE(source_id, url_hash)`
- Layer 1 write functions return `None` on `UniqueViolation`

**This is a correctness invariant, not a performance optimization.**

---

## Component 1: Price Collection

### Source
- Yahoo Finance only
- Endpoint: `query1.finance.yahoo.com/v8/finance/chart/{SYMBOL}`
- Parameters: `range=1d`, `interval=1d`

### Assets (Exactly 5)

| Ticker | Yahoo Symbol |
|--------|--------------|
| NVDA | NVDA |
| AAPL | AAPL |
| MSFT | MSFT |
| SPX | ^GSPC |
| BTC-USD | BTC-USD |

### Data Collected

| Field | Type | Nullable |
|-------|------|----------|
| ticker | string | No |
| vendor | string | No (always "yahoo_finance") |
| date | date | No |
| open | decimal(10,4) | No |
| high | decimal(10,4) | No |
| low | decimal(10,4) | No |
| close | decimal(10,4) | No |
| adj_close | decimal(10,4) | No |
| volume | bigint | Yes (NULL for indices, crypto) |

### Volume Field Contract

Field exists in `raw.prices` table but may be NULL.

NULL volume is acceptable for MVP because:
- Volume not used in NDI calculation
- Volume not used in Layer 3 momentum
- Volume not used in Layer 4 classification

Layer 3 explicitly ignores volume (confirmed: momentum uses `adj_close` only)

**Sources of NULL volume:**
- Indices (SPX)
- Cryptocurrencies (BTC-USD)
- Any asset where Yahoo Finance does not provide volume

This is a documented limitation, not a bug.

### Historical Backfill

- Layer 1 fetches **ONLY the last trading day** (`range=1d`, `interval=1d`)
- Historical data loading is Layer 2's warm-up responsibility
- Layer 3's rolling windows are populated via Layer 2 `get_prices_history()`
- This keeps Layer 1 simple and idempotent

### Retry Policy

| Parameter | Value |
|-----------|-------|
| Maximum attempts | 2 (initial + 1 retry) |
| Initial delay | 5 seconds |
| Backoff strategy | Linear (no jitter in MVP) |
| Request timeout | 30 seconds |

**Retryable errors:**
- Timeout
- 5xx server errors
- Connection errors
- 429 (rate limit)

**Non-retryable:**
- 4xx (except 429)
- Malformed response
- Missing required fields

### Error Handling

| Scenario | Action |
|----------|--------|
| Single asset fails | Log warning, continue with remaining assets |
| All 5 assets fail | Log critical, `sys.exit(1)` |
| Missing `adj_close` | Skip asset entirely, log warning |
| Malformed response | Skip asset, log error with details |

### Schedule
- Once daily, after 8 PM Eastern Time
- Cron: `5 20 * * *`

---

## Component 2: News Collection

### Sources (Exactly 6, Hardcoded)

| Source | RSS URL | Provides URL Parameter |
|--------|---------|------------------------|
| Reuters Business | `http://feeds.reuters.com/reuters/businessNews` | No |
| Associated Press | `https://apnews.com/business.rss` | No |
| Yahoo Finance General | `https://finance.yahoo.com/news/rssindex` | No |
| Yahoo Finance Ticker | `https://finance.yahoo.com/rss/headline?s={TICKER}` | Yes (parameter `s`) |
| CNBC | `https://www.cnbc.com/id/100003114/device/rss/rss.html` | No |
| MarketWatch | `http://feeds.marketwatch.com/marketwatch/topstories/` | No |

### Data Collected Per Headline

| Field | Source | Nullable | Layer 1 Understanding |
|-------|--------|----------|----------------------|
| headline | RSS `<title>` | No | A string |
| normalized_headline | Derived | No | Lowercase, stripped string |
| headline_hash | Derived (SHA256) | No | 64-char hex string |
| article_url | RSS `<link>` | No | A string |
| url_hash | Derived (SHA256) | No | 64-char hex string |
| published_at | RSS `<pubDate>` | Yes | UTC timestamp (NULL if missing) |
| ingested_at | System | No | UTC timestamp |
| author | `<dc:creator>` or `<author>` | Yes | String |
| content_snippet | RSS `<description>` | Yes | String, stripped, max 500 chars |
| source_name | Hardcoded | No | Identifier string |
| url_param_value | URL `?s=` parameter | Yes | String (if present) |

### URL Parameter: Structural, Not Semantic

Layer 1 sees: "There is a URL parameter named `s` with value `NVDA`"

Layer 1 does **not** assume: "This value `NVDA` refers to the asset NVDA"

The value is stored as a neutral string. Layer 3 decides what it means.

### Query Parameter Extraction

Extract **all** query parameters generically (not hardcoded to `s` or `q`):

```python
def extract_all_query_params(url):
    """Return dict of all query parameters, or None if none exist."""
```

The result is included in internal processing but not in JSON output (MVP simplifies stdout contract).

### Deduplication Rule
- Same `url_hash` + same source: skip (enforced by Layer 2 unique constraint)
- Same `headline_hash` + different sources: keep both

### Retry Policy

| Parameter | Value |
|-----------|-------|
| Maximum attempts | 2 (initial + 1 retry) |
| Initial delay | 5 seconds |
| Backoff strategy | Linear |
| Request timeout | 15 seconds |

**Retryable errors:**
- Timeout
- 5xx server errors
- Connection errors
- Bozo detection (`feed.bozo and not feed.entries`)

### Error Handling

| Scenario | Action |
|----------|--------|
| Single feed fails | Log warning, skip feed, continue with remaining 5 |
| All 6 feeds fail | Log critical, `sys.exit(1)` |
| Missing `published_at` | Store NULL (no inference) |
| Empty headline after normalization | Skip item silently |
| Malformed feed | Log error, trigger retry if bozo detection indicates |

### Schedule

| Window | Timing (Eastern Time) |
|--------|----------------------|
| Morning | 6:00 AM |
| Midday | 12:00 PM |
| Evening | 6:00 PM |

Cron: `0 6,12,18 * * *`

---

## Component 3: Database Writer (`writer.py`)

### Connection Management

```python
def get_connection():
    """Read DATABASE_URL env var, return psycopg2 connection."""
    # Raises ValueError if DATABASE_URL not set
    conn.autocommit = False  # Caller manages transactions
```

### Transaction Management

- Writer functions **NEVER** commit or rollback
- Connection has `autocommit = False`
- Orchestrator calls `conn.commit()` after all writes
- Orchestrator calls `conn.rollback()` on exception
- Each ingestion type (prices, news) is its own transaction

### `write_price(conn, record, ingestion_run_id)`

Calls `raw.insert_price_record()` with parameters:

| Parameter | Value |
|-----------|-------|
| p_ticker | record["ticker"] |
| p_vendor | "yahoo_finance" |
| p_date | record["date"] |
| p_open | record["open"] |
| p_high | record["high"] |
| p_low | record["low"] |
| p_close | record["close"] |
| p_adj_close | record["adj_close"] |
| p_volume | record["volume"] (may be None) |
| p_is_correction | FALSE (MVP) |
| p_supersedes_id | NULL (MVP) |
| p_ingestion_run_id | ingestion_run_id (UUID) |

**Returns:** Inserted `id` (BIGINT), or `None` on `UniqueViolation` or error

### `write_headline(conn, record, ingestion_run_id)`

Calls `raw.insert_headline_record()` with parameters:

| Parameter | Value |
|-----------|-------|
| p_source_id | source_id (from config.news_sources) |
| p_headline | record["headline"] |
| p_article_url | record["article_url"] |
| p_published_at | record["published_at"] (may be None) |
| p_author | record["author"] (may be None) |
| p_content_snippet | record["content_snippet"] (may be None) |
| p_ingestion_run_id | ingestion_run_id (UUID) |

**Note:** Layer 1 does **not** pass `url_hash`, `headline_hash`, `source_name_snapshot`, or `source_tier_snapshot` — Layer 2 auto-generates them.

**Returns:** Inserted `id`, or `None` on duplicate URL

### `get_source_id(conn, source_name)`

```sql
SELECT id FROM config.news_sources WHERE name = %s AND is_active = TRUE
```

Returns `int` or `None`. Called by orchestrator before writing headlines.

### Error Handling

| Error | Action |
|-------|--------|
| `UniqueViolation` | `conn.rollback()`, log warning, return `None` |
| Other `psycopg2.Error` | Log error with details, return `None` |
| Missing `DATABASE_URL` | Raise `ValueError` (re-raised to orchestrator) |

---

## Component 4: Orchestrator (`orchestrator.py`)

### Concurrency Control (Lock Files)

| Asset Type | Lock File Path |
|------------|----------------|
| Prices | `/tmp/signaliq_layer1_prices.lock` |
| News | `/tmp/signaliq_layer1_news.lock` |

**Behavior:**
- Checked at start of `main()` before any work
- Contains PID of running process
- Removed in `finally` block (even on crash)
- Separate locks allow price and news to run concurrently
- If lock exists, exit with error (do not wait)

### Ingestion Run Tracking

Each orchestration run generates a `UUID4` at start.

This `run_id` is passed to every `write_price()` and `write_headline()` call.

Layer 2 stores it in `raw.prices` and `raw.news_headlines`.

Enables future correction detection and data lineage.

### Logging Format (Pipe-Delimited)

```
timestamp | TYPE | source | STATUS | key=value pairs
```

**Example:**
```
2026-06-02T20:00:00Z | PRICE | yahoo_finance | SUCCESS | records=5 | duration_ms=1234
2026-06-02T12:00:00Z | NEWS | reuters | SUCCESS | records=42 | duplicates=3 | duration_ms=890
```

**Log file:** `logs/ingestion.log` (auto-created directory)

### Partial Failure Behavior

| Scenario | Behavior |
|----------|----------|
| Prices succeed, News fails | Price transaction commits; News transaction rolls back; Separate log entries for each |
| Some prices fail, others succeed | Each price written individually; failures logged but don't block others; Transaction commits all successful prices |
| News sources partially fail | Successful sources commit their headlines; Failed source logged, no headlines written |
| Retry within same run | Failed prices/feeds are NOT retried within same run; Next day's run fetches fresh data |

**Rule:** One source's failure never blocks another source's ingestion.

### Price Ingestion Flow

1. Generate `ingestion_run_id = str(uuid.uuid4())`
2. Log `START` entry
3. Call `fetch_prices()` → list of normalized dicts
4. For each dict: call `write_price(conn, record, run_id)`
5. Log `SUCCESS` entry with record count and elapsed time
6. Return success count

### News Ingestion Flow

1. Generate `ingestion_run_id`
2. Call `fetch_news(source_filter)` → `{source_name: [headlines]}`
3. For each source:
   a. Log `START` entry
   b. Look up `source_id` via `get_source_id(conn, name)`
   c. For each headline: call `write_headline(conn, record, run_id)`
   d. Log `SUCCESS` entry with count, duplicates, elapsed time
4. Return `{source_name: {"success": n, "duplicates": m}}`

### Transaction Boundaries

```python
try:
    run_price_ingestion(conn, dry_run=args.dry_run)
    conn.commit()
except Exception:
    conn.rollback()
    raise
```

Each ingestion type is its own transaction. If prices succeed and news fails, price writes are preserved (separate transactions).

### CLI Interface

```bash
python -m layer1.orchestrator                     # both prices + news
python -m layer1.orchestrator --type prices
python -m layer1.orchestrator --type news
python -m layer1.orchestrator --type news --source reuters
python -m layer1.orchestrator --type news --dry-run
```

---

## Shared Configuration (Neutral Artifact)

**File:** `config/entity_aliases.json`

**Purpose:** Shared configuration available to any downstream layer (Layer 3, Layer 4, debugging tools). Layer 1 does **not** read this file.

**Format:**
```json
{
  "NVDA": ["NVIDIA", "Nvidia", "NVIDIA CORPORATION", "Nvidia Corp"],
  "AAPL": ["Apple", "Apple Inc."],
  "MSFT": ["Microsoft", "Microsoft Corporation"],
  "SPX": ["S&P 500", "S&P500", "the S&P"],
  "BTC-USD": ["Bitcoin", "BTC"]
}
```

**Why separate from Layer 1:** Layer 1 does not need aliases to collect data. Aliases are an interpretation aid for downstream layers.

---

## What Layer 1 Explicitly Does NOT Do

| ❌ Not Layer 1 | ✅ Belongs In |
|---------------|---------------|
| Interpret URL parameter "s=NVDA" as an asset reference | Layer 3 |
| Decide that a headline matches an asset (beyond explicit URL parameter) | Layer 3 |
| Filter headlines by relevance | Layer 3 |
| Assign sentiment or meaning to text | Layer 3 |
| Apply any probabilistic or semantic judgment | Layer 3 |
| Read or use `entity_aliases.json` | Layer 3+ |
| Pre-aggregate or summarize | Layer 3+ |
| Weight sources by quality | Layer 4 (post-MVP) |

---

## Data Volume Estimate

| Type | Daily Records |
|------|---------------|
| Prices | 5 |
| Headlines | 30-105 |
| Log entries | ~10-20 |
| **Total** | **~45-130 per day** |

---

## MVP Success Criteria

| Metric | Target | Measurement |
|--------|--------|-------------|
| Price fetch success | >95% per asset | Log inspection |
| News fetch success | >90% per source | Log inspection |
| Headlines with timestamps | >90% | Downstream processing |
| Deduplication accuracy | 100% (exact) | Hash collisions impossible |
| Idempotency | No duplicate writes | Database constraint violations = 0 |

---

## Known Limitations (Explicitly Accepted)

| Limitation | Acceptance Rationale |
|------------|----------------------|
| No per-record lineage | Post-MVP add if needed |
| Yahoo Finance only | Acceptable for pilot |
| NULL volume for indices/crypto | Not used in MVP calculations |
| Headlines only (no article text) | Per Tetlock (2007), sufficient |
| Exact-title deduplication only | Acceptable for MVP |
| No source weighting | Post-MVP additive |
| No intraday data | Signal horizon is days |
| No macro feeds | Deferred to post-MVP |
| Linear backoff (no jitter) | RSS feeds independent; retry storms unlikely |

---

## Summary Table: Layer 1 MVP (Final)

| Area | Decision |
|------|----------|
| **Operating principle** | Understands format/schema, not meaning/relevance |
| **Spec authority** | Runtime behavior overrides spec only when observable, repeatable, and documented |
| **Idempotency** | Guaranteed via Layer 2 unique constraints; not Layer 1 logic |
| **Prices source** | Yahoo Finance only |
| **News sources** | 6 hardcoded RSS feeds |
| **Assets** | 5: NVDA, AAPL, MSFT, SPX, BTC-USD |
| **URL parameters** | Extracted as neutral strings. Not interpreted as asset references. |
| **Volume** | NULL allowed for indices and crypto; explicitly ignored by downstream |
| **Shared configuration** | `entity_aliases.json` — Layer 1 does not read it |
| **Logging** | Pipe-delimited, flat file, no semantic directory encoding |
| **Concurrency control** | Lock files in `/tmp/`, separate for prices/news |
| **Transaction boundaries** | Orchestrator commits/rollbacks; writer never does |
| **Run tracking** | UUID per run, passed to all write operations |
| **Retry policy** | 1 retry, 5s delay, linear backoff, 30s/15s timeouts |
| **Partial failure** | One source never blocks another; partial commits allowed |
| **Per-record lineage** | Not included (post-MVP if needed) |
| **Structural understanding** | ✅ Allowed (RSS fields, URL params, timestamps) |
| **Business inference** | ❌ Prohibited (sentiment, entity resolution, relevance) |

---

## Final Verdict

| Dimension | Status |
|-----------|--------|
| **Architectural correctness** | ✅ Structural vs semantic boundary is clear |
| **Practicality for MVP** | ✅ Layer 1 has enough structure to be useful |
| **Philosophical consistency** | ✅ No business logic, but format understanding allowed |
| **Idempotency** | ✅ Explicit contract with enforcement mechanism |
| **Failure semantics** | ✅ Partial failure explicitly defined |
| **Spec authority** | ✅ Clear rule for implementation vs spec conflicts |
| **Future evolution** | ✅ No baked-in assumptions that block scaling |

---

## Layer 1 Status: FINAL (Version 2.0)

> Clean, practical, deterministic ingestion layer. Understands format and schema. Extracts URL parameters as neutral strings. Never interprets meaning. Guarantees idempotency via Layer 2 constraints. Handles partial failure gracefully. Shared configuration exists but is not read by Layer 1.

---



