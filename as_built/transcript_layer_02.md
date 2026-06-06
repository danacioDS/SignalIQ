# SignalIQ Layer 2 — Transcript: Database Build

## Overview

Layer 2 (persistence layer) was built across 5 prompt rounds, producing 4 migration files totalling 1,878 lines of PostgreSQL 15+ SQL. Everything is idempotent (`IF NOT EXISTS` / `CREATE OR REPLACE`), transactional, and follows the LLD spec at `docs/lld/SignalIQ_layer_02.md`.

**Bottom line:** 10 tables, 2 views, 13 functions, 6 triggers, 4 roles, 0 stored procedures.

---

## Prompt 1 — Core Schema (raw.prices, raw.news_headlines, latest_prices view)

**What was created:**
- Schemas `raw`, `ops`, `config`
- `raw.prices` — full OHLCV + correction tracking. Fields: ticker, vendor, date, open/high/low/close/adj_close, volume, is_correction, supersedes_id, ingestion_run_id, extracted_at, content_hash
- `raw.news_headlines` — source-snapshotted headlines. Fields: source_id, source_name_snapshot, source_tier_snapshot, headline, article_url, published_at, ingested_at, author, content_snippet, ingestion_run_id, url_hash, headline_hash
- `raw.latest_prices` view — resolves corrections deterministically

**Key decisions:**
- **Partial unique index** `uq_prices_no_correction` on `(ticker, vendor, date) WHERE is_correction = FALSE` — allows multiple corrections while enforcing exactly one original
- **Self-referential FK** `fk_prices_supersedes` — correction chain integrity at the database level
- **`DISTINCT ON` + `ORDER BY is_correction DESC, extracted_at DESC, id DESC`** — fully deterministic view. Proof: `extracted_at` and `id` are both monotonic and immutable once set
- **Source metadata snapshots** — `source_name_snapshot` and `source_tier_snapshot` are copied at insert time from `config.news_sources`, not read via JOIN. Future config changes cannot corrupt historical analysis
- **pgcrypto extension** for SHA256. Declared once, used by all 3 hashing functions

**Schema alignment with LLD:** The LLD specified a simpler prices table (adj_close only). Prompt 1 expanded to full OHLCV. The LLD specified `source_record_id` on news_headlines; Prompt 1 replaced this with `source_id` + `url_hash` for cleaner dedup. These divergences are intentional — the user's spec supersedes the LLD.

---

## Prompt 2 — OPS + CONFIG tables

**What was created:**
- `ops.ingestion_runs` — UUID PK, lifecycle status, `BEFORE UPDATE` trigger enforcing column immutability
- `ops.ingestion_health` — daily quality snapshot per source with threshold rules documented in comments
- `ops.macro_indicators` — schema-only placeholder, zero MVP data
- `config.monitored_assets` — 5 seed assets (NVDA, AAPL, MSFT, SPX, BTC-USD)
- `config.asset_aliases` — 3 seed aliases (NVIDIA, Apple, Microsoft)
- `config.news_sources` — 6 RSS feeds across tiers 1 and 2, with rate limits and expected daily volumes
- `config.ticker_vendor_mapping` — 5 yahoo_finance primary mappings (including `^GSPC` for SPX)
- `config.config_change_log` — audit table with JSONB before/after capture

**Key decisions:**
- **Seed data uses `ON CONFLICT (id) DO NOTHING`** — idempotent re-runs
- **ingestion_runs update guard** — trigger blocks writes to `run_id`, `source_type`, `source_name`, `started_at`, `metadata` after insert
- **All config tables use explicit INTEGER PK** — small lookup tables, no need for BIGSERIAL
- **config_change_log CHECK constraint** enforces value consistency: insert → old=NULL new!=NULL, update → both non-NULL, delete → old!=NULL new=NULL

---

## Prompt 3 — Validation Layer (Pure Functions, No Orchestration)

This was the critical design constraint: **no stored procedures that manage ingestion orchestration.** Layer 1 (application code) owns batching, retries, correction detection, and run lifecycle. The database provides only:

**3 IMMUTABLE hashing functions** (all `PARALLEL SAFE`):
- `raw.price_content_hash(ticker, vendor, date, adj_close, volume)` — `|`-delimited normalisation, NULL volume → empty string
- `raw.url_hash(url)` — lowercase → trim → SHA256
- `raw.headline_hash(headline)` — lowercase → trim → collapse spaces → strip punctuation → SHA256

**2 BEFORE INSERT triggers** (defensive, complement existing constraints):
- `raw.trg_prices_insert()` — validates adj_close > 0, date not future, correction has supersedes_id, no duplicate non-correction
- `raw.trg_headlines_insert()` — validates headline not empty, tier in (1,2,3), source_id exists in config

**2 atomic write primitives:**
- `raw.insert_price_record(...)` — 12 parameters, auto-hashes content_hash, auto-sets extracted_at, returns id
- `raw.insert_headline_record(...)` — 7 parameters, snapshots source metadata from config, auto-hashes URL and headline, returns `NULL` on UNIQUE_VIOLATION (duplicate URL)

**Config audit trigger** rewritten to use `row_to_json()` + `current_user` (replacing `to_jsonb()` + `current_setting` hack from Prompt 2). Direct `CREATE TRIGGER` on all 4 config tables.

**Why "No Orchestration":**
- No function creates or updates `ops.ingestion_runs`
- No function detects corrections or manages `supersedes_id`
- No function batches multiple records
- Layer 1 calls `insert_price_record()` in a loop and manages the transaction lifecycle

---

## Prompt 4 — Layer 3 Read-Only Interface

**4 STABLE functions (no writes, no side effects):**
- `get_prices_history(ticker, end_date, window_days DEFAULT 20)` — queries `raw.latest_prices`, leverages `(ticker, date, is_correction, extracted_at)` index
- `get_headlines_range(start_date, end_date, tier_filter DEFAULT NULL)` — queries `raw.news_headlines` by `published_at`, uses `source_tier_snapshot` (not current config), DESC
- `get_active_config()` — single JSON payload with 4 arrays: assets, aliases, sources, vendor_mappings. Designed for once-at-startup caching
- `get_ingestion_health_summary(source_name DEFAULT NULL, days DEFAULT 7)` — recent quality metrics from `ops.ingestion_health`, DESC

**1 monitoring view:**
- `v_asset_coverage` — per-asset `last_price_date` (via `latest_prices`) + system-wide `headline_count_last_7_days`. Entity resolution deferred to Layer 3

All functions explicitly marked `STABLE` — PostgreSQL allows optimisation but guarantees no data modification.

---

## Prompt 5 — Security, Maintenance, Build Scripts

**4 database roles:**

| Role | Permissions | Purpose |
|------|-------------|---------|
| `layer1_etl` | INSERT on raw tables + ops.ingestion_runs; SELECT on config.news_sources | Data ingestion |
| `layer3_intel` | SELECT on all data tables/views; EXECUTE on 4 read functions | Signal computation |
| `admin` | ALL on config schema; SELECT on raw, ops | Manual config changes |
| `monitoring` | SELECT on ops.ingestion_health | Alerting systems |

**3 maintenance functions:**
- `vacuum_analyze_schemas()` — VACUUM ANALYZE on all 9 tables. Must run outside transaction block
- `purge_old_health_data(p_keep_days DEFAULT 730)` — deletes old health rows, returns count
- `get_table_sizes()` — returns MB per table across raw/ops/config schemas

**3 build scripts:**
- `master_build.sql` — transactional wrapper (`BEGIN`/`COMMIT`), `\ir` includes the core migration, adds roles and maintenance functions, outputs object summary
- `rollback.sql` — drops in reverse order: triggers → functions → views → tables (CASCADE) → schemas → roles (with `DROP OWNED BY`)
- `test_queries.sql` — 24 validation tests covering schema existence, seed data, atomic writes, correction resolution, all Layer 3 functions, and cleanup

---

## File Inventory

| File | Lines | Role |
|------|-------|------|
| `migrations/001_create_layer2_schema.sql` | 1,243 | Core schema — tables, views, functions, triggers, seed data |
| `migrations/master_build.sql` | 292 | Transactional build wrapper + roles + maintenance |
| `migrations/rollback.sql` | 98 | Complete teardown in reverse dependency order |
| `migrations/test_queries.sql` | 245 | 24 validation tests |
| `transcript_layer_02.md` | this | Build transcript |
| `docs/lld/SignalIQ_layer_02.md` | — | LLD specification (reference) |

**Object count (from build summary):**
- schemas: 3
- tables: 10
- views: 2
- functions: 13
- triggers: 6
- roles: 4

---

## Design Invariants

These constraints are enforced at the database level and cannot be bypassed by any Layer (1, 3, or 4):

1. **Adjacent close > 0** — CHECK constraint + trigger
2. **Date not in future** — CHECK constraint + trigger
3. **Correction always has supersedes_id** — CHECK constraint + trigger
4. **Only one non-correction per (ticker, vendor, date)** — partial unique index + trigger
5. **Headline not empty** — CHECK constraint + trigger
6. **Source tier in (1,2,3)** — CHECK constraint + trigger
7. **No duplicate URL per source** — `UNIQUE(source_id, url_hash)` constraint
8. **Content hash always matches record** — auto-generated by `insert_price_record()`
9. **Source metadata is historical snapshot** — captured at insert time from config
10. **All config changes are audited** — trigger on all 4 config tables

---

## Migration Strategy

All schema changes go into versioned migration files:

```
migrations/
  001_create_layer2_schema.sql   ← Prompt 1-4 (the canonical schema)
  master_build.sql               ← Prompt 5 (transactional orchestration)
  rollback.sql                   ← Prompt 5 (teardown)
  test_queries.sql               ← Prompt 5 (validation)
  002_<feature>.sql              ← future
```

**Rule:** Every change is a new migration file. No in-place edits after merge. `master_build.sql` uses `\ir` to include migrations in dependency order — adding `002_*.sql` means adding one `\ir` line.
