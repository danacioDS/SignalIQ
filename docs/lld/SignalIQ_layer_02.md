# SignalIQ Layer 2: Low-Level Design

## Overview

Layer 2 is the **persistence layer** — the only layer that writes to disk. It serves as the immutable source of truth for all downstream calculations.

**Core Principle:** Layer 2 stores exactly what Layer 1 collects. No transformations. No aggregations. No business logic. Writes are append-only for business data, with explicit operational exceptions for metadata.

---

## Design Assumptions (Explicit)

| # | Assumption | Rationale |
|---|------------|-----------|
| 1 | PostgreSQL is sufficient for MVP volume | ~10K headlines/day → ~3.6M/year → trivial |
| 2 | No vector storage needed in MVP | Embeddings are Layer 5 (AI), not Layer 2 |
| 3 | No partitioning in MVP | Premature complexity; add at ~50M rows if needed |
| 4 | Append-only for business data prevents corruption | No UPDATE or DELETE on prices, headlines |
| 5 | Operational tables may be updated | Ingestion runs, health metrics, configuration audit |
| 6 | Every business data row has traceability | Ingestion run ID + content hash + source snapshot |
| 7 | Historical analysis requires source metadata snapshots | Future config changes must not corrupt past calculations |

---

## Database Schema Structure

Three schemas within the `signaliq` database:

| Schema | Purpose | Write Pattern |
|--------|---------|---------------|
| `raw` | Immutable business data | Append-only (strict) |
| `ops` | Operational monitoring | Append + update (ingestion tracking) |
| `config` | Configuration and audit | Updateable with audit trail |

---

## Schema 1: `raw` (Immutable Business Data)

### Table: `prices`

**Purpose:** Immutable price records from all vendors.

| Field | Type | Description |
|-------|------|-------------|
| id | BigSerial | Surrogate key |
| ticker | String(20) | 'NVDA', 'AAPL', 'SPX', 'BTC-USD' |
| vendor | String(30) | 'yahoo_finance', 'alpha_vantage' |
| date | Date | Trading date (Eastern Time) |
| open | Numeric(12,4) | Opening price |
| high | Numeric(12,4) | Daily high |
| low | Numeric(12,4) | Daily low |
| close | Numeric(12,4) | Unadjusted close |
| adj_close | Numeric(12,4) | **Primary field for calculations** |
| volume | BigInt | Trading volume |
| is_correction | Boolean | If true, this record supersedes a previous one |
| supersedes_id | BigInt | References the id of the record being corrected |
| ingestion_run_id | UUID | References ops.ingestion_runs |
| extracted_at | Timestamp | When this row was written |
| content_hash | String(64) | SHA256 of normalized price record |

**Database Constraints:**
- `CHECK (adj_close > 0)`
- `CHECK (volume >= 0 OR volume IS NULL)`
- `CHECK (date <= CURRENT_DATE)`
- `CHECK (is_correction = false OR supersedes_id IS NOT NULL)`

**Uniqueness Constraint:** `(ticker, vendor, date, is_correction)` with the rule that only one non-correction record may exist per (ticker, vendor, date). Multiple corrections are allowed and chain via `supersedes_id`.

**Correction Handling:**

| Scenario | Action |
|----------|--------|
| First price for (ticker, vendor, date) | Insert with `is_correction = false`, `supersedes_id = NULL` |
| Vendor issues corrected price | Insert new record with `is_correction = true`, `supersedes_id` pointing to previous record |
| Layer 3 reads prices | Uses view `latest_prices` (see below) |

**Content Hash Generation:**
```text
Normalize: ticker|vendor|date|adj_close|volume
Apply: SHA256
```

**Indexes:**
- `(ticker, date, is_correction, extracted_at)` for time-series queries
- `(ticker, vendor, date, is_correction)` for uniqueness
- `ingestion_run_id` for audit
- `content_hash` for deduplication

---

### View: `latest_prices` (Performance Optimization)

**Purpose:** Provides the effective price for each (ticker, date) without Layer 3 writing complex subqueries.

**Logic:**
```sql
-- For each ticker and date:
-- If a correction exists, use the most recent correction
-- Otherwise, use the non-correction record
```

**Why a view:** Prevents every Layer 3 query from implementing correction resolution logic. The database handles it once, centrally.

---

### Table: `news_headlines`

**Purpose:** Immutable headline storage from all RSS/news sources.

**Critical Design Decision:** Snapshot source metadata (`source_name`, `source_tier`) at ingestion time. Future changes to `config.news_sources` must not alter historical analysis.

| Field | Type | Description |
|-------|------|-------------|
| id | BigSerial | Surrogate key |
| source_id | Integer | References config.news_sources.id (for lineage, not for tier) |
| source_name_snapshot | String(50) | Name of source at ingestion time |
| source_tier_snapshot | SmallInt | Tier (1,2,3) at ingestion time |
| headline | Text | The headline text (non-empty) |
| article_url | String(500) | Full URL if available |
| published_at | Timestamp | Source's timestamp (can be NULL) |
| ingested_at | Timestamp | When SignalIQ received it |
| author | String(200) | Byline if available |
| content_snippet | Text | First 500 chars of article body |
| ingestion_run_id | UUID | References ops.ingestion_runs |
| url_hash | String(64) | SHA256 of normalized article_url |
| headline_hash | String(64) | SHA256 of normalized headline text |

**Database Constraints:**
- `CHECK (headline <> '')`
- `CHECK (source_tier_snapshot IN (1,2,3))`

**Uniqueness Constraint:** `(source_id, url_hash)` prevents duplicate URLs from same source.

**Hash Generation:**

URL hash:
```text
Normalize: lowercase(trim(article_url))
Apply: SHA256
```

Headline hash:
```text
Normalize: lowercase → trim → collapse multiple spaces → remove punctuation
Apply: SHA256
```

**Why snapshot source metadata:** Without it, changing `config.news_sources.tier` from 1 to 2 would retroactively change historical sentiment weighting. This would corrupt backtesting and time-series analysis.

**Indexes:**
- `published_at` for time-window queries
- `url_hash` for deduplication
- `headline_hash` for cross-source duplicate detection (Layer 3 uses this)
- `ingestion_run_id` for audit
- `source_tier_snapshot` for filtering

**Storage Note:** `content_snippet` is MVP-only. Post-MVP, full article text would require separate storage.

---

## Schema 2: `ops` (Operational Monitoring)

### Table: `ingestion_runs`

**Purpose:** Audit log of every data collection execution.

**Retention Decision:** Keep records forever to maintain foreign key integrity with `raw.prices` and `raw.news_headlines`. Size is negligible (~36K rows/year at 100 runs/day).

| Field | Type | Description |
|-------|------|-------------|
| run_id | UUID | Primary key, auto-generated |
| source_type | String | 'prices', 'news', 'macro' |
| source_name | String | 'yahoo_finance', 'reuters_rss' |
| started_at | Timestamp | When collection began (immutable) |
| completed_at | Timestamp | When collection finished (UPDATABLE) |
| status | String | 'running', 'success', 'failed', 'partial' (UPDATABLE) |
| records_inserted | Integer | Count of rows written (UPDATABLE) |
| error_message | Text | Null if success (UPDATABLE) |
| metadata | JSON | Flexible: rate limits, pagination tokens |

**Database Constraints:**
- `CHECK (status IN ('running', 'success', 'failed', 'partial'))`

**Update Rule:** Only `completed_at`, `status`, `records_inserted`, and `error_message` may be updated.

**Indexes:**
- `(source_type, source_name)` for operational queries
- `started_at` for time-range analysis
- `status` for monitoring failed runs

---

### Table: `ingestion_health`

**Purpose:** Track data quality and completeness over time. **Required for production monitoring.**

| Field | Type | Description |
|-------|------|-------------|
| id | BigSerial | Primary key |
| source_type | String | 'prices', 'news', 'macro' |
| source_name | String | 'yahoo_finance', 'reuters_rss' |
| date | Date | Date of expected data |
| expected_count | Integer | Expected number of records (e.g., 5 prices for 5 assets) |
| received_count | Integer | Actual records ingested |
| status | String | 'complete', 'partial', 'missing', 'failed' |
| duplicate_count | Integer | Number of duplicates rejected |
| details | JSON | Additional context (e.g., which tickers missing) |
| calculated_at | Timestamp | When this health check was computed |

**Database Constraints:**
- `CHECK (expected_count >= 0)`
- `CHECK (received_count >= 0)`
- `CHECK (status IN ('complete', 'partial', 'missing', 'failed'))`

**Calculation Frequency:** Daily after all ingestion completes.

**Status Determination:**

| Condition | Status |
|-----------|--------|
| received_count >= expected_count * 0.95 | 'complete' |
| received_count >= expected_count * 0.50 | 'partial' |
| received_count > 0 but < expected_count * 0.50 | 'missing' |
| received_count = 0 | 'failed' |

**Indexes:**
- `(source_type, source_name, date)` for trend analysis
- `status` for alerting

---

### Table: `macro_indicators` (Post-MVP Placeholder)

**Purpose:** Reserve for future macro data.

| Field | Type | Description |
|-------|------|-------------|
| id | BigSerial | Surrogate key |
| indicator_name | String | 'DXY', 'US10Y', 'GOLD', 'OIL' |
| vendor | String | 'fred', 'bloomberg' |
| date | Date | Observation date |
| value | Numeric(12,4) | Indicator value |
| ingestion_run_id | UUID | References ops.ingestion_runs |

**MVP Status:** Table defined but not populated.

---

## Schema 3: `config` (Configuration & Audit)

### Table: `monitored_assets`

**Purpose:** Defines which assets the system actively monitors.

**MVP Scope:** Equity, index, and crypto only.

| Field | Type | Description |
|-------|------|-------------|
| id | Integer | Primary key |
| ticker | String(20) | Primary identifier, unique |
| asset_class | String | 'equity', 'index', 'crypto' |
| name | String(200) | Human-readable |
| is_active | Boolean | If false, skip collection |
| added_at | Date | When monitoring began |
| notes | Text | Internal comments |

**Database Constraints:**
- `CHECK (asset_class IN ('equity', 'index', 'crypto'))`

**MVP Active Assets:**
- NVDA (equity)
- AAPL (equity)
- MSFT (equity)
- SPX (index)
- BTC-USD (crypto)

**Indexes:**
- `ticker` (unique)
- `is_active` for filtering

---

### Table: `asset_aliases`

**Purpose:** Maps natural language terms to canonical tickers.

| Field | Type | Description |
|-------|------|-------------|
| id | Integer | Primary key |
| ticker | String(20) | References monitored_assets.ticker |
| alias | String(100) | Natural language term |
| match_priority | Integer | Lower = higher priority (1 = URL param) |
| is_case_sensitive | Boolean | False for MVP |
| min_length | Integer | Minimum alias length (default 3) |

**Database Constraints:**
- `CHECK (match_priority >= 1)`
- `CHECK (min_length >= 1)`
- `CHECK (alias <> '')`

**Example Data:**

| ticker | alias | match_priority |
|--------|-------|----------------|
| NVDA | NVIDIA | 10 |
| NVDA | Nvidia | 10 |
| AAPL | Apple | 10 |
| MSFT | Microsoft | 10 |
| SPX | S&P 500 | 10 |
| BTC-USD | Bitcoin | 10 |

**Indexes:**
- `alias` (btree)
- `ticker` for reverse lookup

---

### Table: `news_sources`

**Purpose:** Defines RSS feeds and their metadata.

**Note:** Changes to this table do not affect historical headlines because `raw.news_headlines` snapshots `source_name` and `source_tier` at ingestion time.

| Field | Type | Description |
|-------|------|-------------|
| id | Integer | Primary key |
| name | String(50) | 'Reuters', 'CNBC', 'AP' |
| url | String(500) | RSS feed URL |
| tier | Integer | 1 = high, 2 = medium, 3 = low |
| is_active | Boolean | If false, skip collection |
| rate_limit_seconds | Integer | Minimum seconds between requests |
| last_fetched_at | Timestamp | When this source was last polled |
| fetch_failures | Integer | Consecutive failure count |
| expected_daily_volume | Integer | Baseline for health monitoring |
| metadata | JSON | Headers, auth tokens |

**Database Constraints:**
- `CHECK (tier IN (1,2,3))`
- `CHECK (rate_limit_seconds >= 0)`
- `CHECK (expected_daily_volume >= 0)`

**MVP Active Sources:**
- Reuters (tier 1, expected: 500)
- Associated Press (tier 1, expected: 400)
- CNBC (tier 1, expected: 300)
- Yahoo Finance General (tier 2, expected: 200)
- Yahoo Finance Ticker (tier 2, expected: 100)
- MarketWatch (tier 2, expected: 200)

**Indexes:**
- `is_active + last_fetched_at` for scheduler

---

### Table: `ticker_vendor_mapping`

**Purpose:** Maps SignalIQ tickers to vendor-specific symbols.

| Field | Type | Description |
|-------|------|-------------|
| id | Integer | Primary key |
| ticker | String(20) | References monitored_assets.ticker |
| vendor | String(30) | 'yahoo_finance', 'alpha_vantage' |
| vendor_symbol | String(50) | Vendor's symbol |
| is_primary | Boolean | Preferred source |

**Database Constraints:**
- `CHECK (vendor IN ('yahoo_finance', 'alpha_vantage'))` — expand as needed

**Example:**

| ticker | vendor | vendor_symbol | is_primary |
|--------|--------|---------------|------------|
| NVDA | yahoo_finance | NVDA | True |
| SPX | yahoo_finance | ^GSPC | True |
| BTC-USD | yahoo_finance | BTC-USD | True |

**Indexes:**
- `(vendor, vendor_symbol)` for reverse lookups
- `(ticker, is_primary)` for quick access

---

### Table: `config_change_log`

**Purpose:** Audit trail for all configuration changes. **Required for governance.**

| Field | Type | Description |
|-------|------|-------------|
| id | BigSerial | Primary key |
| changed_at | Timestamp | When change occurred |
| changed_by | String(100) | User or process name |
| table_name | String(50) | Which config table changed |
| record_id | Integer | ID of the changed record |
| old_value | JSONB | Complete old record (NULL for insert) |
| new_value | JSONB | Complete new record (NULL for delete) |
| change_type | String | 'insert', 'update', 'delete' |

**Database Constraints:**
- `CHECK (change_type IN ('insert', 'update', 'delete'))`
- `CHECK ((change_type = 'insert' AND old_value IS NULL AND new_value IS NOT NULL) OR (change_type = 'delete' AND old_value IS NOT NULL AND new_value IS NULL) OR (change_type = 'update' AND old_value IS NOT NULL AND new_value IS NOT NULL))`

**Population Rule:** Database trigger stores complete before/after state as JSONB.

**Indexes:**
- `(table_name, record_id)` for record history
- `changed_at` for time-range queries

---

## Write Patterns

### Pattern 1: Price Ingestion

**Process:**
1. Layer 1 calls Layer 2 with batch of price records
2. Begin transaction
3. Create `ingestion_runs` record with status 'running'
4. For each price record:
   - Validate fields (application + database constraints)
   - Generate `content_hash`
   - Check if this is a correction (vendor flag or existing record with same ticker/vendor/date)
   - If correction: set `is_correction = true`, populate `supersedes_id`
   - If not correction and record exists: reject with error (no overwriting)
   - Insert into `prices`
5. Update `ingestion_runs` with counts and status 'success'
6. Commit transaction
7. On failure: rollback, update `ingestion_runs` with error

**Correction Detection:** Vendor provides `is_correction` flag in API response, OR Layer 1 detects that a previously ingested price differs from a new pull for the same (ticker, vendor, date).

---

### Pattern 2: News Ingestion

**Process:**
1. Layer 1 calls Layer 2 with batch of headlines
2. Begin transaction
3. Create `ingestion_runs` record
4. For each headline:
   - Look up source from `config.news_sources` by name
   - Snapshot `source.name` as `source_name_snapshot`
   - Snapshot `source.tier` as `source_tier_snapshot`
   - Generate `url_hash` and `headline_hash`
   - Check uniqueness on `(source_id, url_hash)`
   - Insert into `news_headlines`
5. Update `ingestion_runs` and commit
6. On duplicate URL: skip, increment duplicate_count, continue batch

**Critical:** The snapshot occurs at insertion time. Future changes to `news_sources.tier` do not retroactively affect historical headlines.

---

### Pattern 3: Health Metrics Calculation

**Process (daily after ingestion):**
1. For each `source_type` and `source_name`:
   - Get `expected_count` from config (or derive from 30-day average for sources without explicit expectations)
   - Query `received_count` from raw tables for the date
   - Calculate `duplicate_count` from ingestion run logs
   - Determine status using threshold rules
   - Insert into `ingestion_health`
2. If any source shows status 'missing' or 'failed' for 3 consecutive days → external alert

---

### Pattern 4: Configuration Changes

**Process:**
1. Admin runs configuration update script
2. Begin transaction
3. Validate referential integrity
4. Perform INSERT, UPDATE, or DELETE on config table
5. Database trigger automatically stores complete old/new JSONB to `config_change_log`
6. Commit transaction

**Note:** Changes to `news_sources.tier` affect future ingestion snapshots but not historical headlines. This is intentional and correct.

---

## Read Patterns (Layer 3 Queries)

### Query 1: Get Prices for Last N Days

**Parameters:** `ticker`, `end_date`, `window_days` (20)

**Returns:** List of `(date, adj_close)` sorted ascending

**Implementation:** Query the `latest_prices` view (not the raw table). The view handles correction resolution automatically.

**Performance:** ~10ms with indexes on `(ticker, date, is_correction, extracted_at)`

---

### Query 2: Get Headlines for a Date Range

**Parameters:** `start_date`, `end_date`, `tier_filter` (optional)

**Returns:** List of `(headline, published_at, source_tier_snapshot, author, headline_hash)`

**Note:** Entity resolution (headline → ticker) happens in Layer 3, not Layer 2. The `source_tier_snapshot` field enables historical weighting without consulting current config.

---

### Query 3: Get Latest Configuration

**Parameters:** None

**Returns:** All active assets, aliases, sources, vendor mappings

**Frequency:** Once per application startup (cached in Layer 3)

---

### Query 4: Check Ingestion Health

**Parameters:** `source_name`, `date_range`

**Returns:** `expected_count`, `received_count`, `status` for each day

**Purpose:** Layer 3 uses this for confidence scoring (High/Medium/Low/Crisis)

---

## Data Retention Policy

| Table | Retention | Notes |
|-------|-----------|-------|
| `prices` | Forever | Business data |
| `news_headlines` | Forever | Business data |
| `ingestion_runs` | Forever | Maintains FK integrity with business tables |
| `ingestion_health` | 2 years | Trend analysis |
| `macro_indicators` | Forever | Business data (post-MVP) |
| `monitored_assets` | Forever | Small |
| `asset_aliases` | Forever | Small |
| `news_sources` | Forever | Small |
| `ticker_vendor_mapping` | Forever | Small |
| `config_change_log` | Forever | Governance audit |

**Why `ingestion_runs` retained forever:** `prices` and `news_headlines` reference `ingestion_run_id` via foreign key. Deleting ingestion runs would break referential integrity. Size is negligible (~36K rows/year).

---

## Backup Strategy

| Component | Frequency | Retention | Location |
|-----------|-----------|-----------|----------|
| Full database dump | Daily | 30 days | Separate volume |
| WAL archives | Continuous | 7 days | Same volume |
| Configuration exports | After each change | Forever | Git repository |

**RPO:** 24 hours | **RTO:** 4 hours

---

## Health Monitoring Alerts

| Condition | Threshold | Action |
|-----------|-----------|--------|
| Source missing | 3 consecutive days | Email admin |
| Partial ingestion | <80% of expected | Log warning |
| High duplicate rate | >30% of incoming | Investigate source |
| No ingestion runs | 24 hours with zero runs | Critical alert |

---

## Security & Access Control

| Role | Permissions |
|------|-------------|
| Layer 1 (ETL) | INSERT on `raw.*`, `ops.*`; SELECT on `config.news_sources` |
| Layer 3 (Intelligence) | SELECT on `raw.*`, `ops.ingestion_health`, `config.*` |
| Admin (manual) | Full access to `config.*`; SELECT on `raw.*`, `ops.*` |
| Monitoring | SELECT on `ops.ingestion_health` |

---

## Performance Expectations (MVP)

| Metric | Target |
|--------|--------|
| Price insert rate | ~50 records/second |
| News insert rate | ~100 records/second |
| Query: 20-day price history (via view) | <15ms |
| Query: 1-day headlines | <50ms |
| Total database size (1 year) | ~500MB (prices) + ~2GB (headlines) |
| Autovacuum | Enabled, tuned |

**No partitioning in MVP.** PostgreSQL handles ~3.6M headlines/year easily. Re-evaluate at 50M rows.

---

## Migration Strategy

**Rule:** All schema changes require versioned migration file.

**Naming:** `YYYYMMDD_HHMM_description.sql`

**Safety Rules:**
- `CREATE TABLE` → safe
- `ALTER TABLE ADD COLUMN` → safe (with DEFAULT if NOT NULL)
- `CREATE INDEX` → use `CONCURRENTLY` in production
- `DROP COLUMN` → verify no dependencies first
- Never drop a column or table without two-week deprecation warning
- Changes to `news_sources.tier` are safe (snapshots protect history)

---

## What Layer 2 Explicitly Does NOT Do

| Not in Layer 2 | Where it belongs |
|----------------|------------------|
| Sentiment scoring | Layer 3 |
| Entity resolution | Layer 3 |
| NDI calculation | Layer 4 |
| Derived tables / materialized views | Not in MVP |
| Data aggregation | Layer 3 or 4 |
| Caching | Layer 3 or 6 |
| Vector embeddings | Layer 5 |
| Correction resolution logic | `latest_prices` view (in database) |

---

## Integration Points

**Upstream (Layer 1):**
- Batch of price records (vendor, ticker, date, OHLCV, is_correction flag)
- Batch of headline records (source name, headline, url, timestamp)

**Downstream (Layer 3):**
- Historical prices via `latest_prices` view
- Headlines by date range (with source_tier_snapshot)
- Configuration query
- Ingestion health query

**Contract:** Layer 3 does not write to Layer 2.

---

## Known Limitations (Documented)

| Limitation | Mitigation |
|------------|------------|
| No cross-source headline deduplication | Layer 3 uses `headline_hash` to filter |
| No full-text search | Post-MVP: pg_trgm or Elasticsearch |
| UTC timestamps only | Application layer converts to ET |
| No connection pooling | Post-MVP: PgBouncer |
| No automated alerting | External tool reads `ingestion_health` |
| No partitioning | Add at 50M rows if needed |
| `headline_hash` = exact-ish, not semantic | Documented; not a bug |

---

## Setup Checklist

- [ ] Create database `signaliq`
- [ ] Create schemas: `raw`, `ops`, `config`
- [ ] Create all 10 tables
- [ ] Create `latest_prices` view
- [ ] Create all indexes (use CONCURRENTLY in production)
- [ ] Add all CHECK constraints
- [ ] Create `config_change_log` trigger (JSONB version)
- [ ] Insert MVP configuration:
  - [ ] 5 assets (equity/index/crypto only)
  - [ ] 10+ aliases
  - [ ] 6 news sources with expected_daily_volume
  - [ ] Ticker-vendor mappings
- [ ] Create Layer 1 user (INSERT on raw/ops, SELECT on config.news_sources)
- [ ] Create Layer 3 user (SELECT on raw/ops.ingestion_health/config)
- [ ] Enable autovacuum
- [ ] Configure daily backup
- [ ] Test: Insert price, headline, verify
- [ ] Test: Insert correction, verify `latest_prices` view
- [ ] Test: Update news_sources tier, verify snapshot behavior
- [ ] Run initial `ingestion_health` population
- [ ] Verify `config_change_log` captures changes

---

## Design Decision Summary

| Decision | Rationale |
|----------|-----------|
| No partitioning in MVP | Premature complexity; PostgreSQL handles 3.6M rows/year easily |
| Three schemas (raw/ops/config) | Clean separation: business data vs operational vs configuration |
| `latest_prices` view | Centralizes correction logic; prevents repeated complex subqueries |
| Source metadata snapshots | Future config changes don't corrupt historical analysis |
| JSONB config change log | Simpler than field-level; captures complete state atomically |
| SHA256 throughout | Industry standard; no future migration needed |
| `ingestion_runs` retained forever | Maintains FK integrity; negligible size |
| CHECK constraints in database | Defense in depth; never trust applications completely |

---

## Layer 2 Status: READY FOR IMPLEMENTATION

> All review feedback incorporated: three schemas, no premature partitioning, correction handling with `latest_prices` view, source metadata snapshots, JSONB audit log, CHECK constraints, `ingestion_runs` retained forever. Ready for engineering handoff.

---

**SignalIQ** 🔹

*Layer 2 LLD Final v3 — Production-aware persistence layer. Snapshotted source metadata. Correction-ready via view. CHECK constraints. Forever retention for FK integrity. Ready to build.*
