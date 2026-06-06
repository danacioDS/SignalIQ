# SignalIQ — Overall Development Transcript

## Project Genesis

SignalIQ is a market intelligence framework that measures the divergence between market *narratives* (news sentiment) and market *reality* (price momentum) using the **Narrative Divergence Index (NDI)**:

```
NDI(t) = [ S_news(t) - μ_s ] / σ_s  -  [ M_price(t) - μ_m ] / σ_m
```

The project was built across **98+ commits** spanning conceptual documentation → system architecture → 4 implementation layers → pipeline integration.

---

## Phase 0 — Conceptual Foundation (commits 1–30)

Establishing the investment thesis, commercial strategy, and system design before writing code.

### What was done

- **Initial commit** (`59d2768`) — repo bootstrap
- **Commercial pitch & economic theory docs** — NDI formula, four risk regimes, academic pillars (Keynes's animal spirits, bounded rationality, Minsky's overshooting), distributional assumptions, predictive validation
- **Product engineering docs** — `product_engineering.md`, `product_expectations.md`
- **6 conceptual documents** in `docs/conceptual/`:
  - `01_commercial_pitch.md` — Elevator pitch, target users, product-market fit
  - `02_economics_theory.md` — Behavioral economics foundations
  - `03_statistics_theory.md` — Z-score methodology, hypothesis testing
  - `04_commercial_strategy.md` — Product positioning vs. competitors
  - `05_data_acquisition_strategy.md` — Sources for structured/unstructured data
  - `06_operational_strategy.md` — Multi-layer monitoring (currencies, bonds, commodities, equities)
- **Multiple renames and restructures** of documentation hierarchy (HLD → LLD → architecture separation)

### Artifacts produced

- `docs/conceptual/01-06_*.md` — 6 conceptual documents (~2500 lines total)
- `docs/hld/SignalIQ_mvp_plan.md` — Full 6-layer architecture plan
- `docs/hld/SignalIQ_mvp_uni_exec.md` — Unified execution plan
- `docs/hld/product_engineering.md` — Product engineering specification
- `docs/hld/product_expectations.md` — Expected output criteria

---

## Phase 1 — Layer 4: NDI Signal Generation (commits 30–45)

The *first code layer built* (counterintuitively, the signal generation was implemented before ingestion or storage). Built as 4 sublayers with strict one-direction dependency.

### What was built

**4 Python modules in `signal_generation/`** (originally in `layers/`):

| Module | Lines | Responsibility |
|--------|-------|----------------|
| `layer4_measurement.py` | 99 | Validity gate, NDI calculation, 5-day return |
| `layer4_persistence.py` | 123 | Streak tracking (JSON file), stale-gap detection, signal state, regime |
| `layer4_classification.py` | 155 | Confidence (inverted-U), price pressure, risk, attention, NDI trend |
| `layer4_orchestrator.py` | 195 | 9-step pipeline, batch processing, input validation |

**Key design decisions:**

- **NDI = sentiment_zscore - momentum_zscore** — simple, interpretable divergence
- **Inverted-U confidence**: `|NDI| > 2.2 → MEDIUM` (extreme = possibly noise), `|NDI| >= 0.8 → HIGH`, else `LOW`
- **Streak persistence via JSON** — survives cron-job restarts without a database dependency
- **Stale-gap detection** — 3-day max gap prevents weekend/holiday false streaks
- **Explicit `save()`** — avoids O(assets × days) disk writes; orchestrator calls once per batch
- **12-field output schema** — ticker, date, ndi, ndi_delta, ndi_trend, regime, signal_state, confidence, price_modifier, persistence_days, risk_level, attention

**4 rounds of development:**
1. Code review + 6 fixes (configurable path, sorted batch, surfaced fields, LLD superseded)
2. 3 feature upgrades (confidence ceiling guard, NDI velocity, batch validation)
3. 3 hardening changes (ordering comment, ndi_trend, stale persistence detection)
4. L3→L4 pipeline integration (DB connector, pipeline orchestrator, 20-day demo)

**Test suite:** 15 tests, 80+ checks — all pass.

### Artifacts produced

- `signal_generation/layer4_measurement.py`
- `signal_generation/layer4_persistence.py`
- `signal_generation/layer4_classification.py`
- `signal_generation/layer4_orchestrator.py`
- `tests/test_layer4.py`
- `docs/architecture/Layer_04_arch.md`
- `docs/lld/SignalIQ_layer_04.md` (later marked superseded)
- `docs/prompts/prompts_layer_04.md`
- `persistence_state.json` (runtime artifact)

---

## Phase 2 — Layer 3: NLP Intelligence Engine (commits 45–55)

Built after Layer 4. Transforms raw headlines and prices into normalized z-scores. **Zero external dependencies** (standard library only).

### What was built

**5 core modules (stdlib only) + 1 DB connector + 1 pipeline orchestrator:**

| Module | Lines | Responsibility |
|--------|-------|----------------|
| `layer3_config.py` | 25 | Frozen dataclass — all MVP parameters in one place |
| `layer3_entity.py` | 101 | Two-phase entity resolution (URL param → alias regex) |
| `layer3_sentiment.py` | 171 | Loughran-McDonald lexicon + rolling 20-day sentiment z-score |
| `layer3_momentum.py` | 154 | Daily returns + rolling 20-day momentum z-score (two-phase commit) |
| `layer3_orchestrator.py` | 280 | Pipeline orchestration, time alignment, output |
| `layer3_db.py` | 167 | PostgreSQL connector, historical warm-up, config loading |
| `signal_pipeline.py` | 230 | L3→L4 daily coordinator |

**Key design decisions:**

- **Two-phase entity resolution** — URL parameter match (high precision) first, then alias regex (recall-oriented). Custom word-boundary lookarounds (`(?<!\w)` / `(?!\w)`) handle punctuation in aliases (e.g., `AT&T`)
- **Loughran-McDonald lexicon** — domain-specific finance sentiment (positive/negative word lists)
- **Rolling z-scores** — 20-day window with 10-day minimum before activation
- **Two-phase momentum commit** — prices stored in pending state; `commit_pending_returns()` moves them to history. This prevents look-ahead bias in the rolling baseline
- **Zero external packages** — `csv.DictReader`, `re`, `collections.deque`, no numpy/pandas
- **Memory-only state** — all state in `deque(maxlen=30)`; restart recomputes from DB in <5 minutes

**Test suite:** 16 tests, 100+ checks — all pass.

### Artifacts produced

- `intelligence_processing/layer3_config.py`
- `intelligence_processing/layer3_entity.py`
- `intelligence_processing/layer3_sentiment.py`
- `intelligence_processing/layer3_momentum.py`
- `intelligence_processing/layer3_orchestrator.py`
- `intelligence_processing/layer3_db.py`
- `intelligence_processing/signal_pipeline.py`
- `tests/test_layer3.py`
- `docs/architecture/Layer_03_arch.md`
- `docs/lld/SignalIQ_layer_03.md`
- `docs/prompts/prompts_layer_03.md`
- `config/entity_aliases.json`

---

## Phase 3 — Layer 2: PostgreSQL Database (commits 55–65)

Persistence layer — 1,878 lines of PostgreSQL 15+ SQL across 4 migration files.

### What was built

**10 tables, 2 views, 13 functions, 6 triggers, 4 roles across 3 schemas:**

| Schema | Objects |
|--------|---------|
| `raw` | `prices`, `news_headlines`, `latest_prices` (view) |
| `ops` | `ingestion_runs`, `ingestion_health`, `macro_indicators` |
| `config` | `monitored_assets`, `asset_aliases`, `news_sources`, `ticker_vendor_mapping`, `config_change_log` |

**Key design decisions:**

- **Partial unique index** on `(ticker, vendor, date) WHERE is_correction = FALSE` — allows corrections while enforcing one original
- **Self-referential FK** `fk_prices_supersedes` — correction chain integrity at DB level
- **DISTINCT ON + ORDER BY** on `latest_prices` view — fully deterministic correction resolution
- **Source metadata snapshots** — `source_name_snapshot` and `source_tier_snapshot` copied at insert time from config; future config changes cannot corrupt historical analysis
- **No orchestration in DB** — only atomic write primitives; Layer 1 owns batching, retries, run lifecycle
- **4 STABLE read-only functions** for Layer 3: `get_prices_history()`, `get_headlines_range()`, `get_active_config()`, `get_ingestion_health_summary()`
- **4 database roles**: `layer1_etl` (INSERT), `layer3_intel` (SELECT/EXECUTE), `admin` (config), `monitoring` (health)

**Build scripts:**
- `master_build.sql` — transactional build wrapper with `\ir` includes
- `rollback.sql` — complete teardown in reverse dependency order
- `test_queries.sql` — 24 validation tests

**Design invariants (enforced at DB level):**
1. Adjacent close > 0 (CHECK + trigger)
2. Date not in future (CHECK + trigger)
3. Correction always has supersedes_id (CHECK + trigger)
4. One non-correction per (ticker, vendor, date) (partial unique index + trigger)
5. Headline not empty (CHECK + trigger)
6. Source tier in (1,2,3) (CHECK + trigger)
7. No duplicate URL per source (UNIQUE constraint)
8. Content hash auto-generated by insert function
9. Source metadata is historical snapshot
10. All config changes audited via trigger

### Artifacts produced

- `data_storage/001_create_layer2_schema.sql` — 1,243 lines (core schema)
- `data_storage/master_build.sql` — 292 lines
- `data_storage/rollback.sql` — 98 lines
- `data_storage/test_queries.sql` — 245 lines
- `docs/lld/SignalIQ_layer_02.md`
- `docs/architecture/Layer_02_arch.md`
- `docs/prompts/prompts_layer_02.md`

---

## Phase 4 — Layer 1: Data Ingestion (v2.0 Corrected)

The last implementation layer built. Collects daily price data from Yahoo
Finance and news headlines from 6 RSS feeds, normalizes, and writes to
PostgreSQL. Built from the corrected v2.0 spec with all contradictions
resolved.

### What was built

**5 Python modules in `layer1/`:**

| Module | Lines | Responsibility |
|--------|-------|----------------|
| `http_client.py` | 75 | Shared HTTP with configurable retry logic |
| `collect_prices.py` | 115 | Yahoo Finance OHLCV for 5 assets |
| `collect_news.py` | 211 | RSS news collection from 6 sources with observability |
| `writer.py` | 96 | PostgreSQL atomic writes (named parameter dicts) |
| `orchestrator.py` | 214 | Coordination, O_EXCL locks, pipe-delimited logging |

**Key design decisions (v2.0):**

| Decision | Rationale |
|----------|-----------|
| `fetch_with_retry` as shared utility | One retry policy across prices and news; DRY |
| NFKC unicode normalization | Handles scraped content edge cases (ligatures, full-width) |
| Author via `authors[].name` | feedparser normalizes `dc:creator` into `authors[]`, not a top-level key |
| Empty headline counting + WARNING | Silent data loss is worse than noisy logs |
| O_EXCL lock acquisition | Atomic; no TOCTOU race on lock check |
| Price = transactional, News = not | Prices are a coherent snapshot; headlines are independent records |
| Named SQL params (dict-based) | 12+ parameter functions are unreadable with positional args |
| Dry-run = same network, no DB | Tests network path without committing data |

**Transaction model (critical fix):**

- **Prices**: single transaction — all-or-nothing. If any price fails, entire
  batch rolls back.
- **News**: no transaction — per-row idempotency via DB unique constraints.
  Partial writes are acceptable and preferable to losing all headlines.

**Deployment artifacts:**
- `scripts/install_crontab.sh` — idempotent crontab installer (prices daily 8:05 PM ET, news 6/12/18 ET)
- `scripts/rotate_logs.sh` — daily log rotation, 90-day retention
- `config/entity_aliases.json` — Layer 3 config (5 tickers, conservative aliases)
- `requirements_layer1.txt` — `psycopg2-binary`, `requests`, `feedparser`
- `.env.example` — DATABASE_URL template

**Test suite:** 15 tests, 61 checks — all pass.

### Artifacts produced

- `layer1/http_client.py`
- `layer1/collect_prices.py`
- `layer1/collect_news.py`
- `layer1/writer.py`
- `layer1/orchestrator.py`
- `scripts/install_crontab.sh`
- `scripts/rotate_logs.sh`
- `config/entity_aliases.json`
- `requirements_layer1.txt`
- `.env.example`
- `tests/test_layer1_integration.py`
- `docs/lld/SignalIQ_layer_01.md`

---

## Phase 5 — Pipeline Integration

### L3→L4 Pipeline

Connected all 4 layers into an end-to-end pipeline:

- **`intelligence_processing/layer3_db.py`** — PostgreSQL connector that loads historical data, warms up Layer 3's rolling windows, generates `entity_aliases.json` from DB config
- **`intelligence_processing/signal_pipeline.py`** — `SignalPipelineOrchestrator` coordinating daily runs: feed prices/headlines → finalize day → transform z-scores → process batch via Layer 4 → return 12-field signal records
- **`intelligence_processing/signal_pipeline.py::calculate_price_direction()`** — temporary price transform (`price_history[-6:] → RISING/FLAT/FALLING`); post-MVP moves to Layer 3
- **End-to-end 20-day synthetic data verification** — all 46 tests pass across all 4 layers

---

## Current Project State

```
repo root/
├── layer1/                       # Layer 1 — Data Ingestion (5 modules)
├── layers/                       # Legacy — Layer 3 + 4 modules (working)
├── scripts/                      # Crontab, log rotation (2 scripts)
├── tests/                        # 46 tests across all layers
├── config/                       # entity_aliases.json
├── synthetic/                    # Test data generation
├── docs/
│   ├── architecture/             # Layer_01-04 arch docs
│   ├── hld/                      # High-level design docs
│   ├── lld/                      # Low-level design docs
│   ├── conceptual/               # Theory & strategy docs
│   └── prompts/                  # Development prompts
├── as_built/                     # Build transcripts
├── .env.example
├── requirements_layer1.txt       # Layer 1 dependencies
├── architecture.md               # Full system diagram
├── README.md                     # Project documentation
└── demo.py                       # End-to-end demo (stdlib only)
```

### Layer Status

| Layer | Description | Status | Tests |
|-------|-------------|--------|-------|
| **1** | Data ingestion (Yahoo Finance + RSS) | Complete (v2.0) | 15 tests, 61 checks |
| **2** | PostgreSQL persistence (10 tables, 13 functions, 6 triggers, 4 roles) | Complete | 24 SQL validation queries |
| **3** | NLP intelligence (sentiment, momentum, entity resolution) | Complete | 16 tests, 100+ checks |
| **3→4** | Pipeline orchestrator (L2→L3→L4 daily run) | Complete | 20-day end-to-end verification |
| **4** | NDI signal generation (measurement, persistence, classification) | Complete | 15 tests, 80+ checks |
| **5** | AI processing | Not started | — |
| **6** | Presentation | Not started | — |

### Key Metrics

- **98+ commits** across all phases
- **4 implementation layers** built in reverse order (L4 → L3 → L2 → L1)
- **~6,200 lines of Python** across 23 modules
- **~1,900 lines of PostgreSQL SQL** across 4 migration files
- **46 tests** with 241+ assertions — all passing
- **6 conceptual documents** (~3,000 words) establishing the investment thesis
- **Zero external dependencies** in core Layers 3 and 4 (stdlib only)
- **12-field output schema** per ticker per day
- **Layer 1 v2.0 fixes**: 5 contradictions resolved (transaction model, lock race, unicode, author resolution, empty headline counting)
