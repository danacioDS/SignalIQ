# SignalIQ Layer 1: Production Specification (Final)

## Version 2.1 — Production-Ready with Global Invariants

---

## The Core

> **Layer 1 is the ingestion layer — the entry point for all external data into SignalIQ. It collects raw prices and headlines, performs structural transformations only, and writes to Layer 2.**

**Core Principle:** Layer 1 understands **format and schema structure**. It does **not** understand **semantic meaning** (sentiment, entity resolution, relevance filtering, probabilistic interpretation).

**Status: READY FOR PROMPT GENERATION**

---

## Global Invariants (Layer 1 Contract)

These invariants hold for all Layer 1 operations and cannot be violated by any implementation:

| # | Invariant | Enforcement |
|---|-----------|-------------|
| 1 | **Layer 1 is stateless across runs** | No internal state persisted between executions except logs |
| 2 | **Layer 1 never reads from Layer 2 except `config.news_sources`** | No `SELECT` on `raw.*` or `ops.*` tables |
| 3 | **All idempotency guarantees are Layer 2's responsibility** | Layer 1 does not deduplicate; writes and handles `UniqueViolation` |
| 4 | **All transactions are orchestrator-owned** | Writer functions never commit/rollback |
| 5 | **All retries are per-source, not per-run** | Failed source does not retry within same run; next run retries fresh |
| 6 | **One source failure never blocks another source** | Partial failure is explicit, not exceptional |
| 7 | **NULL is semantically distinct from 0 or empty string** | NULL propagates; never coerced |

---

## Spec Authority Rule

This Production Specification is authoritative for Layer 1 implementation.

When implementation conflicts with spec:
1. If implementation passes all tests and spec is outdated → update spec
2. If implementation fails tests but works "accidentally" → fix implementation
3. Spec changes require: (a) test update, (b) implementation update, (c) changelog entry

**Runtime behavior overrides spec only when:**
- Behavior is observable (logs, database state, test output)
- Behavior is repeatable (not a one-off anomaly)
- Behavior is documented in this spec post-observation

---

## Design Assumptions (Explicit)

| # | Assumption | Rationale |
|---|------------|-----------|
| 1 | Yahoo Finance is sufficient for MVP prices | Covers 5 selected assets adequately |
| 2 | 6 RSS feeds provide sufficient news coverage | Signal quality can be validated with this volume |
| 3 | Exact headline deduplication is sufficient | Semantic deduplication is Layer 3 concern |
| 4 | Flat file logging is sufficient for MVP | Post-MVP migrate to `ops.ingestion_runs` |
| 5 | No intraday collection needed | Signal horizon is daily |
| 6 | URL parameters extracted generically | Interpretation belongs to Layer 3 |
| 7 | Linear backoff without jitter is acceptable | RSS feeds independent; retry storms unlikely |
| 8 | Lock file without stale recovery is acceptable | Cron overlap unlikely; manual cleanup if needed |

---

## What Layer 1 Is Allowed to Understand

| ✅ Structural Understanding | ❌ Business Inference |
|----------------------------|----------------------|
| RSS field names and types | Sentiment of headline |
| URL query parameters (any parameter, generically) | Whether `s=NVDA` means the asset NVDA |
| Timestamp formats and UTC conversion | Which asset a headline refers to |
| Text normalization (case, whitespace) | Relevance filtering |
| SHA256 hashing | Source weighting |
| HTTP status codes | Any probabilistic or semantic judgment |
| Feed metadata as provided by source | Reading `entity_aliases.json` |

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

**Deterministic preprocessing ensures stable key generation inputs:**
- URL hash: normalized via `url.strip().lower()` before SHA256
- Headline hash: normalized via lowercase + space collapse before SHA256
- Source ID lookup: stable, idempotent query to `config.news_sources`

**This is a correctness invariant, not a performance optimization.**

---

## Retry Policy Matrix (Single Source of Truth)

| System | Retryable Errors | Delay | Attempts | Notes |
|--------|-----------------|-------|----------|-------|
| Price (Yahoo) | timeout, 5xx, connection, 429 | 5s | 1 retry | Linear backoff |
| RSS fetch | timeout, 5xx, connection, bozo | 5s | 1 retry | Linear backoff |
| Rate limit override (429) | n/a (handled separately) | 60s | 1 retry | Only after 429 response |

**Non-retryable errors (skip immediately):**
- 4xx (except 429)
- Malformed response (JSON/XML parse error)
- Missing required fields

---

## Component 1: Price Collection

### Source Configuration

| Parameter | Value |
|-----------|-------|
| Vendor | Yahoo Finance |
| Endpoint | `query1.finance.yahoo.com/v8/finance/chart/{SYMBOL}` |
| Parameters | `range=1d`, `interval=1d` |
| Assets | NVDA, AAPL, MSFT, SPX (^GSPC), BTC-USD |
| Schedule | Once daily, after 8 PM Eastern Time |
| Timeout | 30 seconds |
| Retries | 1 retry after 5 seconds (see Retry Policy Matrix) |

### Data Extracted Per Asset

| Field | Source | Normalization | Nullable |
|-------|--------|---------------|----------|
| ticker | Internal mapping | Uppercase, trim whitespace | No |
| vendor | Hardcoded | "yahoo_finance" | No |
| date | API response | Date only (no time component) | No |
| open | API response | Round to 4 decimal places | No |
| high | API response | Round to 4 decimal places | No |
| low | API response | Round to 4 decimal places | No |
| close | API response | Round to 4 decimal places | No |
| adj_close | API response | **Primary field**, round to 4 decimals | No |
| volume | API response | Integer | Yes |
| is_correction | Computed | False for initial fetch | No |

### Volume Field Contract

NULL volume is acceptable for MVP because:
- Volume not used in NDI calculation
- Volume not used in Layer 3 momentum
- Volume not used in Layer 4 classification
- **NULL is semantically distinct from 0 and must not be coerced in Layer 2/3**

**Sources of NULL volume:**
- Indices (SPX)
- Cryptocurrencies (BTC-USD)
- Any asset where Yahoo Finance does not provide volume

### Historical Backfill

- Layer 1 fetches **ONLY the last trading day** (`range=1d`, `interval=1d`)
- Historical data loading is Layer 2's warm-up responsibility
- Layer 3's rolling windows are populated via Layer 2 `get_prices_history()`

### Error Handling

| Scenario | Action |
|----------|--------|
| Single asset fails | Log warning, continue with remaining assets |
| All 5 assets fail | Log critical, `sys.exit(1)` |
| Missing `adj_close` | Skip asset entirely, log warning |
| Malformed response | Skip asset, log error with details |

### Write Pattern

```python
def write_price(conn, record, ingestion_run_id):
    """Returns inserted id or None on UniqueViolation."""
    return layer2.insert_price_record(
        ticker=record["ticker"],
        vendor="yahoo_finance",
        date=record["date"],
        open=record["open"],
        high=record["high"],
        low=record["low"],
        close=record["close"],
        adj_close=record["adj_close"],
        volume=record.get("volume"),
        is_correction=False,
        supersedes_id=None,
        ingestion_run_id=ingestion_run_id
    )
```

---

## Component 2: News Collection

### Sources (Exactly 6, Hardcoded)

| Source | URL | URL Param |
|--------|-----|-----------|
| Reuters Business | `http://feeds.reuters.com/reuters/businessNews` | No |
| Associated Press | `https://apnews.com/business.rss` | No |
| Yahoo Finance General | `https://finance.yahoo.com/news/rssindex` | No |
| Yahoo Finance Ticker | `https://finance.yahoo.com/rss/headline?s={TICKER}` | Yes |
| CNBC | `https://www.cnbc.com/id/100003114/device/rss/rss.html` | No |
| MarketWatch | `http://feeds.marketwatch.com/marketwatch/topstories/` | No |

### Schedule

| Time (ET) | Sources |
|-----------|---------|
| 6:00 AM | All 6 |
| 12:00 PM | All 6 |
| 6:00 PM | All 6 |

**Total daily fetch operations:** 3 runs × 6 sources = 18

### RSS Fetch Configuration

| Parameter | Value |
|-----------|-------|
| User-Agent | `SignalIQ/1.0 (MVP ingestion layer)` |
| Timeout | 15 seconds |
| Retries | 1 retry after 5 seconds (see Retry Policy Matrix) |
| Encoding | UTF-8 (fallback: latin-1) |

### Data Extracted Per Headline

| Field | RSS Field | Normalization | Nullable |
|-------|-----------|---------------|----------|
| headline | `<title>` | Trim whitespace, collapse spaces | No |
| normalized_headline | Derived | Lowercase, stripped | No |
| headline_hash | Derived (SHA256) | 64-char hex | No |
| article_url | `<link>` | Raw string | No |
| url_hash | Derived (SHA256) | See URL Hash Normalization below | No |
| published_at | `<pubDate>` | Convert to UTC | Yes |
| ingested_at | System | UTC timestamp | No |
| author | `<dc:creator>` or `<author>` | Raw string | Yes |
| content_snippet | `<description>` | Strip HTML, first 500 chars | Yes |
| source_name | Hardcoded | Identifier string | No |
| url_param_value | URL `?s=` parameter | String | Yes |

### URL Hash Normalization (Canonical)

```python
def normalize_url_for_hash(url: str) -> str:
    """
    Normalize URL for deterministic hashing.
    Preserves path and query case for uniqueness.
    Only normalizes scheme/host to lowercase.
    """
    parsed = urllib.parse.urlparse(url)
    # Normalize scheme and host only
    normalized = parsed._replace(
        scheme=parsed.scheme.lower(),
        netloc=parsed.netloc.lower()
    )
    # Path and query retain original case
    return urllib.parse.urlunparse(normalized)
```

**Why not full lowercase:** Preserves case-sensitive tracking parameters and signed URLs while preventing scheme/host case variations from breaking uniqueness.

### Generic Query Parameter Extraction

```python
def extract_all_query_params(url: str) -> dict | None:
    """
    Extract ALL query parameters from URL as a dictionary.
    Returns None if no query string.
    
    Layer 1 does not look for specific parameter names.
    Layer 3 decides which parameters (if any) are meaningful.
    """
    if not url:
        return None
    parsed = urllib.parse.urlparse(url)
    if not parsed.query:
        return None
    return dict(urllib.parse.parse_qsl(parsed.query))
```

### URL Parameter: Structural, Not Semantic

Layer 1 sees: "There is a URL parameter named `s` with value `NVDA`"

Layer 1 does **not** assume: "This value `NVDA` refers to the asset NVDA"

The value is stored as a neutral string. Layer 3 decides what it means.

### Headline Normalization Steps

| Step | Operation |
|------|-----------|
| 1 | `headline.strip()` |
| 2 | `re.sub(r'\s+', ' ', headline)` |
| 3 | `headline.lower()` |
| 4 | SHA256 of normalized string → `headline_hash` |

### Deduplication Rules

| Scenario | Action |
|----------|--------|
| Same `url_hash` + same source | Skip (enforced by Layer 2 unique constraint) |
| Same `headline_hash` + different sources | Keep both |
| Same run, same source, same `url_hash` | Skip, increment duplicate_count |

### Error Handling

| Scenario | Action |
|----------|--------|
| Single feed fails | Log warning, skip feed, continue with remaining 5 |
| All 6 feeds fail | Log critical, `sys.exit(1)` |
| Missing `published_at` | Store NULL (no inference) |
| Empty headline after normalization | Skip item silently |
| Malformed feed | Log error, trigger retry if bozo detection indicates |

### Write Pattern

```python
def write_headline(conn, source_id, record, ingestion_run_id):
    """Returns inserted id or None on duplicate URL."""
    return layer2.insert_headline_record(
        source_id=source_id,
        headline=record["headline"],
        article_url=record["article_url"],
        published_at=record.get("published_at"),
        author=record.get("author"),
        content_snippet=record.get("content_snippet"),
        ingestion_run_id=ingestion_run_id
    )
    # Note: url_hash and headline_hash auto-generated by Layer 2
```

---

## Component 3: Database Writer (`writer.py`)

### Connection Management

```python
def get_connection():
    """Read DATABASE_URL env var, return psycopg2 connection."""
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL environment variable not set")
    conn = psycopg2.connect(db_url)
    conn.autocommit = False  # Caller manages transactions
    return conn
```

### Transaction Model (Explicit)

**One transaction per ingestion type per run:**

```python
# Price ingestion transaction
try:
    for each price:
        write_price(conn, record, run_id)
    conn.commit()
except Exception:
    conn.rollback()
    raise

# News ingestion transaction (separate)
try:
    for each source:
        for each headline:
            write_headline(conn, source_id, record, run_id)
    conn.commit()
except Exception:
    conn.rollback()
    raise
```

**Rules:**
- Writer functions NEVER commit or rollback
- Orchestrator owns all `commit()` and `rollback()` calls
- Each ingestion type (prices, news) is its own transaction
- **No per-row transactions** — batch commit only
- On `UniqueViolation`, rollback is **not** automatic; writer returns `None`, orchestrator continues

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
| p_volume | record.get("volume") |
| p_is_correction | False |
| p_supersedes_id | None |
| p_ingestion_run_id | ingestion_run_id |

**Returns:** Inserted `id` (BIGINT), or `None` on `UniqueViolation` or error

### `write_headline(conn, source_id, record, ingestion_run_id)`

Calls `raw.insert_headline_record()` with parameters:

| Parameter | Value |
|-----------|-------|
| p_source_id | source_id |
| p_headline | record["headline"] |
| p_article_url | record["article_url"] |
| p_published_at | record.get("published_at") |
| p_author | record.get("author") |
| p_content_snippet | record.get("content_snippet") |
| p_ingestion_run_id | ingestion_run_id |

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
| `UniqueViolation` | Log warning, return `None` (no rollback) |
| Other `psycopg2.Error` | Log error, return `None` |
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

**Stale lock handling (MVP):**
- No automatic stale recovery
- Operator responsibility: manual cleanup of orphaned lock files
- Detection: lock file exists but process PID not running

### Ingestion Run Tracking

Each orchestration run generates a `UUID4` at start.

This `run_id` is passed to every `write_price()` and `write_headline()` call.

Layer 2 stores it in `raw.prices` and `raw.news_headlines`.

Enables future correction detection and data lineage.

### Logging Format (Pipe-Delimited, Strict)

```
timestamp | TYPE | source | STATUS | key=value
```

**Rules:**
- No spaces around `=` in key-value pairs
- No quotes around values (except error messages with spaces)
- Error messages with spaces use double quotes: `error="connection timeout"`

**Examples:**
```
2026-06-02T20:00:00Z | PRICE | yahoo_finance | SUCCESS | records=5 | duration_ms=1234
2026-06-02T12:00:00Z | NEWS | reuters | SUCCESS | records=42 | duplicates=3 | duration_ms=890
2026-06-02T12:00:00Z | NEWS | cnbc | FAILED | error="connection timeout" | duration_ms=15000
```

**Log file:** `logs/ingestion.log` (auto-created directory)

### Partial Failure Behavior

| Scenario | Behavior |
|----------|----------|
| Prices succeed, News fails | Price transaction commits; News transaction rolls back; Separate log entries for each |
| Some prices fail (e.g., 1 of 5 assets) | Each price written individually; failures logged but don't block others; Transaction commits all successful prices |
| News sources partially fail | Successful sources commit their headlines; Failed source logged, no headlines written |
| Retry within same run | Failed prices/feeds are NOT retried within same run; Next day's run fetches fresh data |

**Rule:** One source's failure never blocks another source's ingestion.

### Price Ingestion Flow

1. Acquire price lock (exit if locked)
2. Generate `ingestion_run_id = str(uuid.uuid4())`
3. Log `START` entry
4. Call `fetch_prices()` → list of normalized dicts
5. Begin transaction
6. For each dict: call `write_price(conn, record, run_id)`
7. `conn.commit()` on success, `conn.rollback()` on exception
8. Log `SUCCESS` entry with record count and elapsed time
9. Release lock

### News Ingestion Flow

1. Acquire news lock (exit if locked)
2. Generate `ingestion_run_id`
3. Call `fetch_news(source_filter)` → `{source_name: [headlines]}`
4. Begin transaction
5. For each source:
   a. Log `START` entry
   b. Look up `source_id` via `get_source_id(conn, name)`
   c. For each headline: call `write_headline(conn, source_id, record, run_id)`
   d. Log `SUCCESS` entry with count, duplicates, elapsed time
6. `conn.commit()` on success, `conn.rollback()` on exception
7. Release lock

### CLI Interface

```bash
python -m layer1.orchestrator                     # both prices + news
python -m layer1.orchestrator --type prices
python -m layer1.orchestrator --type news
python -m layer1.orchestrator --type news --source reuters
python -m layer1.orchestrator --type news --dry-run
```

---

## Component 5: Shared Configuration (Not Read by Layer 1)

**File:** `config/entity_aliases.json`

**Purpose:** Available to downstream layers (Layer 3, Layer 4). Layer 1 does **not** read this file.

```json
{
  "NVDA": ["NVIDIA", "Nvidia", "NVIDIA CORPORATION", "Nvidia Corp"],
  "AAPL": ["Apple", "Apple Inc."],
  "MSFT": ["Microsoft", "Microsoft Corporation"],
  "SPX": ["S&P 500", "S&P500", "the S&P"],
  "BTC-USD": ["Bitcoin", "BTC"]
}
```

**Why separate:** Layer 1 does not need aliases to collect data. Aliases are interpretation aids for downstream layers.

---

## Component 6: Scheduler & Log Rotation

### Crontab Entries

```cron
# Prices: once daily at 8:05 PM ET
5 20 * * * cd /opt/signaliq && /usr/bin/python3 -m layer1.orchestrator --type prices

# News: three times daily
0 6,12,18 * * * cd /opt/signaliq && /usr/bin/python3 -m layer1.orchestrator --type news
```

### Log Rotation Script (`scripts/rotate_logs.sh`)

```bash
#!/bin/bash
# Move current log to dated file
mv logs/ingestion.log logs/ingestion-$(date -d "yesterday" +%Y%m%d).log 2>/dev/null
# Delete logs older than 90 days
find logs/ -name "ingestion-*.log" -mtime +90 -delete
```

### Log Rotation Cron

```cron
0 0 * * * /opt/signaliq/scripts/rotate_logs.sh
```

---

## What Layer 1 Explicitly Does NOT Do

| ❌ Not Layer 1 | ✅ Belongs In |
|---------------|---------------|
| Interpret URL parameters (e.g., `s=NVDA` as asset reference) | Layer 3 |
| Match headlines to assets (beyond explicit URL param) | Layer 3 |
| Filter headlines by relevance | Layer 3 |
| Assign sentiment or meaning to text | Layer 3 |
| Apply any probabilistic or semantic judgment | Layer 3 |
| Read or use `entity_aliases.json` | Layer 3+ |
| Pre-aggregate or summarize | Layer 3+ |
| Weight sources by quality | Layer 4 (post-MVP) |
| Semantic deduplication | Layer 3+ |
| Populate `ops.ingestion_runs` | Post-MVP |

---

## Integration Points

### Upstream (External Sources)

| Source | Protocol | Output Format |
|--------|----------|---------------|
| Yahoo Finance | HTTPS | JSON |
| RSS feeds (6 sources) | HTTPS | XML (RSS 2.0) |

### Downstream (Layer 2)

| Operation | Layer 2 Function |
|-----------|------------------|
| Insert price | `raw.insert_price_record(...)` |
| Insert headline | `raw.insert_headline_record(...)` |
| Lookup source ID | `SELECT id FROM config.news_sources WHERE name = %s` |

**Contract:** Layer 1 does **not** read from Layer 2 (except `config.news_sources` for source lookup). Layer 1 only writes.

---

## Data Volume Estimates (MVP)

| Type | Per Day | Per Year |
|------|---------|----------|
| Prices | 5 | 1,825 |
| Headlines (6 sources × 3 runs × avg 5-6 items) | 90-105 | ~35,000 |
| Log entries | ~10-20 | ~5,000 |
| **Total** | **~105-130** | **~42,000** |

---

## Error Handling Summary

| Error Type | Detection | Recovery | Logging |
|------------|-----------|----------|---------|
| Network timeout | HTTP timeout | Retry 1x after 5s | ERROR |
| HTTP 4xx/5xx | Status code | Skip source (retry next window) | ERROR |
| Malformed JSON/XML | Parse exception | Skip item/source | ERROR |
| Missing required field | Field validation | Store NULL if allowed, else skip | WARNING |
| Duplicate headline | Layer 2 unique constraint | Skip, increment counter | INFO |
| Rate limit | HTTP 429 | Retry once after 60s | WARNING |

---

## MVP Success Criteria

| Metric | Target | Measurement |
|--------|--------|-------------|
| Price fetch success | >95% per asset | Log inspection |
| News fetch success | >90% per source | Log inspection |
| Headlines with timestamps | >90% | Downstream processing (Layer 3) |
| Deduplication accuracy | 100% (exact hash) | Hash collisions impossible |
| No semantic inference in code | 0 violations | Code review |
| No Layer 1 reads of alias file | 100% | Code review |
| Idempotency | 0 duplicate violations | Database constraint violation count |
| Lock files prevent concurrent runs | 100% | Manual test |

---

## Setup Checklist

- [ ] Create directory: `logs/`
- [ ] Create directory: `config/` (for `entity_aliases.json` — Layer 3, not Layer 1)
- [ ] Create file: `config/entity_aliases.json` with alias mappings
- [ ] Install dependencies:
  - [ ] `psycopg2-binary>=2.9.0`
  - [ ] `requests>=2.28.0`
  - [ ] `feedparser>=6.0.0`
- [ ] Set environment variable: `DATABASE_URL`
- [ ] Run Layer 2 migrations first (Layer 1 depends on Layer 2)
- [ ] Test price: `python -m layer1.collect_prices --dry-run`
- [ ] Test news: `python -m layer1.collect_news --dry-run`
- [ ] Test orchestrator: `python -m layer1.orchestrator --dry-run`
- [ ] Install crontab entries via `scripts/install_crontab.sh`
- [ ] Verify logs written to `logs/ingestion.log`

---

## Known Limitations (Explicitly Accepted)

| Limitation | Acceptance Rationale | Post-MVP Path |
|------------|----------------------|----------------|
| No ingestion run tracking in DB (only UUID passed) | MVP simplicity | Foreign key to `ops.ingestion_runs` |
| Exact headline dedup only | Acceptable for MVP | Add semantic dedup in Layer 3 |
| No per-record lineage | MVP assumption | Add `lineage_id` to tables |
| Linear backoff (no jitter) | Acceptable (RSS feeds independent) | Add jitter if retry storms occur |
| No stale lock recovery (manual cleanup) | Cron unlikely to overlap; operator responsibility | Add timeout + stale PID detection |
| Yahoo Finance only | Pilot scope | Add Alpha Vantage, others |
| NULL volume for indices/crypto | Not used in MVP calculations | Add if signal requires |
| 3 news runs/day (not 6) | Sufficient for validation | Increase frequency |

---

## Security & Access Control

| Role | Permissions | Used By |
|------|-------------|---------|
| layer1_etl | INSERT on `raw.*`; SELECT on `config.news_sources` | Ingestion scripts |

**Note:** Layer 1 connects to PostgreSQL using the `layer1_etl` database role.

---

## Migration Strategy

**Rule:** All code changes require version control. No formal migration files for MVP.

**Process:**
1. Update code in `layer1/` directory
2. Run tests: `python -m pytest tests/test_layer1.py`
3. Deploy via git pull + restart cron (or wait for next scheduled run)

---

## Design Decision Summary

| Decision | Rationale |
|----------|-----------|
| Yahoo Finance only | MVP scope; 5 assets is manageable |
| 6 RSS feeds hardcoded | No need for dynamic source discovery |
| Extract all query params generically | Removes assumption about which param matters |
| Layer 1 does not read alias file | Enforces structural vs semantic boundary |
| UUID passed to writes for traceability | Enables future correction detection |
| Pipe-delimited logging with strict format | Human-readable, easy to parse |
| 3 news runs/day (not 6) | Sufficient for signal validation |
| 1 retry, linear backoff | Simpler; MVP doesn't need sophisticated retry |
| No stale lock recovery (manual cleanup) | Cron overlap unlikely; operator responsibility |
| Idempotency via Layer 2 constraints | Single source of truth for uniqueness |
| Partial failure allowed | One source never blocks another |
| One transaction per ingestion type | Batch commit, no per-row transactions |
| URL hash preserves path/query case | Prevents false duplicates from case variations |

---

## Prompt Generation Mapping

This Production Specification maps directly to 5 implementation prompts:

| Prompt | Module | Lines (est) | Focus |
|--------|--------|-------------|-------|
| 1 | `layer1/collect_prices.py` | 165 | Yahoo Finance OHLCV with retry logic |
| 2 | `layer1/collect_news.py` | 200 | RSS news collection with generic query param extraction |
| 3 | `layer1/writer.py` | 115 | PostgreSQL atomic writes, no transaction management |
| 4 | `layer1/orchestrator.py` | 170 | Locking, logging, coordination, UUID generation |
| 5 | Deployment artifacts | ~200 | Scripts, crontab, log rotation, tests, README |

Each prompt must include:
- Function signatures
- Expected behavior (happy path)
- Error handling table
- Retry logic specification (per Retry Policy Matrix)
- CLI interface (if applicable)
- Test criteria

---

## Layer 1 Status: READY FOR PROMPT GENERATION

> Production-grade ingestion specification with global invariants, explicit transaction model, canonical URL normalization, strict logging format, and complete retry policy matrix. No semantic inference. Ready for translation into 5 implementation prompts.

---

**SignalIQ** 🔹

*Layer 1 Production Specification v2.1 — Structural ingestion with production contracts. Global invariants enforced. Ready for prompt generation.*