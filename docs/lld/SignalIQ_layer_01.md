# SignalIQ Layer 1: Low-Level Design (MVP-Optimized)

## Version 2.0 — Updated with Runtime Observations & Production Contracts

---

## Overview

Layer 1 is the **ingestion layer** — the entry point for all external data into SignalIQ. It collects raw prices and headlines from external sources, performs **structural transformations only** (normalization, hashing, timestamp conversion), and writes to Layer 2.

**Core Principle:** Layer 1 understands **format and schema structure**. It does **not** understand **semantic meaning**.

**Status: READY FOR IMPLEMENTATION**

---

## Spec Authority Rule

This LLD derives from and must remain consistent with:
1. `docs/hld/SignalIQ_mvp_plan.md` (HLD)
2. `docs/hld/SignalIQ_mvp_uni_exec.md` (Unified Specification)
3. `docs/lld/SignalIQ_layer_01.md` (this document)

When conflicts exist, the Unified Specification takes precedence. Runtime behavior overrides spec only when observable, repeatable, and documented.

---

## Design Assumptions (MVP)

| # | Assumption | Rationale |
|---|------------|-----------|
| 1 | 5 assets is sufficient for pilot | NVDA, AAPL, MSFT, SPX, BTC-USD |
| 2 | 6 RSS feeds provide enough coverage | Signal quality can be validated with this volume |
| 3 | Exact headline dedup is sufficient for MVP | Semantic dedup is post-MVP |
| 4 | Flat file logging is simpler than DB | Post-MVP migrate to ops.ingestion_runs |
| 5 | No intraday collection needed | Signal horizon is daily |
| 6 | URL parameters are extracted as generic query strings | Interpretation belongs to Layer 3 |
| 7 | Linear backoff without jitter is acceptable | RSS feeds are independent; retry storms unlikely |
| 8 | Lock file without stale recovery is acceptable | Cron overlap unlikely in MVP |

---

## What Layer 1 Is Allowed to Understand

| ✅ Structural Understanding | ❌ Business Inference |
|----------------------------|----------------------|
| RSS field names and types | Sentiment of headline |
| URL query parameters (any parameter, generically) | Whether `s=NVDA` means the asset NVDA |
| Timestamp formats and UTC conversion | Which asset a headline refers to |
| Text normalization (case, whitespace) | Relevance filtering |
| SHA256 hashing | Source weighting |
| HTTP status codes | Any probabilistic judgment |

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

### Configuration

| Parameter | Value |
|-----------|-------|
| Vendor | Yahoo Finance |
| Endpoint | `query1.finance.yahoo.com/v8/finance/chart/{SYMBOL}` |
| Parameters | `range=1d`, `interval=1d` |
| Assets | NVDA, AAPL, MSFT, SPX (^GSPC), BTC-USD |
| Schedule | Once daily, after 8 PM ET |
| Timeout | 30 seconds |
| Retries | 1 retry after 5 seconds |
| Backoff | Linear (no jitter) |

### Data Extracted Per Asset

| Field | Source | Normalization | Nullable |
|-------|--------|---------------|----------|
| ticker | Internal mapping | Uppercase, trim | No |
| vendor | Hardcoded | "yahoo_finance" | No |
| date | API response | Date only (no time) | No |
| open | API response | Round to 4 decimals | No |
| high | API response | Round to 4 decimals | No |
| low | API response | Round to 4 decimals | No |
| close | API response | Round to 4 decimals | No |
| adj_close | API response | Round to 4 decimals | No |
| volume | API response | Integer | Yes (NULL for indices, crypto) |

### Volume Field Contract

NULL volume is acceptable for MVP because:
- Volume not used in NDI calculation
- Volume not used in Layer 3 momentum
- Volume not used in Layer 4 classification

**Sources of NULL volume:**
- Indices (SPX)
- Cryptocurrencies (BTC-USD)
- Any asset where Yahoo Finance does not provide volume

### Historical Backfill

- Layer 1 fetches **ONLY the last trading day** (`range=1d`, `interval=1d`)
- Historical data loading is Layer 2's warm-up responsibility
- Layer 3's rolling windows are populated via Layer 2 `get_prices_history()`

### Retry Policy Details

| Scenario | Action |
|----------|--------|
| Timeout | Retry once after 5 seconds |
| 5xx server error | Retry once after 5 seconds |
| Connection error | Retry once after 5 seconds |
| 429 rate limit | Retry once after 5 seconds |
| 4xx (except 429) | No retry, log error |
| Malformed response | No retry, log error |
| Missing required fields | No retry, skip asset |

### Error Handling

| Scenario | Action |
|----------|--------|
| Single asset fails | Log warning, continue with remaining assets |
| All 5 assets fail | Log critical, `sys.exit(1)` |
| Missing `adj_close` | Skip asset entirely, log warning |
| Malformed response | Skip asset, log error with details |

---

## Component 2: News Collection

### Sources (Exactly 6)

| Source | URL | URL Param |
|--------|-----|-----------|
| Reuters | `http://feeds.reuters.com/reuters/businessNews` | No |
| Associated Press | `https://apnews.com/business.rss` | No |
| Yahoo Finance General | `https://finance.yahoo.com/news/rssindex` | No |
| Yahoo Finance Ticker | `https://finance.yahoo.com/rss/headline?s={TICKER}` | Yes |
| CNBC | `https://www.cnbc.com/id/100003114/device/rss/rss.html` | No |
| MarketWatch | `http://feeds.marketwatch.com/marketwatch/topstories/` | No |

### Schedule

| Time (ET) | Runs |
|-----------|------|
| 6:00 AM | All 6 sources |
| 12:00 PM | All 6 sources |
| 6:00 PM | All 6 sources |

**Total:** 3 runs/day × 6 sources = 18 fetch operations

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

### Data Extracted Per Headline

| Field | RSS Field | Normalization | Nullable |
|-------|-----------|---------------|----------|
| headline | `<title>` | Trim whitespace, collapse spaces | No |
| normalized_headline | Derived | Lowercase, stripped | No |
| headline_hash | Derived (SHA256) | 64-char hex | No |
| article_url | `<link>` | Raw string | No |
| url_hash | Derived (SHA256) | 64-char hex | No |
| published_at | `<pubDate>` | Convert to UTC | Yes |
| ingested_at | System | UTC timestamp | No |
| author | `<dc:creator>` or `<author>` | Raw string | Yes |
| content_snippet | `<description>` | Strip HTML, first 500 chars | Yes |
| source_name | Hardcoded | Identifier string | No |
| url_param_value | URL `?s=` parameter | String | Yes |

### Generic Query Parameter Extraction (Neutral)

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

**Why this change:** Layer 1 extracts **all** query parameters generically, not just `s=`. This removes any assumption about which parameter might be meaningful. Layer 3 decides later.

### URL Parameter: Structural, Not Semantic

Layer 1 sees: "There is a URL parameter named `s` with value `NVDA`"

Layer 1 does **not** assume: "This value `NVDA` refers to the asset NVDA"

The value is stored as a neutral string. Layer 3 decides what it means.

### Headline Normalization

| Step | Operation |
|------|-----------|
| 1 | `headline.strip()` |
| 2 | `re.sub(r'\s+', ' ', headline)` |
| 3 | `headline.lower()` |
| 4 | SHA256 of normalized string |

### Deduplication

| Rule | Action |
|------|--------|
| Same `url_hash` + same source | Skip (enforced by Layer 2 unique constraint) |
| Same `headline_hash` + different sources | Keep both |

### Error Handling

| Scenario | Action |
|----------|--------|
| Single feed fails | Log warning, skip feed, continue with remaining 5 |
| All 6 feeds fail | Log critical, `sys.exit(1)` |
| Missing `published_at` | Store NULL (no inference) |
| Empty headline after normalization | Skip item silently |
| Malformed feed | Log error, trigger retry if bozo detection indicates |

---

## Component 3: Database Writer (`writer.py`)

### Connection Management

```python
def get_connection():
    """Read DATABASE_URL env var, return psycopg2 connection."""
    # Raises ValueError if DATABASE_URL not set
    conn = psycopg2.connect(db_url)
    conn.autocommit = False  # Caller manages transactions
    return conn
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
- If lock exists, exit with error (do not wait, no stale recovery)

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

## Component 5: Shared Configuration (Not Read by Layer 1)

**File:** `config/entity_aliases.json`

**Purpose:** For downstream layers only (Layer 3, Layer 4). Layer 1 does **not** read this file.

```json
{
  "NVDA": ["NVIDIA", "Nvidia", "NVIDIA CORPORATION", "Nvidia Corp"],
  "AAPL": ["Apple", "Apple Inc."],
  "MSFT": ["Microsoft", "Microsoft Corporation"],
  "SPX": ["S&P 500", "S&P500", "the S&P"],
  "BTC-USD": ["Bitcoin", "BTC"]
}
```

---

## Component 6: Scheduler & Log Rotation

### Crontab Entries

```cron
# Prices: once daily at 8:05 PM ET
5 20 * * * cd /opt/signaliq && /usr/bin/python3 -m layer1.orchestrator --type prices

# News: three times daily
0 6,12,18 * * * cd /opt/signaliq && /usr/bin/python3 -m layer1.orchestrator --type news
```

### Log Rotation (Cron)

```bash
0 0 * * * mv logs/ingestion.log logs/ingestion-$(date -d "yesterday" +\%Y\%m\%d).log
```

Retention: 90 days via `find -mtime +90 -delete`

---

## What Layer 1 Explicitly Does NOT Do

| ❌ Not Layer 1 | ✅ Belongs In |
|---------------|---------------|
| Interpret URL parameters | Layer 3 |
| Match headlines to assets | Layer 3 |
| Filter headlines by relevance | Layer 3 |
| Assign sentiment | Layer 3 |
| Read `entity_aliases.json` | Layer 3+ |
| Manage database transactions | Orchestrator |
| Semantic deduplication | Layer 3+ |
| Weight sources by quality | Layer 4 (post-MVP) |

---

## Integration with Layer 2

### Layer 1 → Layer 2 Calls

| Operation | Function |
|-----------|----------|
| Insert price | `SELECT raw.insert_price_record(...)` |
| Insert headline | `SELECT raw.insert_headline_record(...)` |
| Lookup source ID | `SELECT id FROM config.news_sources WHERE name = %s` |

### Layer 1 → Layer 2 Run Tracking

Layer 1 passes `ingestion_run_id` (UUID) to every write operation. Layer 2 stores it but does not enforce referential integrity in MVP (post-MVP: foreign key to `ops.ingestion_runs`).

---

## Data Volume (MVP)

| Type | Per Day | Notes |
|------|---------|-------|
| Prices | 5 | One per asset |
| Headlines | 30-105 | 6 sources × 3 runs × avg 5-6 items |
| Log entries | ~10-20 | Per run + errors |
| **Total** | **~45-130** | Trivial |

---

## MVP Success Criteria

| Metric | Target | How to Measure |
|--------|--------|----------------|
| Price fetch success | >95% per asset | Log inspection |
| News fetch success | >90% per source | Log inspection |
| Headlines with timestamps | >90% | Downstream processing |
| No semantic inference in code | 100% | Code review |
| No Layer 1 reads of alias file | 100% | Code review |
| All writes use Layer 2 functions | 100% | Integration test |
| Idempotency | 0 duplicate violations | Database constraint violation count |
| Lock files prevent concurrent runs | 100% | Manual test |

---

## Setup Checklist (MVP)

- [ ] Create directory: `logs/`
- [ ] Create directory: `config/` (for `entity_aliases.json` — Layer 3, not Layer 1)
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

## Known Limitations (MVP)

| Limitation | Acceptance | Post-MVP |
|------------|------------|----------|
| No ingestion run tracking in DB (only UUID passed) | Acceptable for MVP | Foreign key to `ops.ingestion_runs` |
| Exact headline dedup only | Acceptable for MVP | Add semantic dedup in Layer 3 |
| No per-record lineage | Acceptable for MVP | Add lineage_id |
| Linear backoff (no jitter) | Acceptable (RSS feeds independent) | Add jitter if retry storms occur |
| No stale lock recovery | Acceptable (cron unlikely to overlap) | Add timeout + stale PID detection |
| Yahoo Finance only | Pilot scope | Add Alpha Vantage |
| NULL volume for indices/crypto | Not used in MVP calculations | Add if signal requires |
| Single log file | Acceptable for MVP | Migrate to per-day structured logging |

---

## Design Decision Summary (MVP)

| Decision | Rationale |
|----------|-----------|
| Extract all query params generically | Removes assumption about which param matters |
| Layer 1 does not read alias file | Enforces structural vs semantic boundary |
| UUID passed to writes but no FK enforcement | Simplifies; Layer 2 can add referential integrity later |
| Pipe-delimited logging | Human-readable, easy to parse with `cut` |
| 3 news runs/day (not 6) | Sufficient for signal validation |
| 1 retry, linear backoff | Simpler; MVP doesn't need sophisticated retry |
| No stale lock recovery | Cron overlap unlikely; add if becomes problem |
| Idempotency via Layer 2 constraints | Single source of truth for uniqueness |

---

## Changes from Previous Version (v1.0 → v2.0)

| Section | Old (v1.0) | New (v2.0) |
|---------|-----------|-----------|
| Idempotency | Implied | ✅ Explicit contract with enforcement |
| Partial failure | Undefined | ✅ Explicit scenarios defined |
| Retry backoff | "1 retry after 5 seconds" | ✅ Linear backoff, retryable error classes |
| Volume field | "No volume data" | ✅ NULL allowed, contract with downstream |
| Lock files | Not specified | ✅ Explicit paths, behavior, no stale recovery |
| Transaction boundaries | Not specified | ✅ Orchestrator commits/rollbacks |
| Run tracking | Not specified | ✅ UUID per run, passed to all writes |
| Spec authority | None | ✅ Explicit rule |
| Log rotation | None | ✅ Daily rotation, 90-day retention |

---

## Layer 1 Status: READY FOR IMPLEMENTATION (v2.0)

> MVP-optimized ingestion layer with production contracts. Understands format, not semantics. Extracts all query parameters generically. UUID traceability. Idempotency guaranteed via Layer 2. Partial failure explicitly defined. Lock files prevent concurrency. Pipe-delimited logging. Ready for prompt generation and engineering handoff.

---

**SignalIQ** 🔹

*Layer 1 LLD (MVP v2.0) — Structural ingestion. No semantic inference. Generic query param extraction. Production contracts for idempotency, partial failure, and concurrency. Ready for implementation.*