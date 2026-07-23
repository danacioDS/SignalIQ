# SignalIQ Architecture

## Overview

**SignalIQ** is a market intelligence framework that measures the divergence between what the market is *saying* (news sentiment/narrative) and what the market is *actually doing* (price momentum). It quantifies this gap using the **Narrative Divergence Index (NDI)**:

```
NDI = (sentiment - momentum) × scale_factor
```

Markets are driven by stories as much as by numbers. Stories are created, spread, overheat, and exhaust themselves. Numbers (prices, volatility, volume) are slower and heavier. SignalIQ measures the distance between the hot (narrative) and the cold (prices).

### Key Features
- **NDI formula**: `(sentiment - momentum) × 3.0` (additive divergence with sensitivity scale factor)
- **4 risk regimes (core L4)**: Aligned, Accumulation Divergence, Overheating Divergence, Insufficient Data
- **7 risk regimes (API)**: Extreme Overheating, Overheating, Watching, Neutral, Aligned, Strong Undervalued, Capitulation
- **3 signal states**: Inactive → Watching → Active (requires 2 consecutive threshold breaches)
- **Inverted-U confidence**: Mid-range NDI (0.8–2.2) is most reliable; extreme values are down-weighted
- **LLM Router**: Multi-provider support (Gemini, GLM/ZhipuAI, Groq, MOCK mode)
- **Fundamental overlay**: Adjusts NDI risk/confidence based on valuation, growth, and financial health
- **Stdlib-only core**: Core analytics are pure Python (only Layer 1 and Layer 5 have external deps)
- **Real news sentiment**: Production API integrates TextBlob-based sentiment from live RSS feeds
- **Multi-source prices**: Alpha Vantage → Twelve Data → Yahoo Finance cascading fallback
- **Production API**: Lightweight Flask server with real-time data (no database dependency)

### Tech Stack

| Category | Technologies |
|----------|-------------|
| **Backend (production)** | Python 3.12, Flask 3.0, Flask-CORS 4.0, yfinance 0.2, numpy, requests, feedparser, TextBlob |
| **Backend (full pipeline)** | Python 3.12, Flask 3.0, psycopg2-binary, feedparser, requests |
| **Frontend** | React 19, TypeScript 4.9, Recharts 3.8, Axios 1.17, React Router 7 |
| **Database** | PostgreSQL (public, raw, config, layer4 schemas) — offline pipeline only |
| **AI/LLM** | Google Gemini (gemini-2.5-flash), Groq (llama-3.3-70b-versatile), GLM (glm-4.7-flash), MOCK mode |
| **Data Sources** | Yahoo Finance, Alpha Vantage, Twelve Data, Google News RSS, Yahoo Finance RSS, MarketWatch RSS |
| **Infrastructure** | Docker, Docker Compose, Vercel (frontend), Render (backend) |

### Core Philosophy

When narrative runs ahead of price action, SignalIQ flags it as exhaustion, distribution, or severe divergence — not a prediction, but a systematic measurement of risk conditions. Signals classify into 4 risk regimes and 3 signal states based on the persistence and magnitude of the divergence.

---

## Architecture Diagram

```
                     ┌──────────────────────────────────────────────────┐
                     │                   Frontend                      │
                     │          React 19 + TypeScript UI               │
                     │   Dashboard · Economic · Data · Tech · About    │
                     └──────────────────────┬──────────────────────────┘
                                            │ HTTP / JSON
                     ┌──────────────────────▼──────────────────────────┐
                     │          Flask API (port 10000)                 │
                     │      400 lines · 5 endpoints                   │
                     │      Multi-source: AV + Twelve + Yahoo         │
                     │      Real news sentiment (TextBlob)            │
                     │      NDI × 3.0 scale factor                   │
                     │      7-regime classification                   │
                     │      Thread-safe cache · CORS (6 origins)     │
                     └──────────────┬───────────────┬─────────────────┘
                                    │               │
                   ┌────────────────▼───┐   ┌───────▼────────────────┐
                   │  Price APIs        │   │  News RSS Feeds        │
                   │  Alpha Vantage     │   │  Google News           │
                   │  Twelve Data       │   │  Yahoo Finance         │
                   │  Yahoo Finance     │   │  MarketWatch           │
                   │  Hardcoded fallback│   │  TextBlob sentiment    │
                   └────────────────────┘   └────────────────────────┘

               ┌─────────────────────────────────────────────────────┐
               │              Core Pipeline (Offline)                │
               │                                                     │
               │  ┌───────────┐  ┌───────────┐  ┌───────────┐      │
               │  │ Layer 5   │  │ Layer 4   │  │ Layer 3   │      │
               │  │ Fund.     │  │ Signals   │  │ NLP       │      │
               │  │ Scoring   │  │ NDI Calc  │  │ LM Lexicon│      │
               │  │ Sector    │  │ Regime    │  │ Momentum  │      │
               │  │ Benchmarks│  │ Streak    │  │ Entity    │      │
               │  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘      │
               │        │              │              │              │
               │        └──────────────┼──────────────┘              │
               │                       │                             │
               │        ┌──────────────▼──────────────┐             │
               │        │       Layer 2 - Database    │             │
               │        │    PostgreSQL (4 schemas)    │             │
               │        │  10 tables · 2 views         │             │
               │        │  13 functions · 6 triggers   │             │
               │        │  Used by offline pipeline    │             │
               │        └──────────────┬──────────────┘             │
               │                       │                             │
               │        ┌──────────────▼──────────────┐             │
               │        │       Layer 1 - Ingestion   │             │
               │        │  Yahoo Finance (5 assets)   │             │
               │        │  6 RSS Feeds (news)         │             │
               │        │  O_EXCL locks · Cron        │             │
               │        └─────────────────────────────┘             │
               └─────────────────────────────────────────────────────┘
```

Data flows in two paths:

**Core pipeline (offline/batch):** fetch → normalize → write (Layer 1) → store (Layer 2) → analyze (Layer 3) → generate signals (Layer 4) → fundamental overlay (Layer 5). Layer 4 exposes a functional API (`process_asset`, `process_batch`) that wires together measurement, persistence, and classification sublayers.

**Live API path (production):** `main.py` → price APIs (Alpha Vantage → Twelve Data → Yahoo Finance → fallback) → real news (TextBlob sentiment from RSS) → NDI calculation `(sentiment - momentum) × 3` → 7-regime classification → JSON response. The production API operates independently of the database pipeline.

**AI enhancement (offline):** Layer 4 signals → `LLMRouter` (Gemini/GLM/Groq, configured via `PRIMARY_LLM` env var) → AI-powered analysis. Not connected to the production API.

---

## Project Structure

```
repo root/
├── architecture.md                         # This file — system map
├── README.md                               # Project readme
├── report.md                               # Analysis & audit report
├── pitch.md                                # Commercial pitch
├── workflow.md                             # Development methodology
├── signals_demo.csv                        # Sample signal output
├── .env.example                            # Environment variable template
├── .env.template                           # Alternate env template
├── .python-version                         # Python 3.12.5
├── .gitignore                              # Git ignore rules
├── pytest.ini                              # Pytest config (smoke/integration/slow)
├── requirements_layer1.txt                 # Layer 1 Python deps
├── requirements_test.txt                   # Test deps (pytest, pytest-cov)
├── docker-compose.yml                      # Docker Compose (API + Redis + Worker)
├── Dockerfile                              # Root Docker image
│
├── backend/                                # Flask backend API server
│   ├── Dockerfile                          # Backend Docker image
│   ├── requirements.txt                    # Backend dependencies
│   ├── run.sh                              # Dev startup script
│   ├── fix_analyze.py                      # Analysis fix utility
│   ├── render.yaml                         # Render deployment config
│   ├── preload_cache.py                    # Cache preloading script
│   ├── check_cache.py                      # Cache inspection utility
│   ├── static/                             # Built frontend assets
│   └── app/
│       ├── main.py                         # 400-line production API (multi-source, real news)
│       ├── api.py                          # 257-line variant with User-Agent rotation + retries
│       ├── news_pipeline.py                # 104-line real news sentiment (TextBlob + RSS)
│       ├── auth.py                         # [UNUSED by production] API key decorators
│       ├── db.py                           # [UNUSED by production] ThreadedConnectionPool
│       ├── llm_service.py                  # [UNUSED by production] Groq-based LLM service
│       ├── entity_linking.py               # [UNUSED by production] Company→ticker resolution
│       ├── event_extractor.py              # [UNUSED by production] News event extraction
│       ├── narrative_builder.py            # [UNUSED by production] Narrative construction
│       ├── news_fetcher.py                 # [UNUSED by production] NewsAPI integration
│       ├── market_intelligence.py          # [UNUSED by production] Blueprint (defined, not registered)
│       ├── extract_events_job.py           # [UNUSED by production] CLI event extraction
│       ├── ingest_news_job.py              # [UNUSED by production] CLI news ingestion
│       ├── store_intel_job.py              # [UNUSED by production] Intelligence storage
│       ├── classification/
│       │   └── event_classifier.py         # [UNUSED by production] 9 event types classifier
│       └── scoring/
│           └── signal_score.py             # [UNUSED by production] Weighted scoring
│
├── ingestion/                              # Layer 1 — Data Ingestion
│   ├── __init__.py
│   ├── http_client.py                      # Shared HTTP with retry
│   ├── collect_prices.py                   # Yahoo Finance OHLCV (5 assets)
│   ├── collect_news.py                     # RSS feed collection (6 sources)
│   ├── writer.py                           # PostgreSQL atomic writes
│   └── orchestrator.py                     # O_EXCL locks, coordination
│
├── layers/                                 # Layers 3, 4 & 5 — NLP, Signal, Fundamental
│   ├── __init__.py                         # Exports: score_text, net_sentiment,
│   │                                       #   run_pipeline, run_batch_pipeline
│   ├── lm_lexicon.py                       # Loughran-McDonald (558 words, 6 categories)
│   ├── system_config.py                    # SignalIQConfig singleton
│   ├── llm_router.py                       # LLMRouter (Gemini, GLM, Groq, MOCK)
│   ├── integration.py                      # L1→L3→L4 pipeline entry
│   ├── layer3_config.py                    # L3 frozen config dataclass
│   ├── layer3_entity.py                    # L3 entity resolution (two-phase)
│   ├── layer3_sentiment.py                 # L3 LM lexicon + rolling z-score
│   ├── layer3_momentum.py                  # L3 daily returns + rolling z-score
│   ├── layer3_orchestrator.py              # L3 pipeline, TimeAligner, finalize_day()
│   ├── layer4_measurement.py               # L4 validity gate, NDI, 5d return
│   ├── layer4_persistence.py               # L4 streak tracking, stale-gap, state
│   ├── layer4_classification.py            # L4 confidence, price pressure, risk
│   ├── layer4_orchestrator.py              # L4 9-step pipeline + Layer4Orchestrator class
│   └── fundamental/                        # Layer 5 — Fundamental Analysis
│       ├── __init__.py
│       ├── fundamental_engine.py           # Main engine, caching, NDI adjustment
│       ├── metrics_calculator.py           # Valuation, growth, profitability
│       └── score_aggregator.py             # Sector-benchmarked scoring (0-100)
│
├── frontend/                               # Layer 6 — React TypeScript UI
│   ├── package.json                        # React 19, Recharts 3.8, Axios, React Router 7
│   ├── tsconfig.json
│   ├── .env.production                     # API URL: signaliq-api.onrender.com
│   ├── .env.development                    # API URL: https://signaliq-l8mi.onrender.com
│   ├── public/
│   └── src/
│       ├── App.tsx                         # Shell with top nav + 5 routes
│       ├── index.tsx
│       ├── components/
│       │   ├── styles.ts                   # Dark theme constants (C object)
│       │   ├── NDIGauge.tsx                # NDI gauge visualization
│       │   ├── NDIThermometer.tsx          # NDI thermometer visualization
│       │   ├── NDIVelocimeter.tsx          # SVG semi-circular gauge
│       │   ├── NarrativePanel.tsx          # Narrative analysis panel
│       │   ├── TickerFocusStrip.tsx        # Ticker focus/detail strip
│       │   ├── ScanTable.tsx               # Ticker scan results
│       │   ├── TickerAnalysis.tsx          # Per-ticker deep analysis
│       │   ├── ExpandedRow.tsx             # Expanded signal detail
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
│       │   └── ndiRegimes.ts              # NDI regime constants
│       ├── services/
│       │   └── yahoo-finance-service.ts    # Yahoo finance service
│       ├── utils/
│       │   ├── regimeHelpers.ts            # Regime classification helpers
│       │   └── velocimeterUtils.ts         # Velocimeter SVG utilities
│       └── pages/
│           ├── Dashboard.tsx               # 566-line signals dashboard (primary page)
│           ├── EconomicFoundation.tsx      # Economic foundation page
│           ├── Data.tsx                    # Data sources page
│           ├── TechStack.tsx               # Tech stack page
│           ├── About.tsx                   # About page
│           ├── Docs.tsx                    # Documentation page
│           ├── Intelligence.tsx            # Market Intelligence page
│           ├── ScanTable.tsx               # Scan results page
│           ├── ExpandedRow.tsx             # Expanded signal detail page
│           └── Dashboard.tsx.backup_*      # Backup files (2)
│
├── sql/                                    # Layer 2 — SQL Migrations (6 files)
│   ├── 001_create_layer2_schema.sql        # Core schema (public.prices, headlines, ndi_signals)
│   ├── 002_fix_schema.sql                  # raw/config/layer4 schemas, wrapper functions, views
│   ├── 003_create_signal_tables.sql        # Signal classification tables
│   ├── master_build.sql                    # Transactional build wrapper
│   ├── rollback.sql                        # Complete teardown
│   └── test_queries.sql                    # 24 validation queries
│
├── config/                                 # Configuration
│   └── thresholds.py                       # Centralized thresholds
│
├── scripts/                                # Operations & Utilities (12 scripts)
│   ├── demo.py                             # End-to-end synthetic demo (stdlib only)
│   ├── simple_ndi.py                       # Simplified NDI signal generator
│   ├── backtest_engine.py                  # NDI backtesting engine (pandas/numpy)
│   ├── backtest_improved.py                # Enhanced backtesting
│   ├── run_backtest_real.py                # Production backtest runner
│   ├── run_backtest_real_fixed.py          # Fixed backtest runner
│   ├── run_layer3_daily.py                # Daily Layer 3 run
│   ├── run_layer3_historical.py           # Historical Layer 3 run
│   ├── run_layer3_historical_fixed.py     # Fixed historical runner
│   ├── run_layer3_pipeline.py             # Layer 3 pipeline
│   ├── generate_signals_direct.py         # Direct signal generation
│   ├── news_pipeline.py                   # News pipeline script
│   ├── install_crontab.sh                 # Install cron jobs
│   ├── rotate_logs.sh                     # Log rotation
│   └── verify_refactor.py                 # Structural verification
│
├── web/                                    # Standalone HTML dashboards
│   ├── index.html                          # Dark-themed institutional dashboard
│   ├── automatico.html                     # Automated dashboard
│   └── test.html                           # Simple API test UI
│
├── tests/                                  # Official test suite
│   └── pytest/                             # Single source of truth
│       ├── test_smoke.py                   # 4 smoke tests (Layer4, Config, Layer1, API)
│       ├── test_architecture.py            # 4 architecture invariants (1 stub)
│       ├── test_db_contract.py             # DB migration/schema tests (integration)
│       └── test_integration.py             # Full system integration test (integration)
│
└── logs/                                   # Runtime logs (.gitignore)
    └── app.log
```

---

## Layer Details

### Layer 1 — Data Ingestion (`ingestion/`)

**5 modules.**

| Module | File | Responsibility |
|--------|------|---------------|
| HTTP Client | `http_client.py` | Shared `fetch_with_retry()` with configurable retry policy (timeout, connection errors, 429, 5xx) |
| Prices | `collect_prices.py` | Yahoo Finance OHLCV for NVDA, AAPL, MSFT, SPX, BTC-USD. Includes `normalize_price_response()` |
| News | `collect_news.py` | 6 RSS feeds (Reuters, AP, Yahoo General, Yahoo Ticker, CNBC, MarketWatch). NFKC normalization, SHA256 dedup |
| Writer | `writer.py` | PostgreSQL atomic writes via `raw.insert_price_record()` and `raw.insert_headline_record()`. Handles numpy type conversion, `UniqueViolation` rollback |
| Orchestrator | `orchestrator.py` | O_EXCL atomic file locks, pipe-delimited logging, cron entry point |

**Key design decisions:**
- Prices: transactional (all-or-nothing)
- News: per-row idempotent (rollback on duplicate)
- Zero `sys.exit()` in library code — exceptions propagate to callers
- Cron: prices daily @20:05, news 3× daily (06, 12, 18)

### Layer 2 — PostgreSQL Persistence (`sql/`)

**6 migration files**, 24 validation queries.

| Migration | Purpose |
|-----------|---------|
| `001_create_layer2_schema.sql` | Core tables in `public` schema: `prices`, `headlines`, `ndi_signals` |
| `002_fix_schema.sql` | Creates `raw`, `config`, `layer4` schemas; wrapper functions; views; `config.news_sources` |
| `003_create_signal_tables.sql` | Signal classification extension tables |
| `master_build.sql` | Transactional build wrapper (all-or-nothing migration) |
| `rollback.sql` | Complete teardown of all schemas and tables |
| `test_queries.sql` | 24 validation queries verifying schema completeness |

**Stats:** 10 tables, 2 views, 13 functions, 6 triggers, 4 schemas, 4 roles

**Key constraints:**
- `UNIQUE(ticker, price_date, source)` on prices — upsert semantics
- `UNIQUE(sha256_hash)` on headlines — content deduplication
- `UNIQUE(ticker, signal_date)` on ndi_signals — one signal per ticker per day

**Note:** Layer 2 serves the offline batch pipeline only. The production API (`main.py`) does not connect to the database.

### Layer 3 — NLP Intelligence (`layers/`)

**6 modules**, pure Python stdlib.

| Module | Responsibility |
|--------|---------------|
| `lm_lexicon.py` | Loughran-McDonald financial sentiment lexicon. 558 words across 6 categories (positive, negative, uncertainty, litigious, constraining, superfluous). Exports `score_text()` and `net_sentiment()` |
| `layer3_config.py` | Frozen dataclass with lookback window (20 days), min valid days (10), cutoff hour (4 PM ET) |
| `layer3_entity.py` | Two-phase entity resolution: URL parameter match → alias regex matching against 5 tickers |
| `layer3_sentiment.py` | LM lexicon scoring with legacy word list fallback. Rolling 20-day z-scores via deque-based history |
| `layer3_momentum.py` | Daily return calculation. Two-phase commit: pending returns until `commit_pending_returns()` prevents look-ahead bias |
| `layer3_orchestrator.py` | Coordinates entity, sentiment, momentum. `TimeAligner` for UTC→ET conversion. `finalize_day()` processes all data for a given date |

### Layer 4 — Signal Generation (`layers/`)

**5 modules**, 12-field output schema.

| Module | Responsibility |
|--------|---------------|
| `layer4_measurement.py` | NDI = `sentiment_zscore - momentum_zscore`. Validity gates check input completeness. 5-day return calculation. No clamping. |
| `layer4_persistence.py` | `PersistenceTracker` manages consecutive-day threshold breaches. JSON file persistence with stale-gap detection (3-day max). Classifies into 4 regimes |
| `layer4_classification.py` | Inverted-U confidence model (NDI 0.8–2.2 = max reliability). Price pressure classification. Risk escalation (only OVERHEATING_DIVERGENCE produces non-NORMAL risk). Attention text generation |
| `layer4_orchestrator.py` | 9-step pipeline: validate → calculate NDI → compute 5d return → track persistence → classify regime → calculate confidence → boost by streak → determine risk → generate attention. Exports: `process_asset()`, `process_batch()`, `OUTPUT_FIELDS`. Also contains `Layer4Orchestrator` class with LLM integration. |
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

**3 Signal States:**
- **Inactive**: No threshold breach
- **Watching**: 1 consecutive breach
- **Active**: 2+ consecutive breaches

**Confidence model:** Inverted-U. NDI between 0.8 and 2.2 receives highest confidence. Below 0.8 or above 2.2, confidence decreases quadratically.

### Layer 5 — Fundamental Analysis (`layers/fundamental/`)

**3 modules**, depends on numpy.

| Module | Responsibility |
|--------|---------------|
| `fundamental_engine.py` | Main engine: processes metrics, caches results, adjusts NDI risk/confidence |
| `metrics_calculator.py` | Computes valuation ratios (P/E, P/B, P/S), growth (EPS/revenue CAGR), profitability (margins, ROE, ROA), cash flow (FCF yield, dividend yield), financial health (D/E, current ratio) |
| `score_aggregator.py` | Sector-benchmarked 0–100 scoring against Technology, Financials, Healthcare, Consumer, Energy, Industrial. Quality rating: Excellent / Good / Fair / Poor / Distressed |

**Integration:** Fundamental score adjusts NDI risk_level and confidence via `process_signal()`.

### LLM Router (`layers/llm_router.py`)

**Singleton pattern** — supports 4 providers with fallback chain:

```
PRIMARY_LLM (env var, default: "mock") → FALLBACK_LLM (env var, default: "mock") → MOCK mode
```

| Provider | Model | Config |
|----------|-------|--------|
| Google Gemini | gemini-2.5-flash, gemini-1.5-flash | `GEMINI_API_KEY` |
| Groq | llama-3.3-70b-versatile | `GROQ_API_KEY` |
| GLM (ZhipuAI) | glm-4.7-flash | `GLM_API_KEY` |
| MOCK | — | No key required |

**Integration:** `Layer4Orchestrator.process_signal()` calls `llm_router.analyze_signal()` for AI-powered narrative analysis. **Not connected to the production API.**

**Note:** `system_config.py` defaults to `PRIMARY_LLM="glm"`, `FALLBACK_LLM="groq"` — inconsistent with `llm_router.py` defaults of `"mock"` for both.

### Flask API — Production (`backend/app/main.py`)

**400-line Flask application** — multi-source price data with real news sentiment. 5 endpoints, inline NDI calculation with scale factor, 7-regime classification.

#### Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API root with version (6.2), status, mode, available endpoints |
| `/health` | GET | Health check with cache TTL config and timestamp |
| `/api/ticker/<ticker>` | GET | Deep ticker analysis: NDI, regime, price history (20 points), real headlines, confidence |
| `/api/signals-live` | GET | Batch signals for multiple tickers (`?tickers=AAPL,MSFT,...`) |
| `/api/tickers` | GET | Default ticker list (10 tickers) |

**Price sources (cascading fallback):**
1. Alpha Vantage — `GLOBAL_QUOTE` endpoint (requires `ALPHA_VANTAGE_API_KEY`)
2. Twelve Data — `/price` endpoint (requires `TWELVE_DATA_API_KEY`)
3. Yahoo Finance — `yf.Ticker.history(period="2d")`
4. Hardcoded fallback — `FALLBACK_PRICES` dict

**NDI Calculation (Live API):**

```python
def calculate_ndi(ticker):
    price = get_price(ticker)          # Cascading: AV → Twelve → Yahoo → fallback
    history = get_price_history(ticker) # Cascading: AV → Yahoo → simulated
    news_data = process_news_for_ticker(ticker)  # Real RSS → TextBlob sentiment
    sentiment = news_data['sentiment']  # Average TextBlob polarity [-1, 1]
    momentum = (history[-1] - history[-10]) / history[-10]  # 10-day return
    ndi = (sentiment - momentum) * 3.0  # Scale factor for sensitivity
    ndi = clamp(ndi, -3.0, 3.0)        # Bounded output
```

This differs from the core L4 formula (`sentiment_zscore - momentum_zscore` using rolling 20-day z-scores from the offline pipeline). The API uses TextBlob sentiment × scale factor vs momentum period return — a known architectural inconsistency.

**News Pipeline (`news_pipeline.py`):**
- Google News RSS (search-based per ticker, 2 queries)
- Yahoo Finance RSS
- MarketWatch RSS
- TextBlob sentiment analysis (polarity [-1, 1])
- Deduplication via `seen` set
- Fallback: alternative search terms when no results

**Caching:**
- Thread-safe dict cache with `threading.Lock`
- Configurable TTL per type: price=300s, history=600s, ticker=300s, signals=60s
- Cache keys: `price_{ticker}`, `history_{ticker}_{days}`, `ticker_{ticker}`

**CORS:** 6 explicitly allowed origins:
```
http://localhost:3000, http://127.0.0.1:3000,
https://signaliq-zeta-ten.vercel.app,
https://signaliq-zeta.vercel.app,
https://signaliq-api.onrender.com,
https://signaliq-l8mi.onrender.com
```

**No rate limiting.** Flask-Limiter is imported in `config/thresholds.py` but never applied.

**No authentication.** All endpoints publicly accessible.

**Price history:** Always returns 20 data points — real data from APIs when available, simulated random walk as fallback.

**JSON structured logging:** Python `logging` with INFO level.

### News Pipeline (`backend/app/news_pipeline.py`)

**104-line standalone module** — provides real news sentiment to the production API.

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

**Sentiment:** TextBlob polarity (returns float in [-1, 1]). No Loughran-McDonald (that's offline pipeline only).

### Flask API — Alternative (`backend/app/api.py`)

**257-line alternative entry point** — nearly identical to `main.py` but with:
- Exponential backoff retry for yfinance requests (User-Agent rotation, up to 5 retries)
- More robust error handling with descriptive messages
- Uses `requests.Session` with browser-like User-Agent
- Used as a development/debug variant

### Flask API — Unused Modules (13 of 16)

| Module | Lines | Purpose | Status |
|--------|-------|---------|--------|
| `market_intelligence.py` | 229 | Blueprint with `/api/ticker/analysis` + `/api/test` | Defined, never registered |
| `db.py` | ~80 | ThreadedConnectionPool (min=1, max=10) | Unused by production |
| `auth.py` | ~40 | `require_api_key` / `require_api_key_optional` decorators | Unused by production |
| `llm_service.py` | ~60 | Groq-based LLM service (Qwen/Llama) | Unused by production |
| `entity_linking.py` | ~50 | Company→ticker resolution | Unused by production |
| `event_extractor.py` | ~80 | News event extraction | Unused by production |
| `narrative_builder.py` | ~60 | Narrative construction | Unused by production |
| `news_fetcher.py` | ~70 | NewsAPI integration | Unused by production |
| `classification/event_classifier.py` | ~100 | 9 event types classification | Unused by production |
| `scoring/signal_score.py` | ~60 | Weighted scoring (v1.0) | Unused by production |
| `extract_events_job.py` | ~30 | CLI entry point | Unused by production |
| `ingest_news_job.py` | ~30 | CLI entry point | Unused by production |
| `store_intel_job.py` | ~30 | CLI entry point | Unused by production |

### Layer 6 — Frontend (`frontend/`)

**React 19 + TypeScript** app with 5 routes, 16 components, 10 pages.

#### Routes

| Route | Page | Description |
|-------|------|-------------|
| `/` | Dashboard | Main signals dashboard (566 lines) |
| `/economic` | EconomicFoundation | Theory cards |
| `/data` | Data | Data sources |
| `/tech` | TechStack | Technology breakdown |
| `/about` | About | Author bio |

#### Key Components

| Component | Lines | Purpose |
|-----------|-------|---------|
| `App.tsx` | 87 | Shell with sticky top nav bar |
| `pages/Dashboard.tsx` | 566 | Main dashboard: signals, NDI gauge, price chart (Recharts), NDIFrameworkTable (7 regimes), NarrativePanel, TickerFocusStrip |
| `hooks/useSignalAnalysis.ts` | 165 | Transforms signal data into regime analysis. 7 regimes with explanatory text. Inverted-U confidence calculation. |
| `NDIVelocimeter.tsx` | — | SVG semi-circular gauge |
| `NDIGauge.tsx` | — | NDI gauge visualization |
| `NDIThermometer.tsx` | — | NDI thermometer visualization |
| `NarrativePanel.tsx` | — | Narrative analysis display |
| `TickerFocusStrip.tsx` | — | Ticker selection/detail strip |

#### 7 Regimes (Frontend — `useSignalAnalysis.ts`)

| Regime Key | Label | NDI Range | Color |
|------------|-------|-----------|-------|
| EXTREME_OVERHEATING | Extreme Overheating | NDI > 2.0 | #ef4444 (red) |
| OVERHEATING | Overheating | 1.5 < NDI ≤ 2.0 | #f97316 (orange) |
| WATCHING | Watching | 0.5 < NDI ≤ 1.5 | #eab308 (yellow) |
| STABLE | Stable | -0.5 < NDI ≤ 0.5 | #22c55e (green) |
| ALIGNED | Aligned | -1.5 < NDI ≤ -0.5 | #22c55e (green) |
| STRONG_UNDERVALUED | Strong Undervalued | -2.0 < NDI ≤ -1.5 | #3b82f6 (blue) |
| EXTREME_UNDERVALUED | Extreme Undervalued | NDI ≤ -2.0 | #1d4ed8 (dark blue) |

#### Confidence Model (Frontend)

```typescript
// Inverted-U: peak at absNdi 0.8
if (absNdi <= 0.8)  confidence = 50 + (absNdi / 0.8) * 40;   // 50 → 90
if (absNdi <= 2.0)  confidence = 90 - ((absNdi - 0.8) / 1.2) * 40;  // 90 → 50
else                confidence = 50;  // Flat at extreme NDI
```

**Styling:** Shared `C` object from `styles.ts` — dark theme with 15+ color tokens (bg #0f172a, card #1f2937, accent #6c63ff). All components use inline style objects. Tailwind config and PostCSS config exist but are unused.

**Data fetching:** Axios to `REACT_APP_API_URL` (production: `signaliq-api.onrender.com`). Falls back to static data when backend unreachable. 5-minute polling with error recovery.

**Setup proxy:** `frontend/src/setupProxy.js` proxies `/api` to `signaliq-l8mi.onrender.com` in development.

**Standalone HTML dashboards** available in `web/`: `index.html` (dark institutional), `automatico.html` (automated), `test.html` (API test).

---

## Configuration

### Thresholds (`config/thresholds.py`)

Centralized constants used by Layer 4:

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

**Note:** Rate limit constants are defined but **never applied** — no rate-limiting middleware is configured in the production API.

### Environment Variables

| Variable | Purpose | Used By |
|----------|---------|---------|
| `PORT` | Server port (default: 10000) | Production API |
| `PRIMARY_LLM` | LLM provider (gemini/glm/groq/mock) | Offline pipeline |
| `FALLBACK_LLM` | Fallback provider | Offline pipeline |
| `GROQ_API_KEY` | Groq API key | Offline pipeline |
| `GOOGLE_API_KEY` / `GEMINI_API_KEY` | Gemini API key | Offline pipeline |
| `GLM_API_KEY` | ZhipuAI GLM API key | Offline pipeline |
| `FINNHUB_API_KEY` | Finnhub.io API key | Deprecated |
| `NEWS_API_KEY` | NewsAPI key | Offline pipeline |
| `DATABASE_URL` | PostgreSQL connection string | Offline pipeline |
| `ALPHA_VANTAGE_API_KEY` | Alpha Vantage API key | Production API |
| `TWELVE_DATA_API_KEY` | Twelve Data API key | Production API |
| `CORS_ORIGINS` | CORS allowed origins | Not used (origins are hardcoded) |

**Note:** `load_dotenv()` is guarded by `ENVIRONMENT != 'test'` to prevent side effects during test imports.

---

## Testing

### Test Suite (pytest — single source of truth)

| Test File | Type | Tests | Dependencies | Status |
|-----------|------|-------|-------------|--------|
| `test_smoke.py` | Smoke | 4 | None | Pass |
| `test_architecture.py` | Architecture | 4 (1 stub) | None | Pass (stub: test_no_circular_imports) |
| `test_db_contract.py` | Integration | — | PostgreSQL | Skip if no DB |
| `test_integration.py` | Integration | — | Flask API | Skip if no API |

### Run Commands

```bash
# Smoke + architecture tests (no external deps)
pytest tests/pytest/ -m "not integration" -v

# Integration tests (requires DB/API)
pytest tests/pytest/ -m integration -v

# All tests
pytest tests/pytest/ -v
```

### Architecture Invariants (enforced by `test_architecture.py`)

1. **Single orchestrator** — Only one `Layer4Orchestrator` class defined
2. **No circular imports** — `layer4_measurement.py` does not import from `layers/__init__.py` (**stub — currently `pass`**)
3. **NDI formula consistency** — All NDI functions use `sentiment_zscore - momentum_zscore`
4. **Zero sys.exit** — No `sys.exit()` in library code (only in `__main__` blocks)

### Code Quality

- **No linter configured** — No ruff, black, flake8, or mypy (despite `mypy.ini` existing)
- **Minimal type hints** — Some modules have type annotations, but most lack them
- **Mixed language** — Spanish and English used inconsistently; API response fields and comments mix both

---

## Deployment

### Docker

```bash
# Build
docker build -t signaliq-api .

# Run with Docker Compose
docker-compose up
```

- **Port:** 10000 (container) → 5000 (host)
- **Base image:** python:3.11-slim
- **Entrypoint:** `python -m backend.app.main`

### Production

| Service | Platform | URL | Auto-deploy |
|---------|----------|-----|-------------|
| Frontend | Vercel | https://signaliq-zeta-ten.vercel.app | From `main` branch |
| Backend | Render | https://signaliq-l8mi.onrender.com | From `main` branch |

### Cron Jobs

| Schedule | Command | Description |
|----------|---------|-------------|
| `5 20 * * *` | `python -m ingestion.orchestrator --type prices` | Daily price collection |
| `0 6,12,18 * * *` | `python -m ingestion.orchestrator --type news` | News collection (3× daily) |
| Daily | `scripts/rotate_logs.sh` | Log rotation, 90-day retention |

### Installation

```bash
# Install cron jobs
./scripts/install_crontab.sh

# Or run manually
python -m ingestion.orchestrator --type both
python -m ingestion.orchestrator --type prices --dry-run
python -m ingestion.orchestrator --type news --source reuters --dry-run
```

---

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **6-layer architecture** | Clear separation of concerns; each layer is independently testable and replaceable |
| **Stdlib-only core** | Layers 3–4 have zero external dependencies — maximizes stability and portability |
| **Two-phase commit for momentum** | Prevents look-ahead bias in z-score calculations |
| **Inverted-U confidence** | Down-weights extreme NDI values as potential noise; mid-range most reliable |
| **O_EXCL locks** | Prevents concurrent ingestion runs via filesystem-level locking |
| **Idempotent DDL** | `IF NOT EXISTS` / `CREATE OR REPLACE` / `ON CONFLICT DO NOTHING` for safe re-execution |
| **LLM Router singleton** | Single point of configuration for all LLM providers; easy to add new providers |
| **Production API simplification** | yfinance-only + real news removes database operational burden; reduces deployment complexity |
| **Multi-source price cascade** | Alpha Vantage → Twelve Data → Yahoo Finance → fallback ensures high availability |
| **NDI scale factor** | Factor of 3.0 amplifies small divergences for better signal sensitivity |
| **Environment-driven config** | `os.environ.get()` with sensible defaults for production API |

---

## Status Summary

### Completed
- All 6 layers implemented and integrated
- 22+ blockers resolved across 6+ refactoring rounds
- 8 tests pass with no external dependencies
- Production API with real news sentiment (TextBlob) and multi-source prices
- Frontend refactored from monolith to focused components + pages
- ~35% dead code removed, directory structure cleaned
- Architecture invariants enforced by tests
- Centralized thresholds in `config/thresholds.py`
- 5-route React dashboard with NDI visualization
- Cross-origin CORS support for Vercel deployment
- Thread-safe caching with configurable TTL

### Known Issues
- Triplicate NDI formula in live API path vs core L4 vs frontend
- 7 regimes (API) vs 4 regimes (core L4) — different thresholds and semantics
- API keys in git history (need `git filter-repo`)
- ~13 of 16 backend modules are dead code (not used by production entry point)
- Duplicate API entry points (`main.py` vs `api.py`)
- `print()` in production modules (`news_pipeline.py` uses print instead of logging)
- No authentication on any API endpoint
- No rate limiting despite defined constants
- ~120 hardcoded values remain
- No CI/CD pipeline
- Zero frontend tests
- Minimal type hints or linter
- Mixed language (ES/EN)
- Architecture test `test_no_circular_imports` is a stub
- NDI scale factor instability (changed 4 times in recent commits)
- Backup files tracked in git

### Future Directions
- Architectural direction decision: database-backed vs pure yfinance vs hybrid
- Remove dead code or re-integrate unused modules
- NDI formula unification across all layers
- Regime model reconciliation (core L4 ↔ API ↔ frontend)
- CI/CD with GitHub Actions
- Frontend tests (Jest + React Testing Library)
- Type hints + linter (ruff)
- API authentication + rate limiting
- Redis caching layer for yfinance data
- Unit tests for production API logic
- Freeze NDI scale factor with automated validation

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
psql $DATABASE_URL -f sql/002_fix_schema.sql
psql $DATABASE_URL -f sql/test_queries.sql

# Test suite
pytest tests/pytest/ -m "not integration" -v
pytest tests/pytest/ -m integration -v
pytest tests/pytest/ -v

# Backend API server (production)
python backend/app/main.py

# Backend API server (with retries)
python backend/app/api.py

# Frontend
cd frontend && npm start

# Frontend build
cd frontend && npm run build

# Frontend deploy
cd frontend && vercel --prod --force

# End-to-end demo
python scripts/demo.py

# Backtesting
python scripts/backtest_engine.py
python scripts/run_backtest_real.py

# Simplified NDI generation
python scripts/simple_ndi.py

# News pipeline test
python backend/app/news_pipeline.py NVDA

# Verify project structure
python scripts/verify_refactor.py

# Install cron jobs
./scripts/install_crontab.sh

# Docker
docker build -t signaliq-api .
docker-compose up
```

---

## Notes

- `config/thresholds.py` is the single source of truth for all production thresholds
- `layers/lm_lexicon.py` is the canonical Loughran-McDonald lexicon (558 words, 6 categories)
- `layers/__init__.py` exports `score_text`, `net_sentiment`, `run_pipeline`, `run_batch_pipeline`
- `layers/llm_router.py` provides the `LLMRouter` singleton — set `PRIMARY_LLM` in `.env`
- `calculate_narrative_divergence_index()` is the canonical NDI function in `layer4_measurement.py`
- The live API `calculate_ndi()` in `main.py` uses `(sentiment - momentum) × 3` with TextBlob — different from core L4's rolling z-score approach
- `classify_regime()` in `main.py` supports 7 regimes; core L4 uses 4 academic regimes
- The production API (`main.py`) uses multi-source prices (AV → Twelve → Yahoo) and real news sentiment
- `api.py` is a development variant with User-Agent rotation and exponential backoff retries
- ~13 of 16 `backend/app/` modules are unused by the production entry point
- The Market Intelligence Blueprint (`market_intelligence.py`) is defined but never registered
- No `sys.exit()` in library code — exceptions propagate for graceful handling
- `load_dotenv()` guarded by `ENVIRONMENT != 'test'` — no import-time side effects
- Layer 1 installs no cron jobs automatically — run `scripts/install_crontab.sh`
- The frontend is a Create React App — run `npm install && npm start` from `frontend/`
- Architecture invariants enforced by `test_architecture.py` (4 tests, 1 stub)
- Fundamental engine requires `numpy`; all other layers remain stdlib-only
- `docker-compose.yml` reads API keys from `.env` via `${VAR:-}` references
- Production frontend URL: `https://signaliq-zeta-ten.vercel.app`
- Production API URL: `https://signaliq-l8mi.onrender.com`
- News pipeline uses TextBlob (not Loughran-McDonald) for live API sentiment
