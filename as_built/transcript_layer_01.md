# SignalIQ Layer 1 — Transcript 01: Data Ingestion Build (v2.0)

## Overview

Layer 1 is the data ingestion layer. It collects daily price data from Yahoo
Finance and news headlines from 6 RSS feeds, normalizes them, and writes them
to Layer 2 (PostgreSQL). Built from the corrected v2.0 spec with all
contradictions resolved.

| Prompt | Output | Lines | Focus |
|--------|--------|-------|-------|
| 1A | `layer1/http_client.py` | 75 | Shared HTTP with retry logic |
| 1B | `layer1/collect_prices.py` | 115 | Yahoo Finance OHLCV |
| 2 | `layer1/collect_news.py` | 211 | RSS news collection with observability |
| 3A | `layer1/writer.py` | 96 | PostgreSQL atomic writes |
| 3B | `layer1/orchestrator.py` | 214 | Orchestration, locks, logging |

**Total:** ~711 lines across 5 modules + deployment artifacts. All 15 integration tests pass. All existing Layer 3 (16 tests) and Layer 4 (15 tests) pass — zero regressions.

---

## Prompt 1A — HTTP Client (`http_client.py`)

### What it does

Shared HTTP utility with configurable retry logic. Used by both price and news
collection modules. No business logic.

### Function Signatures

```python
def fetch_with_retry(
    url: str, timeout: int, retry_delay: int = 5,
    max_attempts: int = 2, headers: Optional[dict] = None,
    is_retryable: Optional[Callable[[Exception], bool]] = None
) -> Optional[requests.Response]:

def default_is_retryable(error: Exception) -> bool:
```

### Retry Behavior

| Scenario | Action |
|----------|--------|
| Timeout | Retry once after 5s |
| Connection error | Retry once after 5s |
| HTTP 5xx | Retry once after 5s |
| HTTP 429 | Retry once after 5s |
| HTTP 4xx (except 429) | No retry |
| Response parsing error | No retry (caller handles) |

### Design decision

Retryable errors are detected by a pluggable `is_retryable` callable with a
sensible default. This keeps the retry logic reusable across price (Yahoo
Finance) and news (RSS feeds) without coupling to either domain.

---

## Prompt 1B — Price Collection (`collect_prices.py`)

### What it does

Fetches daily OHLCV data for 5 monitored assets from the Yahoo Finance chart
API (`query1.finance.yahoo.com/v8/finance/chart/{SYMBOL}`) using `requests`
via `fetch_with_retry`.

### Assets

| Ticker | Yahoo Symbol | Class |
|--------|-------------|-------|
| NVDA | NVDA | Equity |
| AAPL | AAPL | Equity |
| MSFT | MSFT | Equity |
| SPX | ^GSPC | Index |
| BTC-USD | BTC-USD | Cryptocurrency |

### API response parsing

The Yahoo Finance chart API returns a nested JSON structure:

```
chart → result[0] → timestamp[]            (Unix epoch seconds)
                  → meta
                  → indicators → quote[0]   → open[], high[], low[], close[], volume[]
                               → adjclose[0] → adjclose[]
```

Normalizes to:

```json
{"ticker": "NVDA", "vendor": "yahoo_finance", "date": "2026-06-02",
 "open": 150.25, "high": 152.00, "low": 149.50, "close": 151.00,
 "adj_close": 150.25, "volume": 12345678}
```

### Error handling

- **Missing adj_close**: ValueError raised, asset skipped (log warning)
- **Per-asset failure**: logged as warning, other assets continue
- **All 5 fail**: `logger.critical()` + `sys.exit(1)`
- **Malformed response**: `try/except (KeyError, IndexError, ValueError, TypeError)` — skip asset

### Retry policy

Delegates to `fetch_with_retry`: 1 retry after 5s, 30s timeout, 2 max attempts.

### Dry-run contract

- Same network behavior as production
- Retries still occur
- No database writes
- NOT a mocked run unless explicitly mocked for tests

### Key design decision

The module fetches only the **last trading day** (`range=1d, interval=1d`).
Historical backfill is not Layer 1's responsibility — it's handled by the
pipeline's warm-up which calls Layer 2's `get_prices_history()`.

### CLI

```
python -m layer1.collect_prices          # stdout JSON
python -m layer1.collect_prices --dry-run  # same network, no output
```

---

## Prompt 2 — News Collection (`collect_news.py`)

### What it does

Fetches headlines from 6 hardcoded RSS feeds using `feedparser` with
`requests` as the HTTP transport (via `fetch_with_retry`). Each headline is
normalized, NFKC-unicoded, hashed, and output as JSON.

### RSS Sources

| Source | URL | Notes |
|--------|-----|-------|
| reuters | `http://feeds.reuters.com/reuters/businessNews` | General business |
| ap | `https://apnews.com/business.rss` | General business |
| yahoo_general | `https://finance.yahoo.com/news/rssindex` | Finance |
| yahoo_ticker | `https://finance.yahoo.com/rss/headline?s={TICKER}` | Per-ticker (TICKER unused in MVP) |
| cnbc | `https://www.cnbc.com/id/100003114/device/rss/rss.html` | Finance |
| marketwatch | `http://feeds.marketwatch.com/marketwatch/topstories/` | Markets |

### Extraction and normalization per item

| Field | Source | Normalization |
|-------|--------|---------------|
| `headline` | `<title>` | NFKC → strip → collapse spaces (skip if empty) |
| `article_url` | `<link>` | `.strip()` |
| `published_at` | `<pubDate>` → `published_parsed` | UTC ISO string via `time.strftime`; `None` if missing |
| `author` | `authors[0].name` → `<author>` | First non-null wins; entries from `dc:creator` appear in `authors[]` |
| `content_snippet` | `<description>` | Strip HTML tags, truncate to 500 chars |
| `url_param_value` | URL `s` parameter | Extracted from article URL if present |
| `headline_hash` | SHA256 of normalized (NFKC+lower) headline | 64-char hex |
| `url_hash` | SHA256 of scheme/host-lowercased URL | 64-char hex |

### Author resolution (corrected)

feedparser exposes `dc:creator` through its `authors[]` list, NOT as a
top-level `dc:creator` key. Resolution order:

1. `entry.get("authors")[0].get("name")` — covers `dc:creator` and `<author>`
2. `entry.get("author")` — fallback string
3. None — if neither present

### Unicode normalization

```
Normalization: strip → NFKC → collapse spaces → lowercase
```

NFKC (Normalization Form KC) was chosen over NFD/NFKD because it handles
compatibility compositions (e.g. ligatures, full-width characters) that are
common in scraped web content.

### Observability

| Metric | Log Format |
|--------|------------|
| Skipped empty headlines | `WARNING | SKIPPED_EMPTY_HEADLINE | source=reuters | count=3` |
| Feed fetch failure | `ERROR | FEED_FAILED | source=cnbc | error=timeout` |
| Parse errors (bozo) | `WARNING | BOZO_DETECTED | source=ap | retry=1` |

Empty headlines are no longer skipped silently — they are counted and logged.

### URL parameter extraction

```python
def extract_all_query_params(url):
    """Return dict of ALL query parameters, or None if none exist."""
```

Extracts **all** parameters generically (not hardcoded to `s` or `q`).
The `url_param_value` field stores the `s` parameter value for Layer 3 entity
resolution. All other params are logged at DEBUG level but discarded — no
database field defined in MVP.

### Error handling

- **Single feed failure**: log warning, skip, continue with remaining 5
- **All 6 fail**: `logger.critical()` + `sys.exit(1)`
- **Missing published_at**: stored as `None` (no inference)
- **Empty headline after normalization**: counted + logged at WARNING
- **Bozo feed detection**: `feed.bozo and not feed.entries` triggers retry

### Retry policy

Delegates to `fetch_with_retry`: 1 retry after 5s, 15s timeout, 2 max attempts.

### CLI

```
python -m layer1.collect_news                  # all sources
python -m layer1.collect_news --source reuters  # single source
python -m layer1.collect_news --dry-run         # same network, no output
```

---

## Prompt 3A — Database Writer (`writer.py`)

### What it does

Writes normalized price and headline records to Layer 2 PostgreSQL via the
atomic SQL functions already defined in the migration.

### Connection

```python
def get_connection():
    """Read DATABASE_URL env var, return psycopg2 connection."""
    db_url = os.environ.get("DATABASE_URL")
    # Raises ValueError if not set
    conn = psycopg2.connect(db_url)
    conn.autocommit = False  # caller manages transactions
```

### `write_price(conn, record, ingestion_run_id)`

Calls `raw.insert_price_record(...)` using **named parameter dict**:

```python
cur.execute(
    """SELECT raw.insert_price_record(
        %(ticker)s, %(vendor)s, %(date)s,
        %(open)s, %(high)s, %(low)s, %(close)s, %(adj_close)s,
        %(volume)s,
        FALSE, NULL, %(ingestion_run_id)s
    )""",
    {**record, "ingestion_run_id": ingestion_run_id},
)
```

- `is_correction` is always `FALSE` (MVP)
- `supersedes_id` is always `NULL` (MVP)
- Returns the inserted `id` (BIGINT), or `None` on `UniqueViolation` or error

### `write_headline(conn, source_id, record, ingestion_run_id)`

Calls `raw.insert_headline_record(...)` using named parameter dict:

- Layer 1 does **not** pass `url_hash`, `headline_hash`, `source_name_snapshot`,
  or `source_tier_snapshot` — Layer 2 auto-generates them
- Returns the inserted `id`, or `None` on duplicate URL

### `get_source_id(conn, source_name)`

```sql
SELECT id FROM config.news_sources WHERE name = %s AND is_active = TRUE
```

Returns `int` or `None`. Called by the orchestrator before writing headlines.

### Error handling

| Error | Action |
|-------|--------|
| `UniqueViolation` | Log WARNING, return None (no rollback) |
| Other `psycopg2.Error` | Log ERROR, return None |
| Missing `DATABASE_URL` | Raise ValueError |

### Key design decisions

- **Named parameters (dict-based)** — SQL uses `%(key)s` placeholders with a
  dict. This is more readable and maintainable than positional args, especially
  for functions with 12+ parameters.
- **No transaction management** in this module — the orchestrator owns
  `commit()` / `rollback()`
- **No batching** — each record is written individually (MVP simplicity)
- **`is_correction=False`** always — correction detection is deferred to
  post-MVP

---

## Prompt 3B — Orchestrator (`orchestrator.py`)

### What it does

Coordinates the entire ingestion pipeline: fetching, writing, logging, and
locking. This is the entry point for cron-driven execution.

### Atomic lock acquisition (`O_EXCL`)

```python
def atomic_acquire_lock(lock_type: str) -> Path:
    lock_path = Path(f"/tmp/signaliq_layer1_{lock_type}.lock")
    fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    os.write(fd, str(os.getpid()).encode())
    os.close(fd)
    return lock_path
```

- Uses `O_EXCL` for atomic creation — no race condition
- Contains PID of the running process
- Removed in `finally` block (even on crash)
- Separate locks for prices and news (they can run concurrently)
- No automatic stale lock recovery (MVP); manual cleanup via `rm /tmp/signaliq_layer1_*.lock`

### Pipe-delimited logging

```python
def log_entry(entry_type, source, status, duration_ms, **details):
```

Format: `timestamp | TYPE | source | STATUS | key=value | duration_ms=N`

```
2026-06-02T20:00:00Z | PRICE | yahoo_finance | SUCCESS | records=5 | duration_ms=1234
2026-06-02T12:00:00Z | NEWS | cnbc | FAILED | error="connection timeout" | duration_ms=15000
```

- `duration_ms` is always the last field
- Values with spaces use double quotes
- No spaces around `=`

### Transaction model (corrected)

Two distinct transaction boundaries based on data characteristics:

```
PRICE INGESTION: Single transaction
  All prices commit or none.
  If any price write fails, the entire batch rolls back.
  Caller: conn.commit() / conn.rollback()

NEWS INGESTION: No transaction (per-row idempotency)
  Each headline succeeds or fails independently.
  DB unique constraints (url_hash) provide idempotency.
  No commit() call — partial writes are acceptable by design.
```

**Why this model?** Prices are a coherent snapshot — partial writes would give
a misleading view of the market. News headlines are independent records —
partial ingestion is acceptable and preferable to losing all headlines because
one source failed.

### Price ingestion (`run_price_ingestion`)

1. Generate `ingestion_run_id = str(uuid.uuid4())`
2. Log `START` entry
3. Call `fetch_prices()` → list of normalized dicts
4. For each dict: call `write_price(conn, record, run_id)`
5. Log `SUCCESS` entry with record count and elapsed time
6. Return success count

### News ingestion (`run_news_ingestion`)

1. Generate `ingestion_run_id`
2. Call `fetch_news(source_filter)` → `{source_name: [headlines]}`
3. For each source:
   a. Look up `source_id` via `get_source_id(conn, name)`
   b. For each non-empty headline: call `write_headline(conn, source_id, record, run_id)`
   c. Log `SUCCESS` entry with count, duplicates, elapsed time
4. Return `{source_name: {"success": n, "duplicates": m, "skipped_empty": k}}`

### CLI

```
python -m layer1.orchestrator                     # both prices + news
python -m layer1.orchestrator --type prices
python -m layer1.orchestrator --type news
python -m layer1.orchestrator --type news --source reuters
python -m layer1.orchestrator --type news --dry-run
```

---

## Deployment Artifacts

| Artifact | Purpose |
|----------|---------|
| `scripts/install_crontab.sh` | Idempotent crontab installer (prices 8:05 PM ET daily, news 6/12/18 ET) |
| `scripts/rotate_logs.sh` | Daily rotation, 90-day retention |
| `config/entity_aliases.json` | Layer 3 config (Layer 1 never reads; consumed by EntityResolver) |
| `requirements_layer1.txt` | `psycopg2-binary>=2.9.0`, `requests>=2.28.0`, `feedparser>=6.0.0` |
| `.env.example` | `DATABASE_URL=postgresql://layer1_etl:password@localhost:5432/signaliq` |

---

## Architecture

```
┌───────────────────────────────────────────────────────────────────────┐
│                         Layer 1 (Ingestion)                          │
│                                                                       │
│  ┌─────────────────┐    ┌──────────────────┐    ┌────────────────┐   │
│  │  http_client.py  │    │  collect_news    │    │  writer.py     │   │
│  │  (shared retry)  │    │  (6 RSS feeds)   │    │  (PostgreSQL)  │   │
│  └────────┬─────────┘    └────────┬─────────┘    └───────┬────────┘   │
│           │                      │                       │            │
│  ┌────────▼─────────┐            │                       │            │
│  │  collect_prices   │            │                       │            │
│  │  (Yahoo Finance)  │────────────┘                       │            │
│  └────────┬─────────┘                                      │          │
│           │                                                │          │
│           └──────────────────┬─────────────────────────────┘          │
│                              │                                        │
│                     ┌────────▼────────┐                               │
│                     │  orchestrator   │                               │
│                     │  (logging,      │                               │
│                     │   locking,      │                               │
│                     │   coordination) │                               │
│                     └─────────────────┘                               │
│                                                                       │
│  Log: logs/ingestion.log   │   Lock: /tmp/signaliq_*.lock (O_EXCL)   │
└─────────────────────────────────┬─────────────────────────────────────┘
                                  │
                                  ▼
                          Layer 2 (PostgreSQL)
                     raw.prices · raw.news_headlines
                     ops.ingestion_runs · config.*
```

Data flows: fetch → normalize → write (with run ID traceability). The
orchestrator owns transactions, logging, and concurrency control.

---

## Key Design Decisions (v2.0)

| Decision | Rationale |
|----------|-----------|
| `requests` only (no `yfinance`) | Control over API surface; zero abstraction leakage |
| Yahoo chart API (`range=1d`) | Single-day fetch; history is Layer 2's warm-up |
| RSS via `feedparser` | Standard; handles `authors[]`, `published_parsed`, bozo |
| `fetch_with_retry` as shared utility | One retry policy across prices and news; DRY |
| NFKC unicode normalization | Handles scraped content edge cases (ligatures, full-width) |
| Generic query param extraction | Works with any RSS source, not Yahoo-specific |
| Pipe-delimited logging | `cut -d'|'` parseable; structured enough for scripts |
| O_EXCL lock acquisition | Atomic; no TOCTOU race on lock check |
| Price = transactional, News = not | Prices are a snapshot; headlines are independent records |
| Named SQL params (dict) | 12+ param functions are unreadable with positional args |
| Empty headline counting | Silent data loss is worse than noisy logs |
| Author from `authors[].name` | feedparser normalizes `dc:creator` and `<author>` into `authors[]` |
| Dry-run = same network, no DB | Tests network path without committing data |

---

## Integration Points

### With Layer 2

- `writer.py` calls `raw.insert_price_record()` and `raw.insert_headline_record()`
- `writer.get_source_id()` queries `config.news_sources`
- `orchestrator.py` creates UUIDs traceable to `ops.ingestion_runs`
- Config tables must be populated (6 news sources, 5 asset aliases)

### With Layer 3

- `config/entity_aliases.json` is consumed by `layer3_entity.py` EntityResolver
- Layer 1 does NOT interact with Layer 3 directly — data flows L1 → L2 → L3
- Headlines in L2 have no ticker attribution; L3's alias matching handles it

### With automation

- Cron jobs installed by `scripts/install_crontab.sh`
- Logs rotated by `scripts/rotate_logs.sh`
- Lock files prevent overlapping runs (O_EXCL atomic creation)

---

## File Inventory

| File | Lines | Role |
|------|-------|------|
| `layer1/http_client.py` | 75 | Shared HTTP fetch with retry |
| `layer1/collect_prices.py` | 115 | Yahoo Finance price fetching |
| `layer1/collect_news.py` | 211 | RSS news collection with observability |
| `layer1/writer.py` | 96 | PostgreSQL atomic writes (named params) |
| `layer1/orchestrator.py` | 214 | Coordination, O_EXCL locks, logging |
| `scripts/install_crontab.sh` | 24 | Idempotent crontab installer |
| `scripts/rotate_logs.sh` | 16 | Daily log rotation, 90-day retention |
| `config/entity_aliases.json` | 7 | Alias entries for Layer 3 (5 tickers) |
| `requirements_layer1.txt` | 3 | Python dependencies |
| `.env.example` | 2 | Database URL template |
| `tests/test_layer1_integration.py` | 434 | 15 mock-based tests |

---

## Test Results

```
=== TEST 1: HTTP Retry ===                                      7 PASS
=== TEST 2: Fetch Prices (mock API) ===                         9 PASS
=== TEST 3: Dry-run preserves network behavior ===               2 PASS
=== TEST 4: All assets fail → sys.exit(1) ===                    1 PASS
=== TEST 5: Query param extraction ===                           4 PASS
=== TEST 6: URL hash normalization ===                           2 PASS
=== TEST 7: Unicode normalization (NFKC) ===                     3 PASS
=== TEST 8: Author resolution ===                                2 PASS
=== TEST 9: Empty headline counting ===                          3 PASS
=== TEST 10: Atomic lock with O_EXCL ===                         3 PASS
=== TEST 11: Logging Format ===                                  7 PASS
=== TEST 12: Write Price (mock DB) ===                           7 PASS
=== TEST 13: Write Headline (mock DB) ===                        7 PASS
=== TEST 14: Price ingestion is transactional ===                 2 PASS
=== TEST 15: News partial failure ===                            2 PASS
                                                                ──────
ALL TESTS PASSED                                                61 checks
```

Cross-layer verification:
- Layer 3 (16 tests): ALL PASSED
- Layer 4 (15 tests): ALL PASSED
- Pipeline demo (20-day synthetic run): 30 NDI signals, 2 ACTIVE

---

## Status

```
Layer 1:  BUILD COMPLETE (v2.0) — 5 modules, 5 artifacts, 15 tests, 61 checks
Layer 2:  BUILD COMPLETE  — 10 tables, 2 views, 13 functions, 6 triggers, 4 roles
Layer 3:  BUILD COMPLETE  — 5 modules, 16 tests, DB connector, pipeline
Layer 4:  BUILD COMPLETE  — 4 sublayers, 15 tests, 12-field output schema
Layer 5:  NOT STARTED     — AI processing
Layer 6:  NOT STARTED     — Presentation
```
