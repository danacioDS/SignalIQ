# SignalIQ: Layer 2 Specification (MVP-Ready Revision)

## Storage Schema for a Production-Shaped MVP

---

### What Changed from Previous Version

| Area | Original | MVP-Ready Revision |
|------|----------|-------------------|
| **Vendor mapping** | Full multi-vendor architecture | Single vendor (Yahoo Finance) with table preserved |
| **Asset aliases** | regex/contains/exact with case sensitivity | Simple alias matching (ILIKE in Layer 3) |
| **News sources** | availability_score, influence_weight | Active + execution_order only; other fields deferred |
| **stale_flag** | Stored in prices table | Removed (Layer 3 logic, not storage) |
| **Traceability** | None | Added `source_record_id` and `ingestion_run_id` |
| **Derived schema** | Placeholder | Confirmed deferred (post-MVP) |

**Philosophy:** Production schema shape + MVP execution simplicity. Layer 2 is an append-only event store with query-optimized indexes.

---

### The Operating Principle for Layer 2 (MVP)

> **Layer 2 stores everything Layer 1 collects and serves everything Layer 3 needs. It does not transform, aggregate, or encode domain logic. It is an append-only ingestion ledger, not an intelligent cache.**

---

### Schema Organization

| Schema | Purpose | MVP Tables |
|--------|---------|------------|
| `raw` | Immutable ingested data | `prices`, `news_headlines`, `ingestion_runs` |
| `config` | Configuration (minimal) | `monitored_assets`, `asset_aliases`, `news_sources`, `ticker_vendor_mapping` |

`derived` schema is **excluded from MVP**. All aggregations happen in Layer 3 or Layer 4 application code.

---

## Schema: `raw`

### Table: `raw.prices`

Stores daily adjusted closing prices. Append-only. Never updated.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | BIGSERIAL | PRIMARY KEY | Surrogate key |
| ticker | VARCHAR(20) | NOT NULL | Internal ticker symbol |
| date | DATE | NOT NULL | Trading day |
| adj_close | NUMERIC(12,4) | NOT NULL | Adjusted closing price |
| source | VARCHAR(50) | NOT NULL | Data provider (MVP: only 'yfinance') |
| source_record_id | TEXT | NULL | Raw identifier from source (e.g., Yahoo's internal ID) |
| ingestion_run_id | UUID | NOT NULL | Links to `raw.ingestion_runs.run_id` |
| ingested_at | TIMESTAMPTZ | NOT NULL DEFAULT NOW() | When this record was inserted |

**Constraints:**
- `UNIQUE(ticker, date, source)` — prevents duplicate ingestion

**Indexes:**
- `INDEX idx_prices_ticker_date (ticker, date)` — Layer 3 primary read pattern
- `INDEX idx_prices_ingestion_run (ingestion_run_id)` — traceability

**Notes:**
- `source_record_id` enables replay debugging and feed repair
- No `stale_flag` — that logic belongs in Layer 3
- Single source only in MVP; schema supports multiple for future

---

### Table: `raw.news_headlines`

Stores raw headlines. Append-only. Never updated.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | BIGSERIAL | PRIMARY KEY | Surrogate key |
| headline | TEXT | NOT NULL | Raw headline text (exactly as received) |
| normalized_headline | TEXT | NOT NULL | Lowercase, stripped, whitespace-normalized |
| headline_hash | VARCHAR(64) | NOT NULL | SHA256 of normalized_headline |
| published_at | TIMESTAMPTZ | NULL | Publication timestamp (may be missing) |
| source | VARCHAR(50) | NOT NULL | Source name (matches `config.news_sources.name`) |
| source_asset | VARCHAR(20) | NULL | Asset hint from ticker feed (e.g., "NVDA") |
| url | TEXT | NOT NULL | Canonical URL |
| source_record_id | TEXT | NULL | Raw identifier from feed (e.g., RSS guid) |
| ingestion_run_id | UUID | NOT NULL | Links to `raw.ingestion_runs.run_id` |
| ingested_at | TIMESTAMPTZ | NOT NULL DEFAULT NOW() | When this record was inserted |

**Constraints:**
- `UNIQUE(headline_hash, source)` — prevents exact duplicate from same source

**Indexes:**
- `INDEX idx_news_source_ingested (source, ingested_at)` — Layer 1 fetch pattern
- `INDEX idx_news_published_at (published_at)` — Layer 3 time-window queries
- `INDEX idx_news_ingestion_run (ingestion_run_id)` — traceability

**Effective timestamp rule (documented, not enforced in schema):**
> Layer 3 prioritizes `published_at`. If NULL, falls back to `ingested_at`.

---

### Table: `raw.ingestion_runs`

Tracks every ingestion batch for full traceability.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | BIGSERIAL | PRIMARY KEY | Surrogate key |
| run_id | UUID | NOT NULL DEFAULT gen_random_uuid() | Unique identifier for this ingestion run |
| started_at | TIMESTAMPTZ | NOT NULL | When ingestion began |
| finished_at | TIMESTAMPTZ | NULL | When ingestion completed |
| source_type | VARCHAR(20) | NOT NULL | 'prices' or 'news' |
| source_name | VARCHAR(50) | NOT NULL | Specific source (e.g., 'yfinance', 'Reuters') |
| records_found | INTEGER | DEFAULT 0 | Records retrieved |
| records_inserted | INTEGER | DEFAULT 0 | Records successfully inserted |
| status | VARCHAR(20) | NOT NULL | 'running', 'success', 'failed', 'partial' |
| error_message | TEXT | NULL | If failed or partial |
| metadata | JSONB | NULL | Context (duration_ms, retries, etc.) |

**Constraints:**
- `CHECK (status IN ('running', 'success', 'failed', 'partial'))`
- `CHECK (source_type IN ('prices', 'news'))`

**Indexes:**
- `INDEX idx_ingestion_run_id (run_id)` — primary lookup
- `INDEX idx_ingestion_status (status, started_at)` — health monitoring

**Why this matters for MVP:** When something breaks (and it will), you can trace every record to the exact ingestion batch that inserted it.

---

## Schema: `config`

### Table: `config.monitored_assets`

Explicit list of what the system tracks. MVP: 5 tickers.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| ticker | VARCHAR(20) | PRIMARY KEY | Internal ticker symbol |
| asset_type | VARCHAR(20) | NOT NULL | 'equity', 'index', 'commodity', 'fx', 'bond' |
| is_active | BOOLEAN | NOT NULL DEFAULT TRUE | If false, Layer 1 and Layer 3 skip |
| added_at | TIMESTAMPTZ | NOT NULL DEFAULT NOW() | When added |
| notes | TEXT | NULL | Internal notes |

**Constraints:**
- `CHECK (asset_type IN ('equity', 'index', 'commodity', 'fx', 'bond'))`

**MVP initial data:**
```sql
INSERT INTO config.monitored_assets (ticker, asset_type) VALUES
('NVDA', 'equity'),
('AAPL', 'equity'),
('MSFT', 'equity'),
('SPX', 'index'),
('BTC-USD', 'commodity');
```

---

### Table: `config.asset_aliases` (Simplified for MVP)

Maps asset names and common references to internal tickers. Used by Layer 3 for entity resolution.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | BIGSERIAL | PRIMARY KEY | Surrogate key |
| ticker | VARCHAR(20) | NOT NULL | References `monitored_assets.ticker` |
| alias | VARCHAR(100) | NOT NULL | Alternative name (case-insensitive matching) |

**Constraints:**
- `UNIQUE(ticker, alias)`

**Indexes:**
- `INDEX idx_asset_aliases_alias (alias)` — Layer 3 lookups

**MVP simplification:** No alias_type, no case_sensitive, no regex. Layer 3 uses simple `ILIKE` containment matching. Upgrade path exists by adding columns later.

**Example MVP data:**
```sql
INSERT INTO config.asset_aliases (ticker, alias) VALUES
('NVDA', 'NVIDIA'),
('NVDA', 'Nvidia'),
('NVDA', 'NVIDIA CORPORATION'),
('AAPL', 'Apple'),
('AAPL', 'Apple Inc.'),
('MSFT', 'Microsoft'),
('MSFT', 'Microsoft Corporation'),
('SPX', 'S&P 500'),
('SPX', 'S&P500'),
('BTC-USD', 'Bitcoin'),
('BTC-USD', 'BTC');
```

---

### Table: `config.news_sources` (Simplified for MVP)

Configuration for news sources. Complexity deferred.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Surrogate key |
| name | VARCHAR(50) | UNIQUE NOT NULL | Source name |
| rss_url | TEXT | NOT NULL | RSS feed URL |
| active | BOOLEAN | NOT NULL DEFAULT TRUE | If false, Layer 1 skips |
| is_ticker_feed | BOOLEAN | NOT NULL DEFAULT FALSE | If true, URL contains `{TICKER}` |
| execution_order | INTEGER | NOT NULL | Processing sequence |
| added_at | TIMESTAMPTZ | NOT NULL DEFAULT NOW() | When added |

**Indexes:**
- `INDEX idx_news_sources_active_order (active, execution_order)`

**Deferred fields (post-MVP):** `influence_weight`, `availability_score`, `last_successful_fetch`, `failure_count`

**MVP initial data:**
```sql
INSERT INTO config.news_sources (name, rss_url, is_ticker_feed, execution_order) VALUES
('Reuters Business', 'http://feeds.reuters.com/reuters/businessNews', false, 1),
('Associated Press', 'https://apnews.com/business.rss', false, 2),
('Yahoo Finance General', 'https://finance.yahoo.com/news/rssindex', false, 3),
('Yahoo Finance Ticker', 'https://finance.yahoo.com/rss/headline?s={TICKER}', true, 4),
('CNBC', 'https://www.cnbc.com/id/100003114/device/rss/rss.html', false, 5),
('MarketWatch', 'http://feeds.marketwatch.com/marketwatch/topstories/', false, 6);
```

---

### Table: `config.ticker_vendor_mapping` (Single Vendor for MVP)

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | BIGSERIAL | PRIMARY KEY | Surrogate key |
| internal_ticker | VARCHAR(20) | NOT NULL | References `monitored_assets.ticker` |
| vendor | VARCHAR(20) | NOT NULL | Vendor name |
| vendor_ticker | VARCHAR(20) | NOT NULL | Vendor-specific symbol |

**Constraints:**
- `UNIQUE(internal_ticker, vendor)`

**MVP reality:** Only one vendor (`yahoo`). Schema supports multiple for future.

**MVP data:**
```sql
INSERT INTO config.ticker_vendor_mapping (internal_ticker, vendor, vendor_ticker) VALUES
('NVDA', 'yahoo', 'NVDA'),
('AAPL', 'yahoo', 'AAPL'),
('MSFT', 'yahoo', 'MSFT'),
('SPX', 'yahoo', '^GSPC'),
('BTC-USD', 'yahoo', 'BTC-USD');
```

---

## Schema: `derived` (Explicitly Deferred)

**Not created in MVP.**

Post-MVP, this schema will contain pre-aggregated tables like:
- `derived.daily_sentiment`
- `derived.daily_momentum`
- `derived.ndi_history`

**Decision to defer is explicit, not implicit.** This prevents Layer 3 or Layer 4 from developing dependencies on pre-aggregated data that doesn't exist yet.

---

## Traceability: The Critical Addition

Every record in `raw.prices` and `raw.news_headlines` contains:
- `ingestion_run_id` → links to `raw.ingestion_runs`
- `source_record_id` → raw identifier from the source

**This enables:**
- Debugging: "Which ingestion batch inserted this bad headline?"
- Replay: Rerun a specific batch after fixing a parser bug
- Audit: Prove data lineage for compliance
- Repair: Delete or correct records from a specific run

For MVP with 5 tickers, this is **not overhead** — it's insurance.

---

## Data Retention (MVP)

| Table | Retention | Rationale |
|-------|-----------|-----------|
| `raw.prices` | Indefinite | Primary asset |
| `raw.news_headlines` | Indefinite | Primary asset |
| `raw.ingestion_runs` | 90 days | Operational; old runs not useful |
| `config.*` | Indefinite | Configuration |

**MVP simplification:** No automated purging in initial deployment. Manual cleanup is acceptable for 5 tickers.

---

## Security (MVP Simplification)

| Environment | Approach |
|-------------|----------|
| Development | Single user `signalq_app` with full access |
| Production (post-MVP) | Role separation as previously defined |

**MVP does not need role separation.** One database user is sufficient for a local or single-server deployment.

---

## Migration Strategy

All schema changes as incremental, version-controlled SQL scripts:

```
/migrations
  /001_create_raw_schema.sql
  /002_create_config_schema.sql
  /003_add_traceability_fields.sql
  /004_seed_mvp_data.sql
```

**Rule:** Every change is a new migration. No in-place edits.

---

## Example Queries (MVP)

### Layer 3: Get prices for NDI calculation

```sql
SELECT date, adj_close
FROM raw.prices
WHERE ticker = 'NVDA'
  AND date >= CURRENT_DATE - INTERVAL '252 days'
ORDER BY date;
```

### Layer 3: Get headlines for sentiment (last 5 days)

```sql
SELECT id, headline, normalized_headline, published_at, source, source_asset
FROM raw.news_headlines
WHERE (published_at >= CURRENT_DATE - INTERVAL '5 days'
   OR (published_at IS NULL AND ingested_at >= CURRENT_DATE - INTERVAL '5 days'))
ORDER BY published_at DESC NULLS LAST;
```

### Layer 3: Entity resolution lookup

```sql
SELECT ticker, alias
FROM config.asset_aliases;
-- Layer 3 applies ILIKE matching in application code
```

### Traceability: Find all records from a failed ingestion run

```sql
SELECT 'price' as record_type, ticker, date, source_record_id
FROM raw.prices
WHERE ingestion_run_id = 'abc123...'
UNION ALL
SELECT 'headline' as record_type, source, published_at::text, source_record_id
FROM raw.news_headlines
WHERE ingestion_run_id = 'abc123...';
```

---

## Summary: MVP-Ready Layer 2

| Area | Decision |
|------|----------|
| **Database** | PostgreSQL (any version >= 14) |
| **Schemas** | `raw` + `config` only (no `derived`) |
| **Tables** | 7 tables as specified |
| **Traceability** | `ingestion_run_id` + `source_record_id` on all raw tables |
| **Asset aliases** | Simple (ticker, alias) — no regex/type in MVP |
| **News sources** | Active + execution_order only — complexity deferred |
| **Vendor mapping** | Single vendor (yahoo) — schema supports future |
| **stale_flag** | Removed (Layer 3 logic) |
| **Derived tables** | Explicitly deferred |
| **Retention** | Indefinite for prices/headlines; 90 days for logs |
| **Migrations** | Incremental, version-controlled |

---

## The Golden Rule for Layer 2 (MVP-Ready)

> **Layer 2 is an append-only event store with query-optimized indexes. It stores everything, transforms nothing. It encodes no domain logic. It provides full traceability from signal back to ingestion batch. Derived tables are explicitly deferred. Complexity is deferred, not discarded — the schema has upgrade paths without migration chaos.**

---

**SignalIQ** 🔹

---

## Ready for Layer 3

Layer 3 will read from:
- `raw.prices` (252-day windows for momentum)
- `raw.news_headlines` (5-day windows for sentiment)
- `config.asset_aliases` (simple ILIKE entity resolution)
- `config.monitored_assets` (active tickers)

Layer 3 will write to: **Nothing in MVP**. All outputs calculated on the fly.

Do you want me to write **Layer 3: NLP + Technical Engine Specification** next?