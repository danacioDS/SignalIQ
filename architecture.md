# SignalIQ Architecture

## Overview

**SignalIQ** is a market intelligence framework that measures the divergence between what the market is *saying* (news sentiment/narrative) and what the market is *actually doing* (price momentum). It quantifies this gap using the **Narrative Divergence Index (NDI)**:

```
NDI = sentiment_zscore - momentum_zscore
```

Markets are driven by stories as much as by numbers. Stories are created, spread, overheat, and exhaust themselves. Numbers (prices, volatility, volume) are slower and heavier. SignalIQ measures the distance between the hot (narrative) and the cold (prices).

### Key Features
- **NDI formula**: `sentiment_zscore - momentum_zscore` (additive divergence in standard deviation units)
- **4 risk regimes**: Aligned, Accumulation Divergence, Overheating Divergence, Insufficient Data
- **3 signal states**: Inactive → Watching → Active (requires 2 consecutive threshold breaches)
- **Inverted-U confidence**: Mid-range NDI (0.8–2.2) is most reliable; extreme values are down-weighted
- **LLM Router**: Multi-provider support (Gemini, GLM/ZhipuAI, Groq, MOCK mode)
- **Fundamental overlay**: Adjusts NDI risk/confidence based on valuation, growth, and financial health
- **Stdlib-only core**: Core analytics are pure Python (only Layer 1 and Layer 5 have external deps)

### Tech Stack

| Category | Technologies |
|----------|-------------|
| **Backend** | Python 3.12, Flask 3.0, flask-cors 4.0 |
| **Frontend** | React 19, TypeScript 4.9, Recharts 3.8, Axios 1.17, Tailwind CSS 3.4 |
| **Database** | PostgreSQL (raw, ops, config schemas) |
| **AI/LLM** | Google Gemini, GLM (ZhipuAI), Groq, MOCK mode |
| **Infrastructure** | Docker, Docker Compose, Railway |
| **Data Sources** | Yahoo Finance (yfinance 0.2), 6 RSS feeds (feedparser) |
| **External Deps** | psycopg2-binary, requests, numpy (only Layer 5) |

### Core Philosophy

When narrative runs ahead of price action, SignalIQ flags it as exhaustion, distribution, or severe divergence — not a prediction, but a systematic measurement of risk conditions. Signals classify into 4 risk regimes and 3 signal states based on the persistence and magnitude of the divergence.

---

## Project Structure

```
repo root/
├── architecture.md                         # This file — system map
├── README.md                               # Repo readme
├── api_signaliq.py                         # Flask REST API (/analyze, /batch, /summary, /health)
├── signals_demo.csv                        # Demo signal output
├── .env.example                            # DATABASE_URL template
├── .gitignore                              # Git ignore rules
├── pytest.ini                              # Pytest config (smoke/integration/slow markers)
├── requirements_test.txt                   # Pytest dependencies
├── requirements_layer1.txt                 # Layer 1 dependencies (psycopg2-binary, requests, feedparser)
├── workflow.md                             # Development workflow
│
├── backend/                                # Flask backend (Layer 4 API server)
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                         # CORS Flask API (port 10000) + rate limiting
│   │   └── db.py                           # ThreadedConnectionPool for PostgreSQL
│   └── requirements.txt
│
├── ingestion/                              # Layer 1 — Data Ingestion (5 modules)
│   ├── __init__.py
│   ├── http_client.py                      # Shared HTTP with retry (fetch_with_retry)
│   ├── collect_prices.py                   # Yahoo Finance OHLCV (5 assets)
│   ├── collect_news.py                     # RSS feed collection (6 sources)
│   ├── writer.py                           # PostgreSQL atomic writes (named params)
│   └── orchestrator.py                     # Coordination, O_EXCL locks, logging
│
├── layers/                                 # Layers 3, 4 & 5 — NLP, Signal, Fundamental
│   ├── __init__.py                         # Exports L4 + integration + lexicon
│   ├── lm_lexicon.py                       # Loughran-McDonald lexicon (558 words, 6 categories)
│   ├── layer3_config.py                    # L3 frozen config dataclass
│   ├── layer3_entity.py                    # L3 entity resolution (two-phase)
│   ├── layer3_sentiment.py                 # L3 Loughran-McDonald lexicon + rolling z-score
│   ├── layer3_momentum.py                  # L3 daily returns + rolling z-score (two-phase commit)
│   ├── layer3_orchestrator.py              # L3 pipeline orchestration
│   ├── layer4_measurement.py               # L4 validity gate, NDI, 5-day return
│   ├── layer4_persistence.py               # L4 streak tracking, stale-gap, signal state
│   ├── layer4_classification.py            # L4 confidence, price pressure, risk, attention
│   ├── layer4_orchestrator.py              # L4 9-step pipeline, batch processing, LLM integration
│   ├── system_config.py                    # SignalIQConfig singleton
│   ├── llm_router.py                       # LLMRouter (Gemini, GLM, Groq, MOCK)
│   ├── integration.py                      # L1→L3→L4 pipeline integration entry point
│   └── fundamental/                        # Layer 5 — Fundamental Analysis (3 modules)
│       ├── __init__.py
│       ├── fundamental_engine.py           # Main engine: processes metrics, caches results
│       ├── metrics_calculator.py           # Valuation ratios, growth, profitability, cash flow
│       └── score_aggregator.py             # Sector-benchmarked scoring (0–100)
│
├── frontend/                               # Layer 6 — React TypeScript UI
│   ├── public/
│   ├── src/
│   │   └── App.tsx                         # KPI cards, signal table, NDI bar chart
│   ├── package.json
│   └── tsconfig.json
│
├── sql/                                    # Layer 2 — SQL migrations (6 files)
│   ├── 001_create_layer2_schema.sql        # Core schema (61 lines)
│   ├── 002_fix_schema.sql                  # raw schema, wrapper functions, config tables
│   ├── 003_create_signal_tables.sql        # Signal classification tables
│   ├── master_build.sql                    # Transactional build wrapper
│   ├── rollback.sql                        # Complete teardown
│   └── test_queries.sql                    # 24 validation queries
│
├── scripts/                                # Operations scripts
│   ├── install_crontab.sh                  # Idempotent cron installer
│   ├── rotate_logs.sh                      # Daily rotation, 90-day retention
│   ├── daily.sh                            # Daily pipeline (collect → analyze → signal)
│   ├── backtest_engine.py                  # NDI backtesting engine (pandas/numpy)
│   ├── backtest_improved.py                # Enhanced backtesting with metrics
│   ├── run_backtest_real.py                # Production backtest runner
│   ├── demo.py                             # End-to-end synthetic demo (stdlib only)
│   ├── simple_ndi.py                       # Simplified NDI signal generator
│   └── verify_refactor.py                  # Structural verification script
│
├── web/                                    # Standalone HTML dashboards
│   ├── index.html                          # Dark-themed institutional dashboard
│   ├── automatico.html                     # Automated dashboard
│   └── test.html                           # Simple API test UI
│
├── config/                                 # Configuration files
│   ├── thresholds.py                       # Production-critical thresholds
│   └── entity_aliases.json                 # Alias entries for Layer 3 (5 tickers)
│
├── tests/                                  # Official test suite
│   ├── __init__.py
│   ├── pytest/                             # Pytest tests (single source of truth)
│   │   ├── test_smoke.py                   # 4 smoke tests: Layer4, Config, Layer1, API
│   │   ├── test_architecture.py            # 4 architecture invariants tests
│   │   ├── test_db_contract.py             # DB migration and schema tests (integration)
│   │   └── test_integration.py             # Full system integration test (integration)
│   └── __init__.py
│
└── logs/                                   # Runtime logs (in .gitignore)
    └── ingestion.log
```

---

## Status

### Layer 1 — Data Ingestion
- **5 Python modules** in `ingestion/`: `http_client.py`, `collect_prices.py`, `collect_news.py`, `writer.py`, `orchestrator.py`
- Built from corrected v2.0 spec: resolved transaction model, lock race, unicode normalization, author resolution, empty headline observability, named SQL params
- **15 integration tests** (61 checks) — all pass
- Yahoo Finance OHLCV for 5 assets (NVDA, AAPL, MSFT, SPX, BTC-USD)
- 6 RSS feed sources (reuters, ap, yahoo_general, yahoo_ticker, cnbc, marketwatch)
- Shared `fetch_with_retry()` HTTP client with configurable retry policy
- NFKC unicode normalization for headlines
- Author resolution: `feedparser.authors[].name` → `<author>` fallback
- Empty headline counting with WARNING logging
- O_EXCL atomic lock acquisition
- Pipe-delimited logging to `logs/ingestion.log`
- Corrected transaction model: prices = transactional (all-or-nothing), news = not (per-row idempotency)
- Cron job installer and log rotation scripts
- `normalize_price_response()` at `collect_prices.py:23` — parses Yahoo Finance chart JSON response
- Zero `sys.exit()` in library code — all replaced with `raise Exception` for graceful error propagation
- `write_headline()` rolls back on `UniqueViolation` — prevents aborted transactions from breaking batch

### Layer 2 — PostgreSQL Persistence
- **6 migration files** in `sql/`: schema (`001_`), raw functions (`002_`), signal tables (`003_`), build, rollback, test
- `002_fix_schema.sql` creates `raw` schema, `raw.insert_price_record()`, `raw.insert_headline_record()`, `config.news_sources`, views `raw.prices` and `raw.news_headlines` — bridges writer.py calls to `public.prices` and `public.headlines`
- **10 tables**, **2 views**, **13 functions**, **6 triggers**, **4 roles**
- Schema: `raw` (prices, news_headlines), `ops` (ingestion_runs, ingestion_health), `config` (monitored_assets, asset_aliases, news_sources)
- Atomic write primitives (`insert_price_record`, `insert_headline_record`)
- 4 STABLE read-only functions for Layer 3 consumption
- Partial unique index for correction tracking
- Idempotent DDL with transactional build
- 24 validation queries — all pass

### Layer 3 — NLP Intelligence
- **6 modules** in `layers/`: config, entity, sentiment, momentum, orchestrator, lm_lexicon
- Entity resolution: two-phase (URL param → alias regex)
- Sentiment: Loughran-McDonald lexicon (558 words, 6 categories), rolling 20-day z-scores
- Momentum: simple daily returns, rolling 20-day z-scores (two-phase commit prevents look-ahead bias)
- `lm_lexicon.py` extracted as standalone module with `score_text()` and `net_sentiment()` exported via `layers/__init__.py`
- Module path: `from layers.layer3_* import ...`
- 16 integration tests (100+ checks) — all pass
- Zero external dependencies (stdlib only)

### Layer 4 — Signal Generation
- **5 modules** in `layers/`: measurement, persistence, classification, orchestrator, integration
- NDI = sentiment_zscore - momentum_zscore (canonical name: `calculate_narrative_divergence_index` at `layer4_measurement.py:43`; `calculate_ndi` alias for backward compatibility)
- Inverted-U confidence, streak tracking, regime classification
- Stale-gap detection (3-day max), explicit save on batch
- `integration.py` provides `run_pipeline()` and `run_batch_pipeline()` as single entry points wiring L3→L4
- Module path: `from layers.layer4_* import ...`
- **15 tests (80+ checks) — all pass** (restored 2026-06-12: was broken due to missing symbols)
- 12-field output schema: ticker, date, ndi, ndi_delta, ndi_trend, regime, signal_state, confidence, price_modifier, persistence_days, risk_level, attention
- Exports functional API: `process_asset()`, `process_batch()`, `validate_batch_input()`, `OUTPUT_FIELDS`
- No hardcoded credentials — all config via `.env` / environment variables
- Input validation guards `price_history is None` in `validate_input()` — prevents `TypeError` on missing data
- Thresholds from `config/thresholds.py` (`MIN_PRICE_HISTORY_DAYS`) instead of magic literals
- Single orchestrator implementation (`layer4_orchestrator_simple.py` deleted — zero active imports)

### Layer 5 — Fundamental Analysis
- **3 modules** in `layers/fundamental/`: `fundamental_engine.py`, `metrics_calculator.py`, `score_aggregator.py`
- Computes valuation ratios (P/E, P/B, P/S), growth metrics (EPS/revenue CAGR), profitability (margins, ROE, ROA), cash flow (FCF yield, dividend yield), financial health (D/E, current ratio)
- Sector-benchmarked scoring against Technology, Financials, Healthcare, Consumer, Energy, Industrial benchmarks
- Produces 0–100 fundamental score with quality rating (Excellent / Good / Fair / Poor / Distressed)
- Integrated with Layer 4 via `process_signal()` — fundamental score acts as overlay on NDI
- Example fundamentals provided for NVDA, AAPL, MSFT
- Depends on `numpy` (not stdlib only)

### L3→L4 Pipeline
- `Layer3Orchestrator` + `layer4.process_batch()` wired in `scripts/demo.py`
- `layers/integration.py` provides consolidated `run_pipeline()` entry point
- End-to-end 20-day synthetic data verification — all tests pass
- Demo: `python scripts/demo.py` (stdlib only)

### Layer 5→L4 Integration (Fundamental)
- `Layer4Orchestrator.process_signal()` accepts optional `fundamental_data` parameter
- Fundamental score adjusts risk_level and confidence in the final signal
- Bubble Risk Score merges narrative, technical, and fundamental dimensions

### AI / LLM Router
- **2 modules** in `layers/`: `system_config.py`, `llm_router.py` (moved from `signaliq/core/`)
- `LLMRouter` singleton — supports **Gemini**, **GLM (ZhipuAI)**, **Groq**, and **MOCK** mode
- Primary LLM configured via `PRIMARY_LLM` env var from `.env` (no hardcoded keys in source)
- Fallback chain: primary → fallback (Groq) → MOCK
- Integrated with Layer 4 via `layer4_orchestrator.py` — `process_signal()` calls `llm_router.analyze_signal()` for AI-powered recommendation
- `load_dotenv()` guarded by `ENVIRONMENT != 'test'` — no side effects in test imports
- `api_signaliq.py` — Flask REST API (4 endpoints: `/health`, `/analyze`, `/batch`, `/summary`)
- `backend/app/main.py` — CORS-enabled Flask API on port 10000 with rate limiting (Flask-Limiter: 200/day, 50/hour global; 10/min `/analyze`, 30/min `/classify`) and structured logging (`log_info`/`log_error` with JSON output toggle via `USE_JSON_LOGS` env var)

### Frontend (Layer 6 — Partial)
- **React TypeScript** app in `frontend/` — Create React App + Recharts 3.8 + Axios + Tailwind CSS
- KPI cards (High Confidence count, Avg NDI, Avg Bubble Risk, Market Regime)
- Signal table with color-coded NDI, confidence badges, bubble risk bars
- NDI distribution bar chart
- Connects to remote API via `REACT_APP_API_URL` env var (default: `http://localhost:10000`)
- Env files: `.env.production` (Render URL) and `.env.development` (localhost)
- **HTML alternatives**: `web/index.html` (dark-themed institutional), `web/test.html` (API test UI), `web/automatico.html` (automated dashboard)
- Not yet production-deployed

### Not started
- **Dedicated AI Processing Layer** (news summarization, entity intelligence, Co-Pilot) — the LLM Router provides the foundation but is not a standalone layer
- Production deployment / CI-CD

---

## Architecture

```
  Yahoo Finance ──→ ingestion ──→ sql ──→ layers/layer3_* ──→ layers/layer4_* ──→ layers/llm_router ──→ frontend/
                     prices      raw.prices         sentiment            signal state         LLM Router       React UI
  6 RSS Feeds  ──→  news        raw.news_headlines  momentum             persistence           Flask API       Dashboards
                     http_client ops.ingestion_runs  entity resolution    classification        Gemini / GLM
                     orchestrator config.*           orchestrator         orchestrator          Groq / MOCK
                                                                            integration
                                                                            fundamental
                                                                              ↓
                                                                   process_asset (functional API)
                                                                   process_batch
```

Data flows in two paths:

**Core pipeline:** fetch → normalize → write (Layer 1) → store (Layer 2) → analyze (Layer 3) → generate signals (Layer 4) → fundamental overlay (Layer 5 Fundamental). Layer 4 exposes a functional API (`process_asset`, `process_batch`) that wires together measurement, persistence, and classification sublayers.

**AI enhancement:** Layer 4 signals → `LLMRouter` (Gemini/GLM/Groq, configured via `PRIMARY_LLM` env var from `.env`) → AI-powered analysis → Flask API → frontend/dashboard.

Fundamental analysis acts as an overlay on the NDI signal, adjusting risk and confidence scores based on valuation, growth, profitability, cash flow, and financial health metrics.

---

## Commands

```bash
# Layer 1 — price collection
python -m ingestion.collect_prices
python -m ingestion.collect_prices --dry-run

# Layer 1 — news collection
python -m ingestion.collect_news
python -m ingestion.collect_news --source reuters
python -m ingestion.collect_news --dry-run

# Layer 1 — orchestrator (cron entry point)
python -m ingestion.orchestrator --type both
python -m ingestion.orchestrator --type prices
python -m ingestion.orchestrator --type news
python -m ingestion.orchestrator --type news --source reuters --dry-run

# Layer 2 — build database
psql $DATABASE_URL -f sql/master_build.sql
psql $DATABASE_URL -f sql/002_fix_schema.sql   # raw schema + wrapper functions
psql $DATABASE_URL -f sql/test_queries.sql

# Test suite (pytest is the single source of truth)
pytest tests/pytest/ -m "not integration" -v  # 8 tests (4 smoke + 4 architecture, no externals)
pytest tests/pytest/ -m integration -v        # DB contract + integration (requires DB/API running)

# Layer 5 — fundamental analysis
python -m tests.test_fundamental_engine   # Smoke test with examples

# Backend API server
python api_signaliq.py                    # Start Flask API (port 5000)

# Frontend
cd frontend && npm start                  # Start React dev server

# End-to-end demo
python scripts/demo.py

# Backtesting
python scripts/backtest_engine.py
python scripts/run_backtest_real.py

# Simplified NDI generation
python scripts/simple_ndi.py

# Verify project structure
python scripts/verify_refactor.py

# Install cron jobs
./scripts/install_crontab.sh
```

---

## Notes
- `config/entity_aliases.json` consumed by Layer 3 EntityResolver; `config/thresholds.py` provides `MIN_PRICE_HISTORY_DAYS` — single source of truth for thresholds
- Layer 1 installs no cron jobs automatically — run `scripts/install_crontab.sh`
- All tests mock external dependencies — no network or database required
- Pytest is the single source of truth: `pytest tests/pytest/ -m "not integration" -v` (8 tests: Layer4, Config, Layer1, API, 4 architecture invariants)
- `layers/lm_lexicon.py` is the canonical Loughran-McDonald lexicon source (558 words, 6 categories, imported by `layer3_sentiment.py`)
- `layers/__init__.py` exports `score_text`, `net_sentiment`, `run_pipeline`, and `run_batch_pipeline` as the public API
- `layers/llm_router.py` provides the `LLMRouter` singleton — set `PRIMARY_LLM=gemini` (or `glm`, `groq`, `mock`) in `.env` (no hardcoded API keys in source code)
- `docker-compose.yml` reads API keys from `.env` via `${VAR:-}` references — never hardcoded
- `layers/system_config.py` exposes `DATA_DIR`, `db` (with `.url`), `db_url`, and all LLM provider settings — all config from environment
- No `sys.exit()` in library code — exceptions propagate to callers for graceful handling
- `load_dotenv()` guarded by `ENVIRONMENT != 'test'` in `llm_router.py` and `system_config.py` — prevents side effects during test imports
- API rate limiting via Flask-Limiter (memory fallback for dev); 10 req/min on `/api/analyze`, 30 req/min on `/api/classify`
- Structured logging in `backend/app/main.py`: `log_info()`/`log_error()` with JSON output toggle via `USE_JSON_LOGS`
- `layer4_orchestrator_simple.py` deleted — only `layers.layer4_orchestrator` remains
- `calculate_narrative_divergence_index()` is the canonical NDI function in `layer4_measurement.py`
- Architecture invariants enforced by `test_architecture.py` (4 tests: single orchestrator, no circular imports, consistent NDI formula, zero `sys.exit`)
- `config/thresholds.py` holds all production thresholds — edit there instead of inlining numbers
- Fundamental engine requires `numpy`; all other layers remain stdlib-only
- `frontend/` is a Create React App — run `npm install && npm start` from `frontend/` to launch
- `api_signaliq.py` runs a Flask server on port 5000; `backend/app/main.py` on port 10000
