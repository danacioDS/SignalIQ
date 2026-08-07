# SignalIQ Architecture

> **Last updated:** August 7, 2026 (revision `main` @ `130a686`)

## Overview

**SignalIQ** is a market intelligence framework that measures the divergence between what the market is *saying* (news sentiment/narrative) and what the market is *actually doing* (price momentum). It quantifies this gap using the **Narrative Divergence Index (NDI)**:

```
NDI = (sentiment - momentum) × scale_factor
```

Markets are driven by stories as much as by numbers. Stories are created, spread, overheat, and exhaust themselves. Numbers (prices, volatility, volume) are slower and heavier. SignalIQ measures the distance between the hot (narrative) and the cold (prices).

### Key Features
- **NDI formula**: `(sentiment - momentum) × 3.0` (production API, clamped to [-3, 3]) — core L4 uses `sentiment_zscore - momentum_zscore` (rolling 20-day z-scores)
- **4 risk regimes (core L4)**: Aligned, Accumulation Divergence, Overheating Divergence, Insufficient Data
- **7 risk regimes (API + frontend)**: Extreme Overheating, Overheating, Watching, Neutral/Stable, Aligned, Strong Undervalued, Capitulation/Extreme Undervalued
- **3 signal states**: Inactive → Watching → Active (requires 2 consecutive threshold breaches)
- **Inverted-U confidence**: Mid-range NDI (0.8–2.2) is most reliable; extreme values are down-weighted
- **LLM Router**: Multi-provider support (Gemini, GLM/ZhipuAI, Groq, MOCK mode)
- **Fundamental overlay**: Adjusts NDI risk/confidence based on valuation, growth, and financial health
- **Stdlib-only core**: Core analytics are pure Python (only fundamental Layer 5 and ingestion have external deps)
- **Real news sentiment**: Production API integrates TextBlob-based sentiment from live RSS feeds
- **Multi-source prices**: Alpha Vantage → Twelve Data → Yahoo Finance cascading fallback
- **Rate limiting (new)**: flask-limiter applied (default `200/day` + `50/hour`; per-endpoint 10–30/min, in-memory storage)
- **Optional API-key auth (new, disabled)**: `API_KEY` env + `require_api_key` decorator, currently commented out
- **Production API**: Lightweight Flask server with real-time data (no database dependency)

### Tech Stack

| Category | Technologies |
|----------|-------------|
| **Backend (production)** | Python 3.12, Flask 3.0, Flask-CORS 4.0, flask-limiter 3.5 (**now applied**), yfinance 0.2.36, numpy, requests, feedparser, TextBlob |
| **Backend (declared deps)** | Also pins flask-talisman, redis, python-dotenv, python-json-logger — **never imported** |
| **Frontend** | React 19.2, TypeScript 4.9, Recharts 3.8, Axios 1.17, React Router 7, CRA 5 |
| **Database** | PostgreSQL (public, raw, config, layer4 schemas) — offline pipeline only |
| **AI/LLM** | Google Gemini (gemini-2.5-flash), Groq (llama-3.3-70b-versatile), GLM (glm-4.7-flash), MOCK mode |
| **Data Sources** | Yahoo Finance, Alpha Vantage, Twelve Data, Google News RSS, Yahoo Finance RSS, MarketWatch RSS |
| **Infrastructure** | Docker, Vercel (frontend), Render (backend), GitHub Actions (CI — added Aug 7, currently red) |

### Core Philosophy

When narrative runs ahead of price action, SignalIQ flags it as exhaustion, distribution, or severe divergence — not a prediction, but a systematic measurement of risk conditions. Signals classify into risk regimes and signal states based on the persistence and magnitude of the divergence.

---

## Architecture Diagram

```
                     ┌──────────────────────────────────────────────────┐
                     │                   Frontend                      │
                     │          React 19 + TypeScript UI               │
                     │   Dashboard · Economic · Data · Tech · About    │
                     │        API base centralized in config/api.ts    │
                     └──────────────────────┬──────────────────────────┘
                                             │ HTTP / JSON
                     ┌──────────────────────▼──────────────────────────┐
                     │          Flask API (port 10000)                 │
                     │      backend/app/main.py · 514 lines            │
                     │      7 endpoints (5 live on Render)             │
                     │      Multi-source: AV + Twelve + Yahoo          │
                     │      Real news sentiment (TextBlob)             │
                     │      NDI × 3.0 scale factor (clamped)           │
                     │      7-regime classification                    │
                     │      Thread-safe cache · CORS (5 unique)        │
                     │      Rate limiting (flask-limiter, in-memory)   │
                     └──────────────┬───────────────┬──────────────────┘
                                    │               │
                   ┌────────────────▼───┐   ┌───────▼────────────────┐
                   │  Price APIs        │   │  News RSS Feeds        │
                   │  Alpha Vantage     │   │  Google News (×2)      │
                   │  Twelve Data       │   │  Yahoo Finance         │
                   │  Yahoo Finance     │   │  MarketWatch           │
                   │  Hardcoded fallback│   │  TextBlob sentiment    │
                   └────────────────────┘   └────────────────────────┘

        ┌──────────────────────────────────────────────────────────────┐
        │             Core Pipeline (offline) — backend/app/layers/    │
        │                                                              │
        │  ┌───────────┐  ┌───────────┐  ┌───────────┐               │
        │  │ Layer 5   │  │ Layer 4   │  │ Layer 3   │               │
        │  │ Fund.     │  │ Signals   │  │ NLP       │               │
        │  │ Scoring   │  │ NDI Calc  │  │ LM Lexicon│               │
        │  │ Sector    │  │ Regime    │  │ Momentum  │               │
        │  │ Benchmarks│  │ Streak    │  │ Entity    │               │
        │  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘               │
        │        │              │              │                       │
        │        └──────────────┼──────────────┘                       │
        │                       │                                      │
        │        ┌──────────────▼──────────────┐                       │
        │        │       Layer 2 - Database    │                       │
        │        │    PostgreSQL (4 schemas)    │                       │
        │        │  10 tables · 2 views         │                       │
        │        │  13 functions · 6 triggers   │                       │
        │        │  Used by offline pipeline    │                       │
        │        └──────────────┬──────────────┘                       │
        │                       │                                      │
        │        ┌──────────────▼──────────────┐                       │
        │        │       Layer 1 - Ingestion   │                       │
        │        │  Yahoo Finance (5 assets)   │                       │
        │        │  6 RSS Feeds (news)         │                       │
        │        │  O_EXCL locks · Cron        │                       │
        │        └─────────────────────────────┘                       │
        └──────────────────────────────────────────────────────────────┘
```

Data flows in three paths:

**Core pipeline (offline/batch):** fetch → normalize → write (Layer 1) → store (Layer 2) → analyze (Layer 3) → generate signals (Layer 4) → fundamental overlay (Layer 5). All layer modules live under `backend/app/layers/` and import via `config.thresholds` / `layers.*` — they only resolve when `backend/app` is on `sys.path`.

**Live API path (production):** `backend/app/main.py` → price APIs (Alpha Vantage → Twelve Data → Yahoo Finance → fallback) → real news (TextBlob sentiment from RSS) → NDI `(sentiment - momentum) × 3` → 7-regime classification → JSON response. Operates independently of the database pipeline. ⚠️ Currently degraded by runtime bugs (see Flask API section) — every `/api/ticker` request falls back to minimal data.

**AI enhancement (offline):** Layer 4 signals → `LLMRouter` (Gemini/GLM/Groq, configured via `PRIMARY_LLM` env var) → AI-powered analysis. Not connected to the production API.

**Release flow:** `main` (dev + prod) → auto-deploy Vercel frontend + Render API. The former dev branch `feature/market_intelligence` is **stale** (2 commits behind `main`).

---

## Project Structure

```
repo root/
├── architecture.md                         # This file — system map
├── README.md                               # Project readme
├── report.md                               # Analysis & audit report
├── pitch.md                                # Commercial pitch
├── workflow.md                             # Development methodology
├── new_featrure.md                         # Branch/release strategy notes (outdated — work now lands on main)
├── signals_demo.csv                        # Sample signal output
├── .env.example                            # Environment variable template (placeholders only)
├── .env.template                           # Alternate env template
├── .python-version                         # Python 3.12.5
├── .gitignore                              # Git ignore rules
├── pytest.ini                              # Pytest config (smoke/integration/slow)
├── requirements.txt                        # Root deps (superset of backend/app)
├── requirements_layer1.txt                 # Layer 1 Python deps
├── requirements_test.txt                   # Test deps (pytest, pytest-cov)
├── Dockerfile                              # Root Docker image (legacy)
├── .github/
│   └── workflows/ci.yml                    # GitHub Actions: backend matrix, frontend build+test, ruff lint (red)
│
├── backend/                                # Flask backend API server
│   ├── Dockerfile                          # ✅ FIXED — CMD `python -m app.main` works
│   ├── requirements.txt                    # Backend deps (gunicorn no longer pinned)
│   ├── render.yaml                         # ✅ FIXED — startCommand `python -m app.main` works
│   ├── run.sh                              # Dev startup (cd backend && python app/main.py) — works
│   ├── check_cache.py                      # Cache inspection utility
│   ├── preload_cache.py                    # Cache preloading script
│   ├── fix_analyze.py                      # One-off main.py rewrite utility (scratch)
│   └── app/
│       ├── __init__.py                     # Empty — no sys.path bootstrap
│       ├── main.py                         # Production API (514 lines, v6.2, 7 endpoints, rate-limited)
│       ├── main.py.pre_logging             # ⚠️ 400-line tracked backup of pre-logging main.py
│       ├── main.py.bak_final               # ⚠️ untracked scratch file
│       ├── main.py.fixed                   # ⚠️ untracked 2-line placeholder
│       ├── api.py                          # Alternative entry (257 lines, User-Agent rotation)
│       ├── news_pipeline.py                # Real news sentiment (TextBlob + 4 RSS feeds)
│       ├── yahoo_proxy.py                  # Blueprint defined, never registered (dead)
│       ├── logging_config.py               # ⚠️ Structured logging — NOT imported; missing `import os`
│       ├── config/
│       │   └── thresholds.py               # Centralized thresholds
│       └── layers/                         # Layers 3, 4 & 5 + LLM Router (moved from repo root)
│           ├── __init__.py                 # Exports: score_text, net_sentiment,
│           │                               #   run_pipeline, run_batch_pipeline
│           ├── lm_lexicon.py               # Loughran-McDonald (558 words, 6 categories)
│           ├── system_config.py            # SignalIQConfig singleton
│           ├── llm_router.py               # LLMRouter (Gemini, GLM, Groq, MOCK)
│           ├── integration.py              # L1→L3→L4 pipeline entry
│           ├── layer3_config.py            # L3 frozen config dataclass
│           ├── layer3_entity.py            # L3 entity resolution (two-phase)
│           ├── layer3_sentiment.py         # L3 LM lexicon + rolling z-score
│           ├── layer3_momentum.py          # L3 daily returns + rolling z-score
│           ├── layer3_orchestrator.py      # L3 pipeline, TimeAligner, finalize_day()
│           ├── layer4_measurement.py       # L4 validity gate, NDI, 5d return
│           ├── layer4_persistence.py       # L4 streak tracking, stale-gap, state
│           ├── layer4_classification.py    # L4 confidence, price pressure, risk
│           ├── layer4_orchestrator.py      # L4 9-step pipeline + Layer4Orchestrator class
│           └── fundamental/                # Layer 5 — Fundamental Analysis
│               ├── __init__.py
│               ├── fundamental_engine.py   # Main engine, caching, NDI adjustment
│               ├── metrics_calculator.py   # Valuation, growth, profitability
│               └── score_aggregator.py     # Sector-benchmarked scoring (0-100)
│
├── ingestion/                              # Layer 1 — Data Ingestion
│   ├── __init__.py
│   ├── http_client.py                      # Shared HTTP with retry
│   ├── collect_prices.py                   # Yahoo Finance OHLCV (5 assets)
│   ├── collect_news.py                     # RSS feed collection (6 sources)
│   ├── writer.py                           # PostgreSQL atomic writes
│   └── orchestrator.py                     # O_EXCL locks, coordination
│
├── frontend/                               # Layer 6 — React TypeScript UI
│   ├── package.json                        # React 19.2, Recharts 3.8, Axios, React Router 7, CRA 5
│   ├── tsconfig.json
│   ├── .env.production                     # API URL: signaliq-api.onrender.com ✅
│   ├── .env.development                    # ⚠️ API URL: signaliq-l8mi.onrender.com (returns 404)
│   ├── public/
│   └── src/
│       ├── App.tsx                         # Shell with top nav + routes
│       ├── App.test.tsx                    # ⚠️ FAILS — cannot resolve react-router-dom
│       ├── index.tsx
│       ├── config/
│       │   └── api.ts                      # ✅ Centralized API_BASE / API_ENDPOINTS / DEFAULT_TICKERS
│       ├── components/
│       │   ├── styles.ts                   # Dark theme constants (C object)
│       │   ├── NDIGauge.tsx                # NDI gauge visualization
│       │   ├── NDIThermometer.tsx          # NDI thermometer visualization
│       │   ├── NDIVelocimeter.tsx          # SVG semi-circular gauge
│       │   ├── NarrativePanel.tsx          # Narrative analysis panel
│       │   ├── TickerFocusStrip.tsx        # Ticker focus/detail strip
│       │   ├── ScanTable.tsx               # Ticker scan results
│       │   ├── TickerAnalysis.tsx          # ⚠️ broken URL — `API_ENDPOINTS.ticker(${ticker}` (literal + missing `)`)
│       │   ├── ExpandedRow.tsx             # ⚠️ broken URL — `API_ENDPOINTS.signals?ticker=...` (literal)
│       │   ├── Layout.tsx                  # App layout shell
│       │   ├── EconomicFoundation.tsx      # Theory cards
│       │   ├── Methodology.tsx             # NDI explanation
│       │   ├── Architecture.tsx            # 6-layer diagram
│       │   ├── DataRecovery.tsx            # Data recovery view
│       │   ├── AnalysisContainer.tsx       # Analysis container
│       │   └── About.tsx                   # Author bio
│       ├── hooks/
│       │   └── useSignalAnalysis.ts        # Signal → regime analysis (7 regimes)
│       ├── constants/
│       │   └── ndiRegimes.ts               # NDI regime constants
│       ├── services/
│       │   └── yahoo-finance-service.ts    # ⚠️ broken URL + calls /api/prices/<ticker> (no such route)
│       ├── utils/
│       │   ├── regimeHelpers.ts            # Regime classification helpers
│       │   └── velocimeterUtils.ts         # Velocimeter SVG utilities
│       ├── setupProxy.js                   # ✅ proxies /api → signaliq-api.onrender.com
│       └── pages/
│           ├── Dashboard.tsx               # Main signals dashboard (uses config/api.ts)
│           ├── EconomicFoundation.tsx      # Economic foundation page
│           ├── Data.tsx                    # Data sources page
│           ├── TechStack.tsx               # Tech stack page
│           ├── About.tsx                   # About page
│           ├── Docs.tsx                    # Documentation page
│           ├── Intelligence.tsx            # Market Intelligence page
│           ├── ScanTable.tsx               # Scan results page
│           └── ExpandedRow.tsx             # ⚠️ broken URL — same template-literal bug as component
│
├── sql/                                    # Layer 2 — SQL Migrations (6 files)
│   ├── 001_create_layer2_schema.sql        # Core tables (public.prices, headlines, ndi_signals)
│   ├── 002_fix_schema.sql                  # raw/config/layer4 schemas, wrapper functions, views
│   ├── 003_create_signal_tables.sql        # Signal classification tables
│   ├── master_build.sql                    # Transactional build wrapper
│   ├── rollback.sql                        # Complete teardown
│   └── test_queries.sql                    # 24 validation queries
│
├── scripts/                                # Operations & Utilities (15 files)
│   ├── demo.py                             # End-to-end synthetic demo (stdlib only)
│   ├── simple_ndi.py                       # Simplified NDI signal generator
│   ├── backtest_engine.py                  # NDI backtesting engine (pandas/numpy)
│   ├── backtest_improved.py                # Enhanced backtesting
│   ├── run_backtest_real.py                # Production backtest runner
│   ├── run_backtest_real_fixed.py          # Fixed backtest runner
│   ├── run_layer3_daily.py                 # Daily Layer 3 run
│   ├── run_layer3_historical.py            # Historical Layer 3 run
│   ├── run_layer3_historical_fixed.py      # Fixed historical runner
│   ├── run_layer3_pipeline.py              # Layer 3 pipeline
│   ├── generate_signals_direct.py          # Direct signal generation
│   ├── news_pipeline.py                    # News pipeline script
│   ├── install_crontab.sh                  # Install cron jobs
│   ├── rotate_logs.sh                      # Log rotation
│   └── verify_refactor.py                  # Structural verification
│
├── web/                                    # Standalone HTML dashboards
│   ├── index.html                          # Dark-themed institutional dashboard
│   ├── automatico.html                     # Automated dashboard
│   └── test.html                           # Simple API test UI
│
├── tests/                                  # Official test suite
│   └── pytest/                             # Single source of truth
│       ├── test_smoke.py                   # ⚠️ 2/4 FAIL locally — test_api_import asserts undefined get_ticker_data; test_import_layer4 needs dotenv
│       ├── test_architecture.py            # ⚠️ 2/4 FAIL — orchestrator count; imports nonexistent domain.ndi_calculator
│       ├── test_db_contract.py             # DB migration/schema tests (integration, skipped)
│       └── test_integration.py             # ⚠️ probes /api/health + /api/stats (not in main.py)
│
└── logs/                                   # Runtime logs (.gitignore)
    └── app.log
```

> **Removed since the previous revision:** `docker-compose.yml` (broken — referenced missing `worker.py` + Redis), stale root `main.py`, `backend/main.py.back_up`, `frontend/src/pages/Dashboard.tsx.backup_final` / `.backup_layout`, `frontend/src/services/yahoo-finance-service.ts.bak4`, `backend/app/force_rebuild.txt`.
>
> **Added since the previous revision:** `backend/app/logging_config.py`, `frontend/src/config/api.ts`, `.github/workflows/ci.yml`, `backend/app/main.py.pre_logging` (backup).
>
> **Note:** The root-level `layers/` and `config/` directories described in earlier versions of this document **no longer exist** — they moved into `backend/app/layers/` and `backend/app/config/`.

---

## Layer Details

### Layer 1 — Data Ingestion (`ingestion/`)

**5 modules.**

| Module | File | Responsibility |
|--------|------|---------------|
| HTTP Client | `http_client.py` | Shared `fetch_with_retry()` with configurable retry policy (timeout, connection errors, 429, 5xx) |
| Prices | `collect_prices.py` | Yahoo Finance OHLCV for NVDA, AAPL, MSFT, SPX, BTC-USD. Includes `normalize_price_response()` |
| News | `collect_news.py` | 6 RSS feeds (Reuters, AP, Yahoo General, Yahoo Ticker, CNBC, MarketWatch). NFKC normalization, SHA256 dedup |
| Writer | `writer.py` | PostgreSQL atomic writes via `raw.insert_price_record()` and `raw.insert_headline_record()` |
| Orchestrator | `orchestrator.py` | O_EXCL atomic file locks, pipe-delimited logging, cron entry point |

**Key design decisions:**
- Prices: transactional (all-or-nothing); News: per-row idempotent
- Zero `sys.exit()` in library code
- Cron: prices daily @20:05, news 3× daily (06, 12, 18)

### Layer 2 — PostgreSQL Persistence (`sql/`)

**6 migration files**, 24 validation queries. **Stats:** 10 tables, 2 views, 13 functions, 6 triggers, 4 schemas.

**Key constraints:**
- `UNIQUE(ticker, price_date, source)` on prices
- `UNIQUE(sha256_hash)` on headlines
- `UNIQUE(ticker, signal_date)` on ndi_signals

**Note:** Layer 2 serves the offline batch pipeline only. The production API (`main.py`) does not connect to the database.

### Layer 3 — NLP Intelligence (`backend/app/layers/`)

**6 modules**, pure Python stdlib.

| Module | Responsibility |
|--------|---------------|
| `lm_lexicon.py` | Loughran-McDonald financial sentiment lexicon. 558 words across 6 categories. Exports `score_text()` and `net_sentiment()` |
| `layer3_config.py` | Frozen dataclass: lookback 20 days, min valid days 10, cutoff 4 PM ET |
| `layer3_entity.py` | Two-phase entity resolution: URL parameter match → alias regex matching against 5 tickers |
| `layer3_sentiment.py` | LM lexicon scoring with legacy word-list fallback. Rolling 20-day z-scores via deque history |
| `layer3_momentum.py` | Daily return calculation. Two-phase commit prevents look-ahead bias |
| `layer3_orchestrator.py` | Coordinates entity, sentiment, momentum. `TimeAligner` (UTC→ET). `finalize_day()` |

### Layer 4 — Signal Generation (`backend/app/layers/`)

**5 modules**, 12-field output schema.

| Module | Responsibility |
|--------|---------------|
| `layer4_measurement.py` | NDI = `sentiment_zscore - momentum_zscore`. Validity gates, 5-day return. No clamping |
| `layer4_persistence.py` | `PersistenceTracker` — consecutive-day breaches, JSON persistence, stale-gap detection (3-day max) |
| `layer4_classification.py` | Inverted-U confidence, price pressure, risk escalation, attention text |
| `layer4_orchestrator.py` | 9-step pipeline. Exports `process_asset()`, `process_batch()`, `OUTPUT_FIELDS`, plus `Layer4Orchestrator` class with LLM integration. **Imports `layers.llm_router` at module load** (requires `dotenv`) |
| `integration.py` | Consolidated L3→L4 entry points: `run_pipeline()`, `run_batch_pipeline()` |

**Output schema (12 fields):**
`ticker, date, ndi, ndi_delta, ndi_trend, regime, signal_state, confidence, price_modifier, persistence_days, risk_level, attention`

**4 Regimes (core L4):**
| Regime | NDI Range | Description |
|--------|-----------|-------------|
| ALIGNED | \|NDI\| < 1.5 | Narrative matches price action |
| ACCUMULATION_DIVERGENCE | NDI < -1.5 | Price stronger than narrative (undervalued) |
| OVERHEATING_DIVERGENCE | NDI > 1.5 | Narrative stronger than price (overvalued) |
| INSUFFICIENT_DATA | < 2 valid points | Not enough data |

**7 Regimes (API `classify_regime` in `main.py`):**
| Regime | NDI Range | Recommendation |
|--------|-----------|---------------|
| EXTREME OVERHEATING | NDI > 2.0 | SELL |
| OVERHEATING | NDI > 1.5 | REDUCE |
| WATCHING | NDI > 0.5 | MONITOR |
| NEUTRAL | NDI > -0.5 | HOLD |
| ALIGNED | NDI > -1.5 | BUY |
| STRONG UNDERVALUED | NDI > -2.0 | STRONG BUY |
| CAPITULATION | NDI ≤ -2.0 | ACCUMULATE |

**7 Regimes (frontend `useSignalAnalysis.ts`)** — same thresholds, different labels/colors (STABLE vs NEUTRAL, EXTREME_UNDERVALUED vs CAPITULATION).

**3 Signal States:** Inactive → Watching (1 breach) → Active (2+ consecutive breaches).

**Confidence model:** Inverted-U. NDI between 0.8 and 2.2 receives highest confidence; below 0.8 or above 2.2 confidence decreases quadratically.

### Layer 5 — Fundamental Analysis (`backend/app/layers/fundamental/`)

**3 modules**, depends on numpy.

| Module | Responsibility |
|--------|---------------|
| `fundamental_engine.py` | Main engine: processes metrics, caches results, adjusts NDI risk/confidence |
| `metrics_calculator.py` | Valuation (P/E, P/B, P/S), growth (CAGR), profitability (margins, ROE, ROA), cash flow (FCF yield), health (D/E) |
| `score_aggregator.py` | Sector-benchmarked 0–100 scoring (Technology, Financials, Healthcare, Consumer, Energy, Industrial). Quality: Excellent/Good/Fair/Poor/Distressed |

**Integration:** Fundamental score adjusts NDI risk_level and confidence via `process_signal()`.

### LLM Router (`backend/app/layers/llm_router.py`)

**Singleton pattern** — 4 providers with fallback chain:

```
PRIMARY_LLM (env var, default: "mock") → FALLBACK_LLM (env var, default: "mock") → MOCK mode
```

| Provider | Model | Config |
|----------|-------|--------|
| Google Gemini | gemini-2.5-flash, gemini-1.5-flash | `GEMINI_API_KEY` |
| Groq | llama-3.3-70b-versatile | `GROQ_API_KEY` |
| GLM (ZhipuAI) | glm-4.7-flash | `GLM_API_KEY` |
| MOCK | — | No key required |

**Integration:** `Layer4Orchestrator.process_signal()` calls `llm_router.analyze_signal()`. **Not connected to the production API.**

**Note:** `system_config.py` defaults to `PRIMARY_LLM="glm"`, `FALLBACK_LLM="groq"` — inconsistent with `llm_router.py` defaults of `"mock"` for both.

### Flask API — Production (`backend/app/main.py`)

**514-line Flask application** — multi-source price data with real news sentiment. 7 endpoints, inline NDI calculation, 7-regime classification, rate-limited.

#### Endpoints

| Endpoint | Method | Description | Live? |
|----------|--------|-------------|-------|
| `/` | GET | API root with version (6.2), status, mode, available endpoints | ✅ 200 |
| `/health` | GET | Health check with cache TTL config and timestamp | ✅ 200 |
| `/api/ticker/<ticker>` | GET | Deep ticker analysis: NDI, regime, price history (20 points), real headlines, confidence | ✅ 200 (degraded) |
| `/api/signals-live` | GET | Batch signals for multiple tickers (`?tickers=AAPL,MSFT,...`) | ✅ 200 |
| `/api/tickers` | GET | Default ticker list (10 tickers) | ✅ 200 |
| `/api/prices` | GET | All-ticker prices for `yahoo-finance-service.ts` (NEW, Día 4) | ❌ 404 on deployed API |
| `/api/signals-intel` | GET | Signals intelligence for `ExpandedRow.tsx` (NEW, Día 4) | ❌ 404 on deployed API |

**Price sources (cascading fallback):**
1. Alpha Vantage — `GLOBAL_QUOTE` endpoint (requires `ALPHA_VANTAGE_API_KEY`)
2. Twelve Data — `/price` endpoint (requires `TWELVE_DATA_API_KEY`)
3. Yahoo Finance — `yf.Ticker.history(period="2d")`
4. Hardcoded fallback — `FALLBACK_PRICES` dict

**NDI Calculation (Live API):**

```python
def calculate_ndi(ticker):
    price, _ = get_price(ticker)       # Cascading: AV → Twelve → Yahoo → fallback
    history = get_price_history(ticker, days=30)  # ⚠️ returns a DICT, but treated as a list below
    news_data = process_news_for_ticker(ticker)  # Real RSS → TextBlob sentiment
    sentiment = news_data['sentiment']  # Average TextBlob polarity [-1, 1]
    momentum = (history[-1] - history[-10]) / history[-10]  # ⚠️ dict slices → TypeError
    ndi = (sentiment - momentum) * 3.0  # Scale factor for sensitivity
    ndi = clamp(ndi, -3.0, 3.0)        # Bounded output
```

This differs from the core L4 formula (`sentiment_zscore - momentum_zscore` using rolling 20-day z-scores). The API uses TextBlob sentiment × scale factor vs momentum period return — a **known architectural inconsistency** (the "triplicate NDI" issue).

**Sentiment fallback:** when no news are found, sentiment is simulated from price change (×8) + volatility (×3), clamped to [-1, 1].

**Caching:** thread-safe dict cache (`threading.Lock`); TTL per type: price=300s, history=600s, ticker=300s, signals=60s. Keys: `price_{ticker}`, `history_{ticker}_{days}`, `ticker_{ticker}`.

**Rate limiting (NEW):** `Limiter(key_func=get_remote_address)`, default limits `200 per day` + `50 per hour`; per-endpoint `10 per minute` (`/api/ticker/<ticker>`), `20 per minute` (`/api/signals-live`, `/api/signals-intel`), `30 per minute` (`/api/tickers`, `/api/prices`). **In-memory storage** — flask-limiter emits a startup warning recommending Redis.

**Authentication (NEW, disabled):** optional `API_KEY` env var + `require_api_key` decorator; the only application is commented out.

**CORS:** 6 list entries, **5 unique origins** — the entry `https://signaliq-api.onrender.com` appears **twice** (main.py:345-346).

**Import robustness (fixed):** `from .news_pipeline import process_news_for_ticker` with `except ImportError → from news_pipeline import ...`. Verified working: `python -m app.main` (Docker `CMD` + `render.yaml` `startCommand`), `cd backend/app && python main.py`, `cd backend && python app/main.py`. Gunicorn is no longer in `requirements.txt`.

**Price history:** always returns 20 data points — real API data when available, simulated random walk as fallback.

#### ⚠️ Critical runtime bugs (verified with the Flask test client, Aug 7, 2026)

| # | Bug | Location | Impact |
|---|-----|----------|--------|
| 1 | `get_ticker_data` is **not defined** | `main.py:468, 479` (`/api/signals-intel`) | **500 NameError** on the endpoint |
| 2 | `get_current_price` is **not defined** | `main.py:163` (`get_price_history` simulation branch) | NameError whenever real history is unavailable |
| 3 | `get_price()` caches a **float** but returns `(price, source)` | `main.py:80-126` | Cache hits break tuple unpacking → "cannot unpack non-iterable float object" in `/api/prices` / `/api/ticker` |
| 4 | `calculate_ndi` treats the **dict** from `get_price_history()` as a list | `main.py:212-265` (`len(history)`, `history[-1]`, `history[-20:]` on dict keys) | Every `/api/ticker` call raises and returns minimal fallback data (`news_count: 0`, `ndi: 0.0`) |
| 5 | All price sources labeled `"alphavantage"` | `main.py:108, 119, 126` | Twelve Data / Yahoo / fallback misreported |
| 6 | CORS origin duplicated | `main.py:345-346` | Duplicate entry |
| 7 | `flask_limiter` imported twice | `main.py:11-12, 27-28` | Dead import |
| 8 | Version mismatch | root `6.2` vs startup log `v6.1` | Cosmetic |

### News Pipeline (`backend/app/news_pipeline.py`)

**104-line standalone module** — real news sentiment for the production API.

```python
def process_news_for_ticker(ticker):
    headlines = fetch_news(ticker)       # From 4 RSS sources
    scores = [polarity(h) for h in headlines]  # TextBlob sentiment
    return {
        'sentiment': mean(scores),       # Average polarity [-1, 1]
        'count': len(headlines),
        'headlines': headlines[:10],
        'scores': scores[:10]
    }
```

**RSS Sources:**
| Source | URL Pattern |
|--------|------------|
| Google News | `news.google.com/rss/search?q={ticker}+stock+when:1d` |
| Google News (earnings) | `news.google.com/rss/search?q={ticker}+earnings+when:1d` |
| Yahoo Finance | `feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}` |
| MarketWatch | `marketwatch.com/rss/topstories` |

**Sentiment:** TextBlob polarity ([-1, 1]). No Loughran-McDonald (offline pipeline only).

**Note:** still uses `print()` on lines 44 and 84.

### Logging Config (`backend/app/logging_config.py`) — NEW, dead

**65-line structured-logging helper** (JSON formatter + `setup_logging()`). **Never imported by any module**, and **broken**: it references `os.environ` on line 44 without `import os` → `NameError` at import time. Wire it into `main.py` (and fix the import) or delete it.

### Flask API — Alternative (`backend/app/api.py`)

**257-line alternative entry point** — nearly identical to `main.py` but with:
- Exponential backoff retry for yfinance requests (User-Agent rotation)
- `/api/health` (both `/health` and `/api/health` prefixes)
- `/api/ticker/analysis/<ticker>` route (no `/api/ticker/<ticker>`, `/api/signals-live`, `/api/prices`, or `/api/signals-intel`)
- Used as a development/debug variant; not wired to production

### Unused / Dead Modules (current)

| Module | Lines | Purpose | Status |
|--------|-------|---------|--------|
| `yahoo_proxy.py` | 14 | `/api/yahoo-price/<ticker>` proxy Blueprint | Defined, never registered |
| `logging_config.py` | 65 | Structured JSON logging | Never imported; missing `import os` |
| `main.py.pre_logging` | 400 | Pre-logging snapshot of `main.py` | Tracked in git |
| `main.py.bak_final` / `main.py.fixed` | — | Scratch files | Untracked (`main.py.fixed` is a 2-line placeholder) |

**Removed since the previous revision:** `docker-compose.yml`, stale root `main.py`, `backend/main.py.back_up` (1,323 lines), `force_rebuild.txt`, `Dashboard.tsx.backup_*`, `yahoo-finance-service.ts.bak4`.

### Layer 6 — Frontend (`frontend/`)

**React 19.2 + TypeScript (CRA 5)** — 15 components, 9 pages, 37 TS files (~4,460 lines). **Builds cleanly; its single test fails.**

#### Routes

| Route | Page | Description |
|-------|------|-------------|
| `/` | Dashboard | Main signals dashboard (uses `config/api.ts`) |
| `/economic` | EconomicFoundation | Theory cards |
| `/data` | Data | Data sources |
| `/tech` | TechStack | Technology breakdown |
| `/about` | About | Author bio |

#### Key Components

| Component | Purpose |
|-----------|---------|
| `config/api.ts` | **NEW** — centralizes `API_BASE` (env `REACT_APP_API_URL` or default), `API_ENDPOINTS`, `DEFAULT_TICKERS` |
| `pages/Dashboard.tsx` | Main dashboard: signals, NDI gauge, price chart (Recharts), NDIFrameworkTable (7 regimes), NarrativePanel, TickerFocusStrip. ✅ Uses `config/api.ts` |
| `hooks/useSignalAnalysis.ts` | Transforms signal data into 7-regime analysis with explanatory text + inverted-U confidence |
| `NDIVelocimeter.tsx` | SVG semi-circular gauge |
| `NDIGauge.tsx` / `NDIThermometer.tsx` | NDI gauges |
| `NarrativePanel.tsx` / `TickerFocusStrip.tsx` | Narrative display / ticker strip |
| `components/TickerAnalysis.tsx` | ⚠️ **broken URL** — `` `API_ENDPOINTS.ticker(${ticker}` `` (literal string, missing `${}`, missing `)`) |
| `components/ExpandedRow.tsx` + `pages/ExpandedRow.tsx` | ⚠️ **broken URL** — `` `API_ENDPOINTS.signals?ticker=${ticker}` `` (literal string) |
| `services/yahoo-finance-service.ts` | ⚠️ **broken URL** — `` `API_ENDPOINTS.prices/${ticker}` `` (literal string) and calls `/api/prices/<ticker>` (no such route; backend exposes `/api/prices` for all tickers) |

**Styling:** Shared `C` object from `styles.ts` — dark theme, inline styles. Tailwind installed but unused.

**Data fetching:** Axios/fetch to API URLs centralized in `config/api.ts`. `Dashboard.tsx` interpolates correctly; three other files have **template-literal regressions** from the Día 4 refactor. `.env.production` → `signaliq-api.onrender.com` (correct); `.env.development` → `signaliq-l8mi.onrender.com` (**dead**, 404); `setupProxy.js` → `signaliq-api.onrender.com` (fixed).

**Standalone HTML dashboards** in `web/`: `index.html`, `automatico.html`, `test.html`.

---

## Configuration

### Thresholds (`backend/app/config/thresholds.py`)

```python
NDI_OVERHEATING = 1.5
NDI_WATCHING = 0.7
NDI_ALIGNED = 0.3
CONFIDENCE_BASE = 70
CONFIDENCE_MULTIPLIER = 15
PRICE_CHANGE_THRESHOLD = 0.02
MIN_PRICE_HISTORY_DAYS = 6
RATE_LIMIT_DEFAULT = "200 per day"
RATE_LIMIT_HOUR = "50 per hour"
RATE_LIMIT_PRICES = "10 per minute"
RATE_LIMIT_CLASSIFY = "30 per minute"
RATE_LIMIT_ANALYZE = "10 per minute"
CACHE_TTL_SECONDS = 300
```

**Note:** the rate-limit constants defined in `thresholds.py` are **not** what `main.py` uses — `main.py` configures the Limiter inline (default `200 per day` / `50 per hour`; per-endpoint 10–30/min).

### Environment Variables

| Variable | Purpose | Used By |
|----------|---------|---------|
| `PORT` | Server port (default: 10000) | Production API |
| `ALPHA_VANTAGE_API_KEY` | Alpha Vantage API key | Production API |
| `TWELVE_DATA_API_KEY` | Twelve Data API key | Production API |
| `API_KEY` | Optional API-key auth (`X-API-Key` header) | Production API (disabled by default) |
| `LOG_FORMAT` | `json` or `text` | `logging_config.py` (unused — not imported) |
| `PRIMARY_LLM` | LLM provider (gemini/glm/groq/mock) | Offline pipeline |
| `FALLBACK_LLM` | Fallback provider | Offline pipeline |
| `GROQ_API_KEY` | Groq API key | Offline pipeline |
| `GEMINI_API_KEY` | Gemini API key | Offline pipeline |
| `GLM_API_KEY` | ZhipuAI GLM API key | Offline pipeline |
| `DATABASE_URL` | PostgreSQL connection string | Offline pipeline |
| `CORS_ORIGINS` | CORS allowed origins | **Not used** — origins hardcoded |

**Note:** `load_dotenv()` in `layers/` is guarded by `ENVIRONMENT != 'test'`. `.env` is **not tracked** in git (placeholders only in `.env.example` / `.env.template`).

---

## Testing

### Backend — current status (verified Aug 7, 2026)

| Test File | Type | Tests | Result |
|-----------|------|-------|--------|
| `test_smoke.py` | Smoke | 4 | **2 FAIL locally** (`test_import_layer4` — `dotenv` not installed in the local venv, passes in CI where `backend/requirements.txt` installs it; `test_api_import` — asserts `hasattr(main, 'get_ticker_data')`, which is **undefined**) |
| `test_architecture.py` | Architecture | 4 | **2 FAIL** (`test_only_one_layer4_orchestrator` finds 2 orchestrator files — layer3 + layer4; `test_ndi_formula_consistency` imports nonexistent `domain.ndi_calculator`); 2 pass (real checks, no longer vacuous) |
| `test_db_contract.py` | Integration | 3 | Skipped (needs `DATABASE_URL`) |
| `test_integration.py` | Integration | 2 | Skipped; **contract stale** — probes `/api/health` + `/api/stats` which `main.py` does not expose |

**Run commands:**
```bash
pytest tests/pytest/ -m "not integration" -v   # ⚠️ currently 4 failed / 4 passed
pytest tests/pytest/ -m integration -v
pytest tests/pytest/ -v
```

**CI (`.github/workflows/ci.yml`, new) — currently red:**
- `backend-tests`: Python 3.11/3.12 matrix; installs `backend/requirements.txt` + pytest; runs `cd backend && python -m pytest ../tests/pytest/ -m "not integration"`. From the `backend` cwd the architecture tests resolve `backend/app/layers` relative to `backend/` → `test_only_one_layer4_orchestrator` fails on `os.path.exists`; `test_api_import` fails regardless.
- `frontend-tests`: `npm run build` (PASS); `npm test -- --watchAll=false --passWithNoTests || true` — the failing suite is masked by `|| true`.
- `lint`: `ruff check backend/app --ignore=E501` — ruff is not version-pinned; unused/duplicate imports and bare `except`s are likely flagged.

### Frontend
- `npm run build` — **PASS** (verified)
- `npm test` — **FAIL** (react-scripts 5 / Jest cannot resolve `react-router-dom` v7: `Cannot find module 'react-router/dom'`)

### Architecture Invariants (intended, enforced by `test_architecture.py`)
1. **Single orchestrator** — only one `Layer4Orchestrator` class defined (test currently fails: finds 2 orchestrator files, layer3 + layer4)
2. **No circular imports** — AST-based check for module self-imports (**real implementation since Día 3, passes**)
3. **NDI formula consistency** — asserts `domain = core × 3.0` (test currently fails: `domain` module doesn't exist)
4. **Zero sys.exit** — no `sys.exit()` in library code (passes)

### Code Quality
- **No linter configured locally** — CI runs `ruff` (unpinned); no `pyproject.toml` / ruff config
- **Minimal type hints** — partial (`mypy.ini` exists, unused)
- **Mixed language** — Spanish and English used inconsistently
- **CI added but red** — failing suite is now nominally caught, but the gate is open

---

## Deployment

### Live Production (verified Aug 7, 2026)

| Service | Platform | URL | Status |
|---------|----------|-----|--------|
| Frontend | Vercel | https://signaliq-zeta-ten.vercel.app | 200 OK |
| Backend | Render | https://signaliq-api.onrender.com | 200 OK (v6.2); `/health` healthy |
| Backend `/api/ticker/NVDA` | Render | https://signaliq-api.onrender.com/api/ticker/NVDA | 200 OK — **degraded** (news_count 0, ndi 0.0, fallback price) |
| Backend `/api/prices` | Render | https://signaliq-api.onrender.com/api/prices | **404** — deployed build predates the endpoint |
| Backend `/api/signals-intel` | Render | https://signaliq-api.onrender.com/api/signals-intel | **404** — deployed build predates the endpoint |
| ~~Backend (legacy)~~ | Render | https://signaliq-l8mi.onrender.com | **404** — still referenced in `frontend/.env.development` |

> The local repo is **1 commit ahead of `origin/main`** (`130a686`), and the deployed Render instance 404s on the two new endpoints added in the Día 4 commit — i.e., the deployed build is older than `origin/main`. Push + redeploy is required to make `/api/prices` and `/api/signals-intel` live.

### Docker

```bash
docker build -t signaliq-api ./backend
```

- **Base image:** python:3.12-slim, WORKDIR `/app` (= backend content)
- **Entrypoint:** `CMD ["python", "-m", "app.main"]` — ✅ **works** (verified). No gunicorn in requirements.
- `docker-compose.yml` was **deleted** (it referenced missing `worker.py` + Redis).

### Branch / Release Flow (changed Aug 7)

```
main (dev + prod) → https://signaliq-zeta-ten.vercel.app (auto-deploy)
   └── feature/market_intelligence — STALE, 2 commits behind (Día 1–5 landed directly on main)
```

### Cron Jobs

| Schedule | Command | Description |
|----------|---------|-------------|
| `5 20 * * *` | `python -m ingestion.orchestrator --type prices` | Daily price collection |
| `0 6,12,18 * * *` | `python -m ingestion.orchestrator --type news` | News collection (3× daily) |
| Daily | `scripts/rotate_logs.sh` | Log rotation, 90-day retention |

### Installation

```bash
./scripts/install_crontab.sh
python -m ingestion.orchestrator --type both
python -m ingestion.orchestrator --type prices --dry-run
```

---

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **6-layer architecture** | Clear separation of concerns; each layer independently testable and replaceable |
| **Stdlib-only core** | Layers 3–4 have zero external dependencies — stability and portability |
| **Two-phase commit for momentum** | Prevents look-ahead bias in z-score calculations |
| **Inverted-U confidence** | Down-weights extreme NDI values as potential noise; mid-range most reliable |
| **O_EXCL locks** | Prevents concurrent ingestion runs |
| **Idempotent DDL** | `IF NOT EXISTS` / `ON CONFLICT DO NOTHING` for safe re-execution |
| **LLM Router singleton** | Single point of configuration for all LLM providers |
| **Production API simplification** | yfinance + real news removes database operational burden |
| **Multi-source price cascade** | AV → Twelve → Yahoo → fallback ensures high availability |
| **NDI scale factor** | Factor of 3.0 amplifies small divergences; stable since Jul 10 |
| **Relative-import fallback for entrypoints** | `from .news_pipeline` → `from news_pipeline` lets both `python -m app.main` and `python main.py` work |
| **Rate limiting applied (Día 5)** | flask-limiter wired: default 200/day + 50/hour, per-endpoint 10–30/min (in-memory) |
| **Optional API-key auth** | `require_api_key` decorator + `API_KEY` env; disabled by default |
| **Centralized frontend API config** | `config/api.ts` replaces scattered hardcoded URLs (refactor partially regressed) |
| **CI via GitHub Actions** | Backend matrix + frontend build/test + ruff lint (added Aug 7, currently red) |

---

## Status Summary

### Completed (since the `238a4f7` revision)
- ✅ **Entrypoint fixed**: Dockerfile + render.yaml run `python -m app.main` (verified working)
- ✅ **News pipeline import hardened**: relative → absolute fallback
- ✅ **Rate limiting applied** (flask-limiter, in-memory): default + per-endpoint limits
- ✅ **Optional API-key auth** scaffolding (`API_KEY` env, `require_api_key` decorator)
- ✅ **CI added** (GitHub Actions: backend matrix, frontend build/test, ruff lint)
- ✅ **Cleanup**: `docker-compose.yml`, stale root `main.py`, `main.py.back_up`, `Dashboard.tsx.backup_*`, `.bak4`, `force_rebuild.txt` deleted
- ✅ **Frontend API config centralized** (`config/api.ts`); `setupProxy.js` + `api.py` CORS point to the live host
- ✅ **`.env.example` rewritten** with `API_KEY`, `LOG_FORMAT`, `CORS_ORIGINS`
- ✅ New endpoints `/api/prices` + `/api/signals-intel` added to `main.py` code
- ✅ All 6 layers implemented; dead-code purge; layers under `backend/app/layers/`
- ✅ Production API live on `signaliq-api.onrender.com` (v6.2); frontend live on Vercel
- ✅ No live secrets in tracked files

### Known Issues (current)
- **Test suite red**: 4/8 backend tests fail (new causes); CI is red
- **`main.py` runtime bugs (verified)**: `/api/signals-intel` → 500 (`get_ticker_data` undefined); `/api/ticker` degrades to fallback data (`get_price_history` dict treated as list; `get_current_price` undefined); cache/unpack mismatch; all sources labeled `alphavantage`
- **Frontend fetch regressions**: `API_ENDPOINTS.*` used as literal strings in 3 files (`ExpandedRow`, `TickerAnalysis`, `yahoo-finance-service`)
- **Deployed API 404s** on `/api/prices` + `/api/signals-intel`; live `/api/ticker` returns `news_count: 0` / fallback price
- **Legacy host in dev config**: `frontend/.env.development` → `signaliq-l8mi.onrender.com` (404)
- **Branch flow changed**: `feature/market_intelligence` stale; Día 1–5 landed directly on `main`
- **Triplicate NDI formula** (core L4 / API / frontend); 7 regimes (API + frontend) vs 4 (core L4)
- **Auth disabled** by default; rate limiting on in-memory storage (Redis not wired)
- **Frontend test red** (react-scripts 5 / React Router 7); ruff unpinned; `|| true` masks frontend test failures in CI
- **`logging_config.py` dead + broken** (missing `import os`); tracked backup `main.py.pre_logging`; untracked scratch files
- **Integration test contract stale** (`/api/health`, `/api/stats`)
- **Mixed language (ES/EN)**; `print()` in `news_pipeline.py`; LLM default mismatch; NDI scale factor unguarded by tests

### Future Directions
- Fix the four `main.py` runtime bugs and redeploy to Render; verify against the deployed host
- Fix the frontend template-literal regressions; align `yahoo-finance-service` with the `/api/prices` contract
- Make CI green: fix test assertions, run pytest from the repo root, pin ruff, drop `|| true`
- Reconcile API hostnames (`signaliq-l8mi` → `signaliq-api` in `.env.development`)
- NDI formula unification; regime model reconciliation (4 ↔ 7)
- Redis-backed rate limiting; enable API-key auth; frontend tests (fix Router resolution)
- Type hints + ruff config; unit tests for production API logic; freeze NDI scale factor with automated validation

---

## Commands

```bash
# Backend API server (production — works)
cd backend && python -m app.main
# or
cd backend/app && python main.py
# or
cd backend && python app/main.py

# Backend API server (alternative entry — dev variant)
cd backend/app && python api.py

# Test suite (currently 4/8 failing)
pytest tests/pytest/ -m "not integration" -v
pytest tests/pytest/ -m integration -v

# Frontend
cd frontend && npm start
cd frontend && npm run build      # PASS
cd frontend && npm test           # FAIL (react-router-dom resolution)

# Layer 1 — price collection
python -m ingestion.collect_prices --dry-run

# Layer 1 — news collection
python -m ingestion.collect_news --dry-run

# Layer 1 — orchestrator (cron entry point)
python -m ingestion.orchestrator --type both

# Layer 2 — build database
psql $DATABASE_URL -f sql/master_build.sql
psql $DATABASE_URL -f sql/test_queries.sql

# Backtesting / demo
python scripts/demo.py
python scripts/backtest_engine.py
python scripts/simple_ndi.py

# News pipeline test
cd backend/app && python news_pipeline.py NVDA

# Verify project structure
python scripts/verify_refactor.py

# Install cron jobs
./scripts/install_crontab.sh

# Docker (✅ entrypoint fixed)
docker build -t signaliq-api ./backend
```

---

## Notes

- `backend/app/config/thresholds.py` is the single source of truth for thresholds (its rate-limit constants are not what `main.py` uses — the Limiter is configured inline)
- `layers/lm_lexicon.py` (in `backend/app/layers/`) is the canonical Loughran-McDonald lexicon (558 words, 6 categories)
- `calculate_narrative_divergence_index()` is the canonical core NDI function in `layer4_measurement.py`
- The live API `calculate_ndi()` in `main.py` uses `(sentiment - momentum) × 3` with TextBlob — different from core L4's rolling z-score approach (known triplicate-formula issue). **Currently buggy**: `get_price_history()` returns a dict but the code slices it as a list → every request degrades to minimal fallback data.
- `classify_regime()` in `main.py` supports 7 regimes; core L4 uses 4 academic regimes
- `api.py` is a development variant with User-Agent rotation and exponential backoff
- The production API (`main.py`) uses multi-source prices (AV → Twelve → Yahoo) and real news sentiment — but all sources are labeled `"alphavantage"` and `get_price()` mixes float-cache/tuple-return
- Root-level `layers/` and `config/` no longer exist — all analytics live under `backend/app/layers/` and `backend/app/config/`
- `yahoo_proxy.py` Blueprint is defined but never registered
- `logging_config.py` is never imported and would raise `NameError` (`os` not imported) — wire it up or delete it
- No `sys.exit()` in library code; exceptions propagate
- `load_dotenv()` guarded by `ENVIRONMENT != 'test'`
- Layer 1 installs no cron jobs automatically — run `scripts/install_crontab.sh`
- Fundamental engine requires `numpy`; all other layers stdlib-only
- `frontend/.env.development` still points at the dead `signaliq-l8mi.onrender.com`; `setupProxy.js` and `.env.production` point at `signaliq-api.onrender.com`
- Live production: frontend `signaliq-zeta-ten.vercel.app`, API `signaliq-api.onrender.com` (both verified 200); `/api/prices` + `/api/signals-intel` are **404** on the deployed API
- News pipeline uses TextBlob (not Loughran-McDonald) for live API sentiment
- Rate limiting is in-memory; flask-limiter warns to use Redis in production
- The `feature/market_intelligence` branch is stale; recent work lands directly on `main`

## Estado Actualizado (Agosto 2026)

### ✅ Día 1 Completado - Estabilización
- Archivos stale eliminados
- Imports arreglados (soportan relativo y absoluto)
- Logging estructurado implementado (`logging_config.py` — aún no conectado)
- Datos simulados etiquetados
- README limpiado

### ✅ Día 2 - Entrypoints y Configuración
- Dockerfile actualizado (usa `python -m app.main`) — ✅ verificado
- render.yaml actualizado — ✅ verificado
- Hostname unificado: `signaliq-api.onrender.com` (README, setupProxy, api.py; **`.env.development` aún apunta a `signaliq-l8mi`**)
- Variables de entorno documentadas (`.env.example` con `API_KEY`, `LOG_FORMAT`)

### ✅ Día 3 - Tests y CI
- Tests de smoke reescritos (4) y tests de arquitectura reescritos (4, cheques reales)
- GitHub Actions CI añadido (backend 3.11/3.12, frontend build+test, ruff)
- **⚠️ El CI está en rojo**: 4/8 tests fallan (orchestrator count, `domain` inexistente, `get_ticker_data` indefinido)

### ✅ Día 4 - Endpoints Faltantes y Consistencia API-Frontend
- `/api/prices` y `/api/signals-intel` añadidos a `main.py` (código)
- `config/api.ts` centraliza URLs del frontend
- **⚠️ Regresión**: `API_ENDPOINTS.*` se pegó como string literal (sin `${}`) en `ExpandedRow`, `TickerAnalysis`, `yahoo-finance-service`
- **⚠️ `/api/signals-intel` devuelve 500** (`get_ticker_data` no existe)

### ✅ Día 5 - Rate Limiting y Seguridad
- flask-limiter aplicado (200/día + 50/hora default; 10–30/min por endpoint, in-memory)
- Auth opcional con `API_KEY` (decorador listo, deshabilitado por defecto)

### 🐛 Bugs Críticos Detectados (a corregir)
1. `get_ticker_data` / `get_current_price` no definidos en `main.py`
2. Caché guarda `float` pero `get_price()` retorna tupla → error de unpacking en cache hits
3. `calculate_ndi` trata el dict de `get_price_history()` como lista → `/api/ticker` siempre devuelve datos mínimos
4. Endpoints nuevos no están desplegados (404 en Render) — falta push + redeploy
5. Regresión de template literals en el frontend (3 archivos)
