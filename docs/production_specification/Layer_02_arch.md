---
# SignalIQ Layer 2: Production Specification (Final)

## The Core

> **Layer 2 is the persistence layer — the only layer that writes to disk. It serves as the immutable source of truth for all downstream calculations.**

**Core Principle:** Layer 2 stores exactly what Layer 1 collects. No transformations. No aggregations. No business logic. Writes are append-only for business data, with explicit operational exceptions for metadata.

**Status: READY FOR IMPLEMENTATION**

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

**Uniqueness:** `(ticker, vendor, date, is_correction)` with rule that only one non-correction record may exist per (ticker, vendor, date). Multiple corrections allowed, chained via `supersedes_id`.

**Content Hash Generation:**
```
Normalize: ticker|vendor|date|adj_close|volume
Apply: SHA256
```

**Indexes:**
- `(ticker, date, is_correction, extracted_at)` for time-series queries
- `(ticker, vendor, date, is_correction)` for uniqueness
- `ingestion_run_id` for audit
- `content_hash` for deduplication

---

### View: `latest_prices`

**Purpose:** Provides the effective price for each (ticker, date) without Layer 3 writing complex subqueries.

**Logic:** For each ticker and date: if correction exists, use most recent correction; otherwise use non-correction record.

**Why a view:** Prevents every Layer 3 query from implementing correction resolution logic. Database handles it once, centrally.

---

### Table: `news_headlines`

**Purpose:** Immutable headline storage from all RSS/news sources.

**Critical Design Decision:** Snapshot source metadata (`source_name`, `source_tier`) at ingestion time. Future changes to `config.news_sources` must not alter historical analysis.

| Field | Type | Description |
|-------|------|-------------|
| id | BigSerial | Surrogate key |
| source_id | Integer | References config.news_sources.id (for lineage) |
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

**Uniqueness:** `(source_id, url_hash)` prevents duplicate URLs from same source.

**Hash Generation:**

URL hash: `lowercase(trim(article_url))` → SHA256

Headline hash: `lowercase → trim → collapse multiple spaces → remove punctuation` → SHA256

**Why snapshot source metadata:** Without it, changing `config.news_sources.tier` from 1 to 2 would retroactively change historical sentiment weighting, corrupting backtesting and time-series analysis.

**Indexes:**
- `published_at` for time-window queries
- `url_hash` for deduplication
- `headline_hash` for cross-source duplicate detection
- `ingestion_run_id` for audit
- `source_tier_snapshot` for filtering

---

## Schema 2: `ops` (Operational Monitoring)

### Table: `ingestion_runs`

**Purpose:** Audit log of every data collection execution.

**Retention:** Keep forever to maintain foreign key integrity with `raw.prices` and `raw.news_headlines`. Size negligible (~36K rows/year at 100 runs/day).

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
| expected_count | Integer | Expected number of records |
| received_count | Integer | Actual records ingested |
| status | String | 'complete', 'partial', 'missing', 'failed' |
| duplicate_count | Integer | Number of duplicates rejected |
| details | JSON | Additional context |
| calculated_at | Timestamp | When this health check was computed |

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

**Purpose:** Reserve for future macro data. Table defined but not populated in MVP.

| Field | Type | Description |
|-------|------|-------------|
| id | BigSerial | Surrogate key |
| indicator_name | String | 'DXY', 'US10Y', 'GOLD', 'OIL' |
| vendor | String | 'fred', 'bloomberg' |
| date | Date | Observation date |
| value | Numeric(12,4) | Indicator value |
| ingestion_run_id | UUID | References ops.ingestion_runs |

---

## Schema 3: `config` (Configuration & Audit)

### Table: `monitored_assets`

**Purpose:** Defines which assets the system actively monitors.

| Field | Type | Description |
|-------|------|-------------|
| id | Integer | Primary key |
| ticker | String(20) | Primary identifier, unique |
| asset_class | String | 'equity', 'index', 'crypto' |
| name | String(200) | Human-readable |
| is_active | Boolean | If false, skip collection |
| added_at | Date | When monitoring began |
| notes | Text | Internal comments |

**MVP Active Assets:** NVDA, AAPL, MSFT, SPX, BTC-USD

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

**Example Data:**

| ticker | alias | match_priority |
|--------|-------|----------------|
| NVDA | NVIDIA | 10 |
| AAPL | Apple | 10 |
| MSFT | Microsoft | 10 |

---

### Table: `news_sources`

**Purpose:** Defines RSS feeds and their metadata.

**Note:** Changes to this table do not affect historical headlines because `raw.news_headlines` snapshots source metadata at ingestion time.

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

**MVP Active Sources:**
- Reuters (tier 1, expected: 500)
- Associated Press (tier 1, expected: 400)
- CNBC (tier 1, expected: 300)
- Yahoo Finance General (tier 2, expected: 200)
- Yahoo Finance Ticker (tier 2, expected: 100)
- MarketWatch (tier 2, expected: 200)

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

**Example:**

| ticker | vendor | vendor_symbol | is_primary |
|--------|--------|---------------|------------|
| NVDA | yahoo_finance | NVDA | True |
| SPX | yahoo_finance | ^GSPC | True |
| BTC-USD | yahoo_finance | BTC-USD | True |

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

**Population Rule:** Database trigger stores complete before/after state as JSONB.

---

## Write Patterns

### Pattern 1: Price Ingestion

1. Layer 1 calls Layer 2 with batch of price records
2. Begin transaction
3. Create `ingestion_runs` record with status 'running'
4. For each price record: validate, generate `content_hash`, detect corrections, insert
5. Update `ingestion_runs` with counts and status 'success'
6. Commit transaction
7. On failure: rollback, update `ingestion_runs` with error

**Correction Detection:** Vendor provides `is_correction` flag, OR Layer 1 detects that a previously ingested price differs from a new pull for same (ticker, vendor, date).

---

### Pattern 2: News Ingestion

1. Layer 1 calls Layer 2 with batch of headlines
2. Begin transaction
3. Create `ingestion_runs` record
4. For each headline: look up source, snapshot metadata, generate hashes, check uniqueness, insert
5. Update `ingestion_runs` and commit
6. On duplicate URL: skip, increment duplicate_count, continue batch

**Critical:** Snapshot occurs at insertion time. Future changes to `news_sources.tier` do not retroactively affect historical headlines.

---

### Pattern 3: Configuration Changes

1. Admin runs configuration update script
2. Begin transaction
3. Validate referential integrity
4. Perform INSERT, UPDATE, or DELETE on config table
5. Database trigger automatically stores complete old/new JSONB to `config_change_log`
6. Commit transaction

---

## Read Patterns (Layer 3 Queries)

### Query 1: Get Prices for Last N Days

**Implementation:** Query the `latest_prices` view (not the raw table). The view handles correction resolution automatically.

**Performance:** ~10ms with indexes on `(ticker, date, is_correction, extracted_at)`

### Query 2: Get Headlines for a Date Range

**Note:** Entity resolution (headline → ticker) happens in Layer 3, not Layer 2. The `source_tier_snapshot` field enables historical weighting without consulting current config.

### Query 3: Get Latest Configuration

**Frequency:** Once per application startup (cached in Layer 3)

### Query 4: Check Ingestion Health

**Purpose:** Layer 3 uses this for confidence scoring (High/Medium/Low/Crisis)

---

## Data Retention Policy

| Table | Retention |
|-------|-----------|
| `prices` | Forever |
| `news_headlines` | Forever |
| `ingestion_runs` | Forever (maintains FK integrity) |
| `ingestion_health` | 2 years |
| All config tables | Forever |

**Why `ingestion_runs` retained forever:** `prices` and `news_headlines` reference `ingestion_run_id` via foreign key. Deleting would break referential integrity. Size negligible (~36K rows/year).

---

## Backup Strategy

| Component | Frequency | Retention |
|-----------|-----------|-----------|
| Full database dump | Daily | 30 days |
| WAL archives | Continuous | 7 days |
| Configuration exports | After each change | Forever (Git) |

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

## Setup Checklist

- [ ] Create database `signaliq`
- [ ] Create schemas: `raw`, `ops`, `config`
- [ ] Create all 10 tables
- [ ] Create `latest_prices` view
- [ ] Create all indexes (use CONCURRENTLY in production)
- [ ] Add all CHECK constraints
- [ ] Create `config_change_log` trigger
- [ ] Insert MVP configuration (assets, aliases, sources, vendor mappings)
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
| No partitioning in MVP | PostgreSQL handles 3.6M rows/year easily |
| Three schemas (raw/ops/config) | Clean separation of concerns |
| `latest_prices` view | Centralizes correction logic |
| Source metadata snapshots | Future config changes don't corrupt history |
| JSONB config change log | Captures complete state atomically |
| `ingestion_runs` retained forever | Maintains FK integrity; negligible size |
| CHECK constraints in database | Defense in depth |

---

## Layer 2 Status: READY FOR IMPLEMENTATION

> Three schemas. Append-only business data. Correction handling via `latest_prices` view. Source metadata snapshots. JSONB audit log. CHECK constraints. Forever retention for FK integrity. Ready for engineering handoff.

---

**SignalIQ** 🔹

*Layer 2 Production Specification — Immutable persistence. Correction-ready. Snapshotted metadata. Audit-complete. Ready to build.*
