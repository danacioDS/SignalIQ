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
- **Stdlib-only core**: Core analytics are pure Python (only `ingestion/` and `layers/fundamental/` have external deps)

### Tech Stack

| Category | Technologies |
|----------|-------------|
| **Backend** | Python 3.12, Flask 3.0, flask-cors 4.0, Flask-Limiter 3.5 |
| **Frontend** | React 19, TypeScript 4.9, Recharts 3.8, Axios 1.17, Tailwind CSS 3.4 |
| **Database** | PostgreSQL (raw, ops, config, layer4 schemas) |
| **AI/LLM** | Google Gemini, GLM (ZhipuAI), Groq, MOCK mode |
| **Infrastructure** | Docker, Docker Compose |
| **Data Sources** | Yahoo Finance (yfinance 0.2), 6 RSS feeds (feedparser) |
| **External Deps** | psycopg2-binary, requests, numpy (only Layer 5), google-generativeai, groq |

### Core Philosophy

When narrative runs ahead of price action, SignalIQ flags it as exhaustion, distribution, or severe divergence — not a prediction, but a systematic measurement of risk conditions. Signals classify into 4 risk regimes and 3 signal states based on the persistence and magnitude of the divergence.

---

## Project Structure

```
repo root/
├── architecture.md                         # This file — system map
├── README.md                               # Repo readme
├── api_signaliq.py                         # Legacy Flask REST API (port 5000)
├── signals_demo.csv                        # Demo signal output
├── .env.example                            # DATABASE_URL + LLM config template
├── .gitignore
├── pytest.ini                              # Pytest config (smoke/integration/slow markers)
├── requirements_layer1.txt                 # Layer 1 dependencies (psycopg2, requests, feedparser)
├── requirements_test.txt                   # Test dependencies (pytest, pytest-cov, requests)
├── Dockerfile                              # Python 3.12-slim backend build
├── docker-compose.yml                      # Multi-service orchestration (port 5000)

├── package.json                            # Root recharts dep
├── pitch.md                                # Commercial pitch
├── workflow.md                             # Development workflow
├── report.md                               # Additional documentation
│
├── backend/                                # Flask API (primary, port 10000)
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                         # CORS Flask API + rate limiting (Flask-Limiter)
│   │   ├── db.py                           # ThreadedConnectionPool for PostgreSQL
│   │   ├── classification/
│   │   │   ├── __init__.py
│   │   │   └── event_classifier.py         # 9 event types
│   │   └── scoring/
│   │       ├── __init__.py
│   │       └── signal_score.py             # Weighted signal scoring
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── static/                             # React build output
│   └── update_tickers.py
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
│   ├── system_config.py                    # SignalIQConfig singleton
│   ├── llm_router.py                       # LLMRouter (Gemini, GLM, Groq, MOCK)
│   ├── layer3_config.py                    # L3 frozen config dataclass
│   ├── layer3_entity.py                    # L3 entity resolution (two-phase)
│   ├── layer3_sentiment.py                 # L3 Loughran-McDonald lexicon + rolling z-score
│   ├── layer3_momentum.py                  # L3 daily returns + rolling z-score (two-phase commit)
│   ├── layer3_orchestrator.py              # L3 pipeline orchestration
│   ├── layer4_measurement.py               # L4 validity gate, NDI, 5-day return
│   ├── layer4_persistence.py               # L4 streak tracking, stale-gap, signal state
│   ├── layer4_classification.py            # L4 confidence, price pressure, risk, attention
│   ├── layer4_orchestrator.py              # L4 9-step pipeline, batch processing, LLM integration
│   ├── integration.py                      # L3→L4 pipeline integration entry point
│   └── fundamental/                        # Layer 5 — Fundamental Analysis (3 modules)
│       ├── __init__.py
│       ├── fundamental_engine.py           # Main engine: processes metrics, caches results
│       ├── metrics_calculator.py           # Valuation ratios, growth, profitability, cash flow
│       └── score_aggregator.py             # Sector-benchmarked scoring (0–100)
│
├── frontend/                               # Layer 6 — React TypeScript UI
│   ├── public/
│   ├── src/
│   │   ├── App.tsx                         # Main app with 6 sections
│   │   ├── index.tsx                       # Entry point
│   │   └── pages/
│   │       ├── Dashboard.tsx               # KPI cards, NDI chart, signal table
│   │       └── Landing.tsx                 # Hero, live signals, ticker analyzer
│   ├── package.json                        # React 19, Recharts 3.8, Axios, Tailwind
│   ├── tsconfig.json
│   ├── tailwind.config.js
│   └── postcss.config.js
│
├── web/                                    # Standalone HTML dashboards
│   ├── index.html                          # Dark-themed institutional dashboard
│   ├── automatico.html                     # Automated analysis dashboard
│   └── test.html                           # Simple API test UI
│
├── sql/                                    # Layer 2 — SQL migrations (6 files)
│   ├── 001_create_layer2_schema.sql        # Core schema (prices, headlines, ndi_signals)
│   ├── 002_fix_schema.sql                  # raw/config/layer4 schemas, wrapper functions
│   ├── 003_create_signal_tables.sql        # news_articles, score_configs, signal_predictions
│   ├── master_build.sql                    # Transactional build wrapper
│   ├── rollback.sql                        # Complete teardown
│   └── test_queries.sql                    # 24 validation queries
│
├── scripts/                                # Operations, demo, backtesting
│   ├── demo.py                             # End-to-end synthetic demo (stdlib only)
│   ├── simple_ndi.py                       # Simplified NDI signal generator
│   ├── generate_ndi.py                     # DB-backed NDI generation
│   ├── backtest_engine.py                  # NDI backtesting engine (pandas/numpy)
│   ├── backtest_improved.py                # Enhanced backtesting with metrics
│   ├── run_backtest_real.py                # Production backtest runner
│   ├── validate_ndi.py                     # NDI predictive power validation
│   ├── verify_refactor.py                  # Structural verification script
│   ├── install_crontab.sh                  # Idempotent cron installer
│   └── rotate_logs.sh                      # Daily rotation, 90-day retention
│
├── config/                                 # Configuration files
│   ├── thresholds.py                       # Production-critical thresholds
│   └── entity_aliases.json                 # Alias entries for Layer 3 (5 tickers)
│
├── tests/                                  # Official test suite
│   ├── __init__.py
│   └── pytest/                             # Pytest tests (single source of truth)
│       ├── test_smoke.py                   # 4 smoke tests: Layer4, Config, Layer1, API
│       ├── test_architecture.py            # 4 architecture invariant tests
│       ├── test_db_contract.py             # 3 DB migration/schema tests (integration)
│       └── test_integration.py             # 2 full system integration tests (integration)
│
├── docs/                                   # Documentation
│   ├── conceptual/                         # 6 docs: pitch, economics, statistics, commercial, data, operations
│   ├── hld/                                # 6 high-level design docs
│   ├── lld/                                # 4 low-level design docs
│   ├── production_specification/           # 5 production architecture specs
│   └── prompts/                            # 4 development prompt docs
│
└── logs/                                   # Runtime logs (in .gitignore)
    └── ingestion.log
```

---

## Status

### Layer 1 — Data Ingestion
- **5 Python modules** in `ingestion/`: `http_client.py`, `collect_prices.py`, `collect_news.py`, `writer.py`, `orchestrator.py`
- Built from corrected v2.0 spec: resolved transaction model, lock race, unicode normalization, author resolution, empty headline observability, named SQL params
- Yahoo Finance OHLCV for 5 assets (NVDA, AAPL, MSFT, SPX, BTC-USD)
- 6 RSS feed sources (reuters, ap, yahoo_general, yahoo_ticker, cnbc, marketwatch)
- Shared `fetch_with_retry()` HTTP client with configurable retry policy (timeout, ConnectionError, 429, 5xx)
- NFKC unicode normalization for headlines
- Author resolution: `feedparser.authors[].name` → `<author>` fallback
- Empty headline counting with WARNING logging
- O_EXCL atomic lock acquisition
- Pipe-delimited logging to `logs/ingestion.log`
- Corrected transaction model: prices = transactional (all-or-nothing), news = not (per-row idempotency via SHA256 dedup)
- Cron job installer and log rotation scripts
- `normalize_price_response()` at `collect_prices.py:23` — parses Yahoo Finance chart JSON response
- Zero `sys.exit()` in library code — all replaced with `raise Exception` for graceful error propagation
- `write_headline()` rolls back on `UniqueViolation` — prevents aborted transactions from breaking batch

### Layer 2 — PostgreSQL Persistence
- **6 migration files** in `sql/`: schema (`001_`), raw functions (`002_`), signal tables (`003_`), build, rollback, test
- `002_fix_schema.sql` creates `raw`, `config`, `layer4` schemas, `raw.insert_price_record()`, `raw.insert_headline_record()`, `config.news_sources`, views `raw.prices` and `raw.news_headlines` — bridges writer.py calls to `public.prices` and `public.headlines`
- **10 tables**, **2 views**, **13 functions**, **6 triggers**, **4 roles**
- **Schemas**: `raw` (prices, news_headlines), `ops` (ingestion_runs, ingestion_health), `config` (monitored_assets, asset_aliases, news_sources), `layer4` (ndi_signals)
- **Key tables**: `prices`, `headlines` (SHA256 dedup), `ndi_signals`, `news_articles`, `score_configs`, `signal_predictions`
- Atomic write primitives (`insert_price_record`, `insert_headline_record`)
- 4 STABLE read-only functions for Layer 3 consumption
- Partial unique index for correction tracking
- Idempotent DDL with transactional build
- 24 validation queries

### Layer 3 — NLP Intelligence
- **6 modules** in `layers/`: `layer3_config.py`, `layer3_entity.py`, `layer3_sentiment.py`, `layer3_momentum.py`, `layer3_orchestrator.py`, `lm_lexicon.py`
- Entity resolution: two-phase (URL param → alias regex for NVDA, AAPL, MSFT)
- Sentiment: Loughran-McDonald lexicon (558 words, 6 categories), rolling 20-day z-scores
- Momentum: simple daily returns, rolling 20-day z-scores (two-phase commit prevents look-ahead bias)
- `lm_lexicon.py` extracted as standalone module with `score_text()` and `net_sentiment()` exported via `layers/__init__.py`
- Module path: `from layers.layer3_* import ...`
- Zero external dependencies (stdlib only)

### Layer 4 — Signal Generation
- **5 modules** in `layers/`: `layer4_measurement.py`, `layer4_persistence.py`, `layer4_classification.py`, `layer4_orchestrator.py`, `integration.py`
- NDI = sentiment_zscore - momentum_zscore (canonical name: `calculate_narrative_divergence_index` at `layer4_measurement.py:43`; `calculate_ndi` alias for backward compatibility)
- Inverted-U confidence: mid-range NDI (0.8–2.2) is HIGH; extreme values (>2.2) are MEDIUM; low values are LOW; streak boost (+1 level at 3+ days)
- Streak tracking with stale-gap detection (3-day max), JSON-file persistence
- Regime classification: 4 risk regimes (ALIGNED, ACCUMULATION_DIVERGENCE, OVERHEATING_DIVERGENCE, INSUFFICIENT_DATA)
- Signal states: INACTIVE → WATCHING → ACTIVE (requires 2 consecutive threshold breaches)
- `integration.py` provides `run_pipeline()` and `run_batch_pipeline()` as single entry points wiring L3→L4
- Module path: `from layers.layer4_* import ...`
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
- Weighted composite: valuation 25%, growth 30%, profitability 20%, cash flow 15%, financial health 10%
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
- **2 modules** in `layers/`: `system_config.py`, `llm_router.py`
- `LLMRouter` singleton — supports **Gemini**, **GLM (ZhipuAI)**, **Groq**, and **MOCK** mode
- Primary LLM configured via `PRIMARY_LLM` env var from `.env` (no hardcoded keys in source)
- Fallback chain: primary → fallback (Groq) → MOCK
- Integrated with Layer 4 via `layer4_orchestrator.py` — `process_signal()` calls `llm_router.analyze_signal()` for AI-powered recommendation
- `load_dotenv()` guarded by `ENVIRONMENT != 'test'` — no side effects in test imports
- **Gemini**: models tried in order — `gemini-2.5-flash`, `gemini-1.5-flash`, `gemini-pro`
- **GLM**: model `glm-4.7-flash` via ZhipuAI
- **Groq**: model `llama-3.3-70b-versatile` via Groq
- **MOCK**: built-in fallback with structured ASCII art output

### Flask API (Backend)
- **Two API servers**: `backend/app/main.py` (primary, port 10000) and `api_signaliq.py` (legacy, port 5000)
- **`backend/app/main.py`** endpoints:

| Endpoint | Method | Rate Limit | Purpose |
|----------|--------|------------|---------|
| `/api/health` | GET | — | Health check, returns mode (REAL/MOCK) |
| `/api/version` | GET | — | Build version (`2026-06-12`) |
| `/api/stats` | GET | — | DB stats: total signals, bullish, avg score, active tickers |
| `/api/signals` | GET | — | Last 50 signals from `signal_predictions` |
| `/api/score/<ticker>` | GET | — | Latest signal for a specific ticker |
| `/api/classify` | POST | 30/min | Classifies news title/content into event type |
| `/api/analyze/<ticker>` | GET | 10/min | Gemini-powered stock analysis (BUY/SELL/HOLD) |
| `/api/routes` | GET | — | Lists all registered API routes |
| `/` | GET | — | Serves frontend `index.html` |

- **Global rate limits**: 200/day, 50/hour (memory:// fallback or Redis)
- **Input validation**: ticker (1-10 alphanumeric/hyphens), date range (YYYY-MM-DD, max 5 years)
- **Event classifier**: 9 event types in `backend/app/classification/event_classifier.py`
- **Signal scoring**: weighted scoring in `backend/app/scoring/signal_score.py`
- CORS-enabled, structured logging with JSON output toggle via `USE_JSON_LOGS`

### Frontend (Layer 6 — Partial)
- **React TypeScript** app in `frontend/` — Create React App + Recharts 3.8 + Axios + Tailwind CSS
- **6 sections in App.tsx**: Dashboard (KPI cards, NDI chart, signal table), Economic Foundation (5 pillars), Statistical Methodology, Data Recovery Strategy, Tech Stack, Architecture
- **Dashboard**: live signals grid, NDI evolution chart, interactive ticker analyzer
- **Landing page**: hero section, live signals, ticker analyzer, beta signup
- Connects to remote API via `REACT_APP_API_URL` env var (default: `http://localhost:10000`)
- **HTML alternatives**: `web/index.html` (dark-themed institutional), `web/test.html` (API test UI), `web/automatico.html` (automated dashboard)
- Not yet production-deployed

### Not started
- Production deployment / CI-CD

---

## Architecture

```
  Yahoo Finance ──→ ingestion ──→ sql ──→ layers/layer3_* ──→ layers/layer4_* ──→ layers/llm_router ──→ frontend/
                     prices      raw.prices         sentiment            signal state         LLM Router       React UI
  6 RSS Feeds  ──→  news        raw.news_headlines  momentum             persistence           Flask API       Dashboards
                     http_client ops.ingestion_runs  entity resolution    classification        Gemini / GLM    web/
                     orchestrator config.*  layer4.*  orchestrator         orchestrator          Groq / MOCK
                                                                             integration
                                                                             fundamental
                                                                               ↓
                                                                    process_asset (functional API)
                                                                    process_batch

  Deployment:
  Dockerfile ──→ docker-compose.yml
  backend/app/main.py (port 10000, rate-limited)
  api_signaliq.py (port 5000, legacy)
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
psql $DATABASE_URL -f sql/test_queries.sql

# Test suite (pytest is the single source of truth)
pytest tests/pytest/ -m "not integration" -v  # 8 tests (4 smoke + 4 architecture, no externals)
pytest tests/pytest/ -m integration -v        # 5 tests (3 DB contract + 2 integration, requires DB/API)

# Layer 5 — fundamental analysis
python -m layers.fundamental.fundamental_engine

# Backend API server (primary)
python -m app.main                            # Start Flask API from backend/ (port 10000)

# Backend API server (legacy)
python api_signaliq.py                        # Start Flask API (port 5000)

# Frontend
cd frontend && npm start                      # Start React dev server

# End-to-end demo
python scripts/demo.py

# Backtesting
python scripts/backtest_engine.py
python scripts/run_backtest_real.py

# DB-backed NDI generation
python scripts/generate_ndi.py

# NDI validation
python scripts/validate_ndi.py

# Simplified NDI generation
python scripts/simple_ndi.py

# Verify project structure
python scripts/verify_refactor.py

# Install cron jobs
./scripts/install_crontab.sh

# Docker
docker compose up -d
```

---

## Notes
- `config/entity_aliases.json` consumed by Layer 3 EntityResolver; `config/thresholds.py` provides `MIN_PRICE_HISTORY_DAYS` — single source of truth for thresholds
- Layer 1 installs no cron jobs automatically — run `scripts/install_crontab.sh`
- All tests mock external dependencies — no network or database required
- Pytest is the single source of truth: `pytest tests/pytest/ -m "not integration" -v` (8: Layer4, Config, Layer1, API, 4 architecture invariants)
- `layers/lm_lexicon.py` is the canonical Loughran-McDonald lexicon source (558 words, 6 categories, imported by `layer3_sentiment.py`)
- `layers/__init__.py` exports `score_text`, `net_sentiment`, `run_pipeline`, and `run_batch_pipeline` as the public API
- `layers/llm_router.py` provides the `LLMRouter` singleton — set `PRIMARY_LLM=gemini` (or `glm`, `groq`, `mock`) in `.env` (no hardcoded API keys in source code)
- `layers/system_config.py` exposes `DATA_DIR`, `db` (with `.url`), `db_url`, and all LLM provider settings — all config from environment
- `docker-compose.yml` reads API keys from `.env` via `${VAR:-}` references — never hardcoded
- No `sys.exit()` in library code — exceptions propagate to callers for graceful handling
- `load_dotenv()` guarded by `ENVIRONMENT != 'test'` in `llm_router.py` and `system_config.py` — prevents side effects during test imports
- API rate limiting via Flask-Limiter (memory fallback for dev); 10 req/min on `/api/analyze`, 30 req/min on `/api/classify`
- Structured logging in `backend/app/main.py`: `log_info()`/`log_error()` with JSON output toggle via `USE_JSON_LOGS`
- `layer4_orchestrator_simple.py` deleted — only `layers.layer4_orchestrator` remains
- `calculate_narrative_divergence_index()` is the canonical NDI function in `layer4_measurement.py`
- Architecture invariants enforced by `test_architecture.py` (4 tests: single orchestrator, no circular imports, consistent NDI formula, zero `sys.exit()`)
- `config/thresholds.py` holds all production thresholds — edit there instead of inlining numbers
- Fundamental engine requires `numpy`; all other layers remain stdlib-only
- `frontend/` is a Create React App — run `npm install && npm start` from `frontend/` to launch
- `backend/app/main.py` runs on port 10000; `api_signaliq.py` runs on port 5000
- `signaliq/core/` directory was merged into `layers/` — LLM Router, config, and persistence now reside there
- `data_storage/` renamed to `sql/`; `layer1/` renamed to `ingestion/`
- `demo.py` and `simple_ndi.py` moved to `scripts/`
