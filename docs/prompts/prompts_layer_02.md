# SignalIQ Layer 2: Final Production Prompts 

## Word Boundary Improvement
Understood. **No code. Just prompts.**

Here are the **5 fixed, production-ready prompts** for Open Code:

---

## Prompt 1: Database Schema & Raw Tables

```
Create a PostgreSQL 15+ database setup for SignalIQ Layer 2 with the following:

**Database & Schemas:**
- Create database 'signaliq' (if not exists)
- Create schemas: raw, ops, config

**RAW Schema - Prices Table:**
Fields: id (BIGSERIAL), ticker (VARCHAR20), vendor (VARCHAR30), date (DATE), open (NUMERIC12,4), high (NUMERIC12,4), low (NUMERIC12,4), close (NUMERIC12,4), adj_close (NUMERIC12,4 NOT NULL), volume (BIGINT), is_correction (BOOLEAN DEFAULT FALSE), supersedes_id (BIGINT), ingestion_run_id (UUID NOT NULL), extracted_at (TIMESTAMP DEFAULT CURRENT_TIMESTAMP), content_hash (VARCHAR64 NOT NULL)

Constraints: adj_close > 0, volume >=0 or null, date <= CURRENT_DATE, is_correction=false or supersedes_id not null

Uniqueness: Only one non-correction record per (ticker, vendor, date). Corrections allowed but must chain via supersedes_id.

Indexes: (ticker, date, is_correction, extracted_at), (ticker, vendor, date, is_correction), ingestion_run_id, content_hash

**RAW Schema - News Headlines Table:**
Fields: id (BIGSERIAL), source_id (INTEGER NOT NULL), source_name_snapshot (VARCHAR50 NOT NULL), source_tier_snapshot (SMALLINT NOT NULL), headline (TEXT NOT NULL), article_url (VARCHAR500), published_at (TIMESTAMP), ingested_at (TIMESTAMP DEFAULT CURRENT_TIMESTAMP), author (VARCHAR200), content_snippet (TEXT), ingestion_run_id (UUID NOT NULL), url_hash (VARCHAR64 NOT NULL), headline_hash (VARCHAR64 NOT NULL)

Constraints: headline not empty, source_tier_snapshot in (1,2,3)

Uniqueness: No duplicate (source_id, url_hash)

Indexes: published_at, url_hash, headline_hash, ingestion_run_id, source_tier_snapshot, (source_id, published_at)

**View: latest_prices** (Fully deterministic)
Logic: For each (ticker, date), return exactly one row. If corrections exist, use most recent correction (by extracted_at DESC, then id DESC). Otherwise use non-correction record. Must be immutable once resolved.

Output: Single SQL file with all CREATE statements, using IF NOT EXISTS. Include comments explaining the deterministic view logic.
```

---

## Prompt 2: Operational & Configuration Tables

```
Continue from Prompt 1. Add these tables:

**OPS Schema - ingestion_runs:**
Fields: run_id (UUID PRIMARY KEY), source_type (VARCHAR), source_name (VARCHAR), started_at (TIMESTAMP), completed_at (TIMESTAMP), status (VARCHAR), records_inserted (INTEGER), error_message (TEXT), metadata (JSONB)

Constraints: status in ('running','success','failed','partial')

Update rule: Only completed_at, status, records_inserted, error_message may be updated after insert.

Indexes: (source_type, source_name), started_at, status

**OPS Schema - ingestion_health:**
Fields: id (BIGSERIAL), source_type (VARCHAR), source_name (VARCHAR), date (DATE), expected_count (INTEGER), received_count (INTEGER), status (VARCHAR), duplicate_count (INTEGER), details (JSONB), calculated_at (TIMESTAMP)

Constraints: status in ('complete','partial','missing','failed')
Status thresholds: >=95% = complete, >=50% = partial, >0 but <50% = missing, 0 = failed

Indexes: (source_type, source_name, date), status

**OPS Schema - macro_indicators (placeholder):**
Fields: id (BIGSERIAL), indicator_name (VARCHAR), vendor (VARCHAR), date (DATE), value (NUMERIC12,4), ingestion_run_id (UUID)
No data in MVP, just schema.

**CONFIG Schema - monitored_assets:**
Fields: id (INTEGER PRIMARY KEY), ticker (VARCHAR20 UNIQUE), asset_class (VARCHAR), name (VARCHAR200), is_active (BOOLEAN), added_at (DATE), notes (TEXT)
Constraints: asset_class in ('equity','index','crypto')
Seed data: NVDA (equity), AAPL (equity), MSFT (equity), SPX (index), BTC-USD (crypto)

**CONFIG Schema - asset_aliases:**
Fields: id (INTEGER PRIMARY KEY), ticker (VARCHAR20 REFERENCES monitored_assets), alias (VARCHAR100), match_priority (INTEGER), is_case_sensitive (BOOLEAN DEFAULT FALSE), min_length (INTEGER DEFAULT 3)
Seed data: NVIDIA→NVDA, Apple→AAPL, Microsoft→MSFT (match_priority=10 for all)

**CONFIG Schema - news_sources:**
Fields: id (INTEGER PRIMARY KEY), name (VARCHAR50), url (VARCHAR500), tier (INTEGER), is_active (BOOLEAN), rate_limit_seconds (INTEGER), last_fetched_at (TIMESTAMP), fetch_failures (INTEGER), expected_daily_volume (INTEGER), metadata (JSONB)
Constraints: tier in (1,2,3)
Seed data: Reuters (tier1, expected 500), Associated Press (tier1, expected 400), CNBC (tier1, expected 300), Yahoo Finance General (tier2, expected 200), Yahoo Finance Ticker (tier2, expected 100), MarketWatch (tier2, expected 200)

**CONFIG Schema - ticker_vendor_mapping:**
Fields: id (INTEGER PRIMARY KEY), ticker (VARCHAR20 REFERENCES monitored_assets), vendor (VARCHAR30), vendor_symbol (VARCHAR50), is_primary (BOOLEAN)
Constraints: vendor in ('yahoo_finance', 'alpha_vantage')
Seed data: NVDA→yahoo_finance:NVDA (primary), SPX→yahoo_finance:^GSPC (primary), BTC-USD→yahoo_finance:BTC-USD (primary)

**CONFIG Schema - config_change_log:**
Fields: id (BIGSERIAL PRIMARY KEY), changed_at (TIMESTAMP), changed_by (VARCHAR100), table_name (VARCHAR50), record_id (INTEGER), old_value (JSONB), new_value (JSONB), change_type (VARCHAR)
Constraints: change_type in ('insert','update','delete')
Population rule: Database trigger stores complete before/after state as JSONB

Output: SQL file with CREATE TABLE, INSERT seed data, and all indexes.
```

---

## Prompt 3: Validation & Pure Functions (No Orchestration)

```
Continue from Prompts 1-2. Add validation layer only. NO orchestration stored procedures.

**IMPORTANT:** This prompt creates ONLY:
- Pure hashing functions (immutable, deterministic)
- Validation triggers (defensive)
- Atomic write primitives
DO NOT create ingestion orchestration procedures. Application Layer 1 handles batching, retries, correction detection, and run lifecycle.

**Extension required:**
CREATE EXTENSION IF NOT EXISTS pgcrypto;

**Pure Hashing Function - price_content_hash:**
Input: ticker TEXT, vendor TEXT, date DATE, adj_close NUMERIC, volume BIGINT
Output: TEXT (hex encoded SHA256)
Logic: Normalize as 'ticker|vendor|date|adj_close|volume' (NULL volume becomes empty string), apply SHA256, return hex
Properties: IMMUTABLE, parallel safe

**Pure Hashing Function - url_hash:**
Input: url TEXT
Output: TEXT (hex encoded SHA256)
Normalization: lowercase → trim
Properties: IMMUTABLE

**Pure Hashing Function - headline_hash:**
Input: headline TEXT
Output: TEXT (hex encoded SHA256)
Normalization: lowercase → trim → collapse multiple spaces → remove punctuation (keep letters, numbers, spaces only)
Properties: IMMUTABLE

**Validation Trigger - prices_insert_trigger:**
Fire BEFORE INSERT ON raw.prices
Checks:
- adj_close > 0 (else RAISE EXCEPTION)
- date <= CURRENT_DATE (else RAISE EXCEPTION)
- is_correction=true requires supersedes_id NOT NULL (else RAISE EXCEPTION)
- If is_correction=false, verify no existing non-correction for same (ticker, vendor, date) (RAISE EXCEPTION if duplicate)
Returns NEW

**Validation Trigger - headlines_insert_trigger:**
Fire BEFORE INSERT ON raw.news_headlines
Checks:
- headline NOT empty (else RAISE EXCEPTION)
- source_tier_snapshot IN (1,2,3) (else RAISE EXCEPTION)
- Verify source_id exists in config.news_sources (RAISE EXCEPTION if not)
Returns NEW

**Atomic Write Primitive - insert_price_record:**
Function that inserts ONE price record with auto-generated content_hash and extracted_at
Parameters: ticker, vendor, date, open, high, low, close, adj_close, volume, is_correction, supersedes_id, ingestion_run_id
Returns: id of inserted record
Note: Does NOT manage ingestion_runs. Does NOT detect corrections. Does NOT batch. Application Layer 1 handles those.

**Atomic Write Primitive - insert_headline_record:**
Function that inserts ONE headline record with auto-generated url_hash, headline_hash, and source metadata snapshot
Parameters: source_id, headline, article_url, published_at, author, content_snippet, ingestion_run_id
Behavior: Looks up source_name and source_tier from config.news_sources at insert time, snapshots them
Returns: id of inserted record or NULL if duplicate URL (violates uniqueness constraint)
Note: Does NOT manage ingestion_runs. Does NOT batch. Application Layer 1 handles those.

**Audit Trigger Function - log_config_change:**
Fire AFTER INSERT OR UPDATE OR DELETE on ALL config schema tables (monitored_assets, asset_aliases, news_sources, ticker_vendor_mapping)
Captures: changed_at = CURRENT_TIMESTAMP, changed_by = current_user, table_name = TG_TABLE_NAME, record_id = OLD.id or NEW.id, old_value = row_to_json(OLD) (NULL on INSERT), new_value = row_to_json(NEW) (NULL on DELETE), change_type = TG_OP
Inserts into config.config_change_log

Output: SQL file with all functions, triggers, and trigger attachments.
```

---

## Prompt 4: Read Layer for Layer 3

```
Continue from Prompts 1-3. Create read-only functions for Layer 3 consumption.

**Function: get_prices_history**
Parameters: p_ticker TEXT, p_end_date DATE, p_window_days INTEGER DEFAULT 20
Returns: TABLE (date DATE, adj_close NUMERIC, volume BIGINT)
Logic: Query the latest_prices view for the ticker, dates between (p_end_date - p_window_days + 1) and p_end_date, ordered by date ASC
Performance: Must use indexes (ticker, date)

**Function: get_headlines_range**
Parameters: p_start_date DATE, p_end_date DATE, p_tier_filter INTEGER DEFAULT NULL (NULL means all tiers)
Returns: TABLE (headline TEXT, published_at TIMESTAMP, source_tier_snapshot SMALLINT, author VARCHAR, headline_hash VARCHAR)
Logic: SELECT from raw.news_headlines WHERE published_at BETWEEN p_start_date AND p_end_date, and source_tier_snapshot = p_tier_filter if provided, ordered by published_at DESC
Note: Uses source_tier_snapshot (historical snapshot), not current config. Entity resolution happens in Layer 3, not here.

**Function: get_active_config**
Parameters: None
Returns: JSON
Logic: Return a single JSON object containing:
{
  "assets": [SELECT ticker, asset_class, name FROM config.monitored_assets WHERE is_active=true],
  "aliases": [SELECT ticker, alias, match_priority FROM config.asset_aliases],
  "sources": [SELECT id, name, tier, expected_daily_volume FROM config.news_sources WHERE is_active=true],
  "vendor_mappings": [SELECT ticker, vendor, vendor_symbol FROM config.ticker_vendor_mapping WHERE is_primary=true]
}
Intended to be called once at Layer 3 startup and cached.

**Function: get_ingestion_health_summary**
Parameters: p_source_name TEXT DEFAULT NULL, p_days INTEGER DEFAULT 7
Returns: TABLE (source_name TEXT, date DATE, status TEXT, received_count INTEGER, expected_count INTEGER)
Logic: SELECT from ops.ingestion_health for the last p_days, filtered by source_name if provided, ordered by date DESC

**View: v_asset_coverage**
Purpose: Show data completeness per asset for monitoring
Fields: ticker, last_price_date, headline_count_last_7_days
Logic: 
- last_price_date: MAX(date) from latest_prices view per ticker
- headline_count_last_7_days: COUNT from raw.news_headlines (joined via entity resolution? No - show raw counts, Layer 3 handles resolution)

Output: SQL file with all functions and view. Include comment: "Layer 3 reads only. No writes."
```

---

## Prompt 5: Security, Maintenance & Master Integration

```
Continue from Prompts 1-4. Add security, maintenance, and create master build script.

**Database Roles with Permissions:**

Role: layer1_etl
Permissions: INSERT ON raw.prices, raw.news_headlines, ops.ingestion_runs; SELECT ON config.news_sources
No UPDATE, DELETE on raw tables

Role: layer3_intel  
Permissions: SELECT ON raw.latest_prices, raw.news_headlines, ops.ingestion_health, config.monitored_assets, config.asset_aliases, config.news_sources, config.ticker_vendor_mapping
No writes to any table

Role: admin
Permissions: ALL ON config schema; SELECT ON raw, ops schemas
For manual configuration changes only

Role: monitoring
Permissions: SELECT ON ops.ingestion_health
For alerting systems

**Maintenance Functions:**

Function: vacuum_analyze_schemas()
Parameters: None
Behavior: Execute VACUUM ANALYZE on raw, ops, config schemas
Return: TEXT summary of what was vacuumed

Function: purge_old_health_data()
Parameters: p_keep_days INTEGER DEFAULT 730 (2 years)
Behavior: DELETE FROM ops.ingestion_health WHERE date < CURRENT_DATE - p_keep_days
Return: INTEGER count of rows deleted

Function: get_table_sizes()
Parameters: None
Returns: TABLE (schema TEXT, table_name TEXT, size_mb NUMERIC)
For monitoring database growth

**Master Build Script Requirements:**

Create a single master SQL file that:
1. Runs all CREATE statements in order (Prompt 1 → 2 → 3 → 4 → 5)
2. Uses IF NOT EXISTS for all objects (idempotent)
3. Wraps the entire script in a transaction (BEGIN/COMMIT)
4. On any error: ROLLBACK and output error details
5. At end of successful run: output summary of created objects (schemas, tables, views, functions, triggers, roles)

**Rollback Script:**

Create separate file with DROP statements for all objects in reverse order:
- DROP all functions
- DROP all triggers  
- DROP all views
- DROP all tables (with CASCADE)
- DROP all schemas
- DROP all roles

**README Content (as comments in master script):**

Include at top of master script:
- Connection string format: postgresql://user:password@localhost:5432/signaliq
- Quick start: psql -U postgres -f master_build.sql
- Order of operations: Run master_build.sql first, then verify with test queries
- Configuration backup: Run pg_dump --schema=config before any config changes
- Testing: Insert one price, one headline, verify latest_prices view
- Layer 3 expects: get_prices_history(), get_headlines_range(), get_active_config()

Output: 
- File 1: master_build.sql (complete build script)
- File 2: rollback.sql (complete cleanup)
- File 3: test_queries.sql (validation queries)
```

---

## Summary

| Prompt | Focus | Output |
|--------|-------|--------|
| 1 | Database + raw schema + latest_prices view | SQL file (DDL) |
| 2 | ops + config tables + seed data | SQL file (DDL + INSERTs) |
| 3 | Validation + pure functions (no orchestration) | SQL file (functions + triggers) |
| 4 | Read layer for Layer 3 | SQL file (queries + view) |
| 5 | Security + maintenance + master script | 3 SQL files (build + rollback + tests) |

---

**These 5 prompts are ready to paste into Open Code.** No code in the prompts — just clear, deterministic specifications.
