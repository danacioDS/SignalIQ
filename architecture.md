# SignalIQ Architecture

## Overview

**SignalIQ** is a market intelligence framework that measures the divergence between what the market is *saying* (news sentiment/narrative) and what the market is *actually doing* (price momentum). It quantifies this gap using the **Narrative Divergence Index (NDI)**:

```
NDI = sentiment_zscore - momentum_zscore
```

Markets are driven by stories as much as by numbers. Stories are created, spread, overheat, and exhaust themselves. Numbers (prices, volatility, volume) are slower and heavier. SignalIQ measures the distance between the hot (narrative) and the cold (prices).

### Key Features
- **NDI formula**: `sentiment_zscore - momentum_zscore` (additive divergence in standard deviation units)
- **4 risk regimes (core)**: Aligned, Accumulation Divergence, Overheating Divergence, Insufficient Data
- **7 risk regimes (API)**: Extreme Overheating, Overheating, Watching, Stable, Aligned, (negative Aligned), Strong Undervalued
- **3 signal states**: Inactive → Watching → Active (requires 2 consecutive threshold breaches)
- **Inverted-U confidence**: Mid-range NDI (0.8–2.2) is most reliable; extreme values are down-weighted
- **LLM Router**: Multi-provider support (Gemini, GLM/ZhipuAI, Groq, MOCK mode)
- **Fundamental overlay**: Adjusts NDI risk/confidence based on valuation, growth, and financial health
- **Stdlib-only core**: Core analytics are pure Python (only Layer 1 and Layer 5 have external deps)
- **Market Intelligence**: Deep ticker analysis with narrative breakdown, exhaustion detection, and ranking

### Tech Stack

| Category | Technologies |
|----------|-------------|
| **Backend** | Python 3.12, Flask 3.0, Flask-CORS 4.0, Flask-Limiter 3.5 |
| **Frontend** | React 19, TypeScript 4.9, Recharts 3.8, Axios 1.17 |
| **Database** | PostgreSQL (public, raw, config, layer4 schemas) |
| **AI/LLM** | Google Gemini (gemini-2.0-flash), Groq (qwen3-32b, llama-3.3-70b), GLM (glm-4.7-flash), MOCK mode |
| **Data Sources** | Yahoo Finance (yfinance 0.2), NewsAPI, 6 RSS feeds (feedparser) |
| **Infrastructure** | Docker, Docker Compose, Vercel (frontend), Render (backend) |
| **External Deps** | psycopg2-binary, requests, numpy (Layer 5 only), feedparser, httpx |

### Core Philosophy

When narrative runs ahead of price action, SignalIQ flags it as exhaustion, distribution, or severe divergence — not a prediction, but a systematic measurement of risk conditions. Signals classify into 4 risk regimes and 3 signal states based on the persistence and magnitude of the divergence.

---

## Architecture Diagram

```
                     ┌──────────────────────────────────────────────────┐
                     │                   Frontend                      │
                     │          React 19 + TypeScript UI               │
                     │   Dashboard · Intelligence · Data · About       │
                     │   Methodology · Tech Stack · Architecture       │
                     └──────────────────────┬──────────────────────────┘
                                            │ HTTP / JSON
                     ┌──────────────────────▼──────────────────────────┐
                     │              Flask API (port 10000)             │
                     │     14+ endpoints · CORS · Rate Limiting       │
                     │   yfinance (live) · PostgreSQL (history)        │
                     │   LLM Router (Gemini / Groq / GLM / MOCK)      │
                     │   Market Intelligence Blueprint                 │
                     │   ThreadedConnectionPool · JSON logging         │
                     └──────────────────────┬──────────────────────────┘
                                            │
              ┌─────────────────────────────┬─────────────────────────────┐
              │                             │                             │
  ┌───────────▼───────────┐   ┌────────────▼───────────┐   ┌────────────▼───────────┐
  │    Layer 5 - Fund.    │   │    Layer 4 - Signals   │   │    Layer 3 - NLP       │
  │  Valuation Ratios     │   │  NDI Calculation       │   │  LM Lexicon (558 words) │
  │  Growth Metrics       │   │  Regime Classification │   │  Entity Resolution      │
  │  Profitability Score  │   │  Streak Tracking       │   │  Momentum Z-Scores      │
  │  Sector Benchmarks    │   │  Inverted-U Confidence │   │  Two-Phase Commit       │
  │  NDI Risk Adjustment  │   │  Risk Escalation       │   │  TimeAligner (UTC→ET)   │
  └───────────────────────┘   └───────────┬────────────┘   └─────────────────────────┘
                                          │
                          ┌───────────────▼───────────────┐
                          │       Layer 2 - Database      │
                          │    PostgreSQL (4 schemas)     │
                          │  10 tables · 2 views          │
                          │  13 functions · 6 triggers    │
                          │  Idempotent DDL · Rollback    │
                          └───────────────┬───────────────┘
                                          │
                          ┌───────────────▼───────────────┐
                          │       Layer 1 - Ingestion     │
                          │  Yahoo Finance (OHLCV, 5 assets)│
                          │  6 RSS Feeds (news headlines) │
                          │  O_EXCL locks · Dedup by hash │
                          │  NFKC Unicode Normalization   │
                          │  Cron: prices @20:05, news x3 │
                          └───────────────────────────────┘
```

Data flows in two paths:

**Core pipeline:** fetch → normalize → write (Layer 1) → store (Layer 2) → analyze (Layer 3) → generate signals (Layer 4) → fundamental overlay (Layer 5). Layer 4 exposes a functional API (`process_asset`, `process_batch`) that wires together measurement, persistence, and classification sublayers.

**Live API path:** `/api/prices`, `/api/signals`, `/api/market-intelligence` → yfinance → calculated NDI → JSON response. Note: this path uses a different NDI calculation than the core pipeline (recent return z-score vs momentum period z-score).

**AI enhancement:** Layer 4 signals → `LLMRouter` (Gemini/GLM/Groq, configured via `PRIMARY_LLM` env var) → AI-powered analysis → Flask API → frontend/dashboard.

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
├── .gitignore                              # Git ignore rules
├── pytest.ini                              # Pytest config (smoke/integration/slow)
├── requirements_layer1.txt                 # Layer 1 Python deps
├── requirements_test.txt                   # Test deps (pytest, pytest-cov)
├── docker-compose.yml                      # Docker Compose (API service)
├── Dockerfile                              # Root Docker image
│
├── backend/                                # Flask backend API server
│   ├── Dockerfile                          # Backend Docker image
│   ├── requirements.txt                    # Backend dependencies
│   ├── run.sh                              # Dev startup script
│   ├── fix_analyze.py                      # Analysis fix utility
│   ├── render.yaml                         # Render deployment config
│   ├── static/                             # Built frontend assets
│   └── app/
│       ├── main.py                         # 889-line Flask API, Config class, 14+ routes
│       ├── auth.py                         # API key auth decorators
│       ├── db.py                           # ThreadedConnectionPool
│       ├── llm_service.py                  # Groq-based LLM service
│       ├── entity_linking.py               # Company → ticker resolution
│       ├── event_extractor.py              # News event extraction
│       ├── narrative_builder.py            # Narrative construction
│       ├── news_fetcher.py                 # NewsAPI integration
│       ├── market_intelligence.py          # Blueprint: /api/ticker/analysis/<ticker>
│       ├── extract_events_job.py           # CLI event extraction
│       ├── ingest_news_job.py              # CLI news ingestion
│       ├── store_intel_job.py              # Intelligence storage
│       ├── classification/
│       │   └── event_classifier.py         # 9 event types classifier
│       └── scoring/
│           └── signal_score.py             # Weighted scoring (v1.0)
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
│   ├── package.json                        # React 19, Recharts 3.8, Axios
│   ├── tsconfig.json
│   ├── .env.production                     # API URL: signaliq-l8mi.onrender.com
│   ├── .env.development                    # API URL: http://localhost:10000
│   ├── public/
│   └── src/
│       ├── App.tsx                         # Shell with sidebar + 5 routes
│       ├── index.tsx
│       ├── components/
│       │   ├── styles.ts                   # Dark theme constants
│       │   ├── Dashboard.tsx               # Live signals, KPI cards, charts
│       │   ├── ScanTable.tsx               # Ticker scan results
│       │   ├── TickerAnalysis.tsx          # Per-ticker deep analysis
│       │   ├── ExpandedRow.tsx             # Expanded signal detail
│       │   ├── Layout.tsx                  # App layout shell
│       │   ├── NDIGauge.tsx                # NDI gauge visualization
│       │   ├── NDIThermometer.tsx          # NDI thermometer visualization
│       │   ├── NDIVelocimeter.tsx          # SVG semi-circular gauge
│       │   ├── NarrativePanel.tsx          # Narrative analysis panel
│       │   ├── TickerFocusStrip.tsx        # Ticker focus/detail strip
│       │   ├── EconomicFoundation.tsx      # Theory cards
│       │   ├── Methodology.tsx             # NDI explanation
│       │   ├── Architecture.tsx            # 6-layer diagram
│       │   ├── Data.tsx                    # Data sources
│       │   ├── DataRecovery.tsx            # Data recovery view
│       │   ├── TechStack.tsx               # Technology breakdown
│       │   ├── AnalysisContainer.tsx       # Analysis container
│       │   ├── About.tsx                   # Author bio
│       │   └── market-intelligence/        # Market Intelligence components
│       └── pages/
│           ├── Dashboard.tsx               # Signals dashboard
│           ├── Intelligence.tsx            # Ticker analyzer
│           ├── Data.tsx                    # Data sources
│           ├── ScanTable.tsx               # Scan results
│           ├── ExpandedRow.tsx             # Expanded signal detail
│           ├── EconomicFoundation.tsx      # Economic foundation
│           ├── About.tsx                   # About page
│           └── Docs.tsx                    # Documentation
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
│   ├── thresholds.py                       # Centralized thresholds (MIN_PRICE_HISTORY_DAYS, etc.)
│   └── __pycache__/
│
├── scripts/                                # Operations & Utilities (14 scripts)
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
│   ├── install_crontab.sh                  # Idempotent cron installer
│   ├── rotate_logs.sh                      # Daily rotation, 90-day retention
│   └── verify_refactor.py                  # Structural verification
│
├── web/                                    # Standalone HTML dashboards
│   ├── index.html                          # Dark-themed institutional dashboard
│   ├── automatico.html                     # Automated dashboard
│   └── test.html                           # Simple API test UI
│
├── tests/                                  # Official test suite
│   └── pytest/                             # Single source of truth
│       ├── test_smoke.py                   # 4 smoke tests (Layer4, Config, Layer1, API)
│       ├── test_architecture.py            # 4 architecture invariants
│       ├── test_db_contract.py             # DB migration/schema tests (integration)
│       └── test_integration.py             # Full system integration test (integration)
│
└── logs/                                   # Runtime logs (.gitignore)
    ├── about.tsx
    ├── app.log
    └── ingestion.log
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
| `002_fix_schema.sql` | Creates `raw`, `config`, `layer4` schemas; wrapper functions `insert_price_record`, `insert_headline_record`; views `raw.prices`, `raw.news_headlines`; table `config.news_sources` |
| `003_create_signal_tables.sql` | Signal classification extension tables |
| `master_build.sql` | Transactional build wrapper (all-or-nothing migration) |
| `rollback.sql` | Complete teardown of all schemas and tables |
| `test_queries.sql` | 24 validation queries verifying schema completeness |

**Stats:** 10 tables, 2 views, 13 functions, 6 triggers, 4 schemas, 4 roles

**Key constraints:**
- `UNIQUE(ticker, price_date, source)` on prices — upsert semantics
- `UNIQUE(sha256_hash)` on headlines — content deduplication
- `UNIQUE(ticker, signal_date)` on ndi_signals — one signal per ticker per day

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
| `layer4_measurement.py` | NDI = `sentiment_zscore - momentum_zscore`. Validity gates check input completeness. 5-day return calculation |
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

**7 Regimes (API `classify_regime`):**
| Regime | NDI Range | Recommendation |
|--------|-----------|---------------|
| Extreme Overheating | NDI > 2.0 | SELL |
| Overheating | NDI > 1.5 | REDUCE |
| Watching | NDI > 0.5 | MONITOR |
| Stable | NDI > -0.5 | HOLD |
| Aligned | NDI > -1.5 | BUY |
| Aligned negative | NDI > -2.0 | (buffer) |
| Strong Undervalued | NDI ≤ -2.0 | STRONG_BUY |

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
PRIMARY_LLM (env var) → FALLBACK_LLM (env var) → MOCK mode
```

| Provider | Model | Config |
|----------|-------|--------|
| Google Gemini | gemini-2.0-flash | `GEMINI_API_KEY_1/2/3` |
| Groq | qwen3-32b, llama-3.3-70b-versatile | `GROQ_API_KEY` |
| GLM (ZhipuAI) | glm-4.7-flash | `GLM_API_KEY` |
| MOCK | — | No key required |

**Integration:** `Layer4Orchestrator.process_signal()` calls `llm_router.analyze_signal()` for AI-powered narrative analysis.

### Flask API (`backend/app/main.py`)

**889-line Flask application** with environment-driven `Config` class, CORS, rate limiting, JSON logging, and 14+ endpoints.

#### Config Class

All configuration is driven by environment variables with sensible defaults:

```python
class Config:
    DATABASE_URL              # PostgreSQL connection string
    GOOGLE_API_KEY            # Gemini API key
    GROQ_API_KEY              # Groq API key
    CORS_ORIGINS              # Comma-separated allowed origins
    REDIS_URL                 # Rate limiting backend (default: memory://)
    PORT / HOST               # Server binding (default: 10000 / 0.0.0.0)
    APP_VERSION               # "2026-07-07"
    APP_ENV                   # "production"
    APP_MODE                  # "REAL"
    DEFAULT_TICKERS           # NVDA,AAPL,MSFT,TSLA,GOOGL,META,AMD,AMZN,JPM,KO
    PRICE_HISTORY_LIMIT       # 60 days
    MOMENTUM_PERIOD           # 20 days
    NDI_CLAMP_MIN/MAX         # -3.0 / 3.0
```

#### Regime Classification (API)

The live API uses a 7-regime system with buy/sell recommendations:

```python
thresholds = {
    'extreme_overheating': 2.0,   # → SELL
    'overheating': 1.5,           # → REDUCE
    'watching': 0.5,              # → MONITOR
    'stable': -0.5,               # → HOLD
    'aligned': -1.5,              # → BUY
    'strong_undervalued': -2.0    # → STRONG_BUY
}
```

All thresholds and labels are configurable via environment variables (`THRESHOLD_EXTREME_OVERHEATING`, `REGIME_OVERHEATING`, etc.).

#### API Endpoints

| Endpoint | Method | Rate Limit | Data Source | Description |
|----------|--------|------------|-------------|-------------|
| `/` | GET | — | — | API root with version, build, endpoints |
| `/health` | GET | — | PostgreSQL | Health check with DB status |
| `/api/prices` | GET | 10/min | yfinance | Historical prices for 1+ tickers |
| `/api/signals` | GET | 30/min | yfinance | NDI signals for 1+ tickers |
| `/api/analyze` | POST | 10/min | Gemini + Groq | LLM text analysis + event classification |
| `/api/classify` | POST | 30/min | EventClassifier | Event type classification |
| `/api/regimes` | GET | — | — | All regime definitions with examples |
| `/api/tickers` | GET | — | yfinance | Default ticker list + search |
| `/api/ticker-info` | GET | — | yfinance | Detailed ticker metadata |
| `/api/market-intelligence` | GET | 5/min | yfinance + LLM | Sector/ticker market intelligence |
| `/api/market-intelligence/trends` | GET | 5/min | yfinance | Market trends across top tickers |
| `/api/ticker/analysis/<ticker>` | GET | — | PostgreSQL | Deep ticker analysis (Blueprint) |
| `/api/test` | GET | — | — | Blueprint connectivity test |

#### NDI Calculation (Live API)

```python
def calculate_ndi(closes):
    daily_returns = [(closes[i] - closes[i-1]) / closes[i-1] ...]
    sentiment_zscore = (latest_return - mean_returns) / std_returns
    momentum_zscore  = (latest_momentum - mean_momentum) / std_momentum
    ndi = sentiment_zscore - momentum_zscore
    ndi = clamp(ndi, -3.0, 3.0)
    return ndi, sentiment_zscore, momentum_zscore
```

This differs from the core L4 formula (`sentiment_zscore - momentum_zscore` using rolling 20-day z-scores from the offline pipeline).

**3-tier fallback (removed):** The API previously used Finnhub.io → yfinance → Mock fallback chain. Now uses yfinance exclusively.

**Structured logging:** JSON-formatted logs via `JSONFormatter` with timestamp, level, module, function, and line number.

### Market Intelligence Blueprint (`backend/app/market_intelligence.py`)

Registered at `/api` prefix via Flask Blueprint.

#### `/api/ticker/analysis/<ticker>` — Deep Ticker Analysis

Returns a comprehensive analysis including:

```json
{
  "ticker": "NVDA",
  "ndi": 0.85,
  "statusLabel": "WATCHING",
  "confidenceScore": 72.5,
  "measuredMetrics": {
    "sentiment": 0.03,
    "momentum": -0.02,
    "divergence": 0.85,
    "sourcesCount": 12
  },
  "narrativeBreakdown": {
    "consensusPercentage": 86,
    "intensityPercentage": 67,
    "dispersionValue": 0.05,
    "mediaBias": { "centerBizPercentage": 60, ... }
  },
  "narrativeExhaustion": {
    "status": "MEDIA",
    "conditionsObservedCount": 1,
    "conditionsDetails": [...]
  },
  "aiInterpretation": "NVDA: NDI 0.850, Régimen: WATCHING...",
  "newsSummary": {
    "items": [...],
    "positiveCount": 0,
    "negativeCount": 0,
    "averageSentiment": 0.0
  },
  "relativeContext": {
    "sectorName": "Technology",
    "comparison": { ... },
    "ranking": [
      {"rank": 1, "ticker": "NVDA", "ndi": 0.85},
      ...
    ],
    "insight": "NVDA: Divergencia de 0.850 entre narrativa y precio."
  }
}
```

#### `/api/test` — Blueprint Test

Returns `{"status": "ok", "message": "Market Intelligence is working!"}`

### Layer 6 — Frontend (`frontend/`)

**React 19 + TypeScript** app with 5 routes (Dashboard, Intelligence, Data, About, Docs), refactored into focused components and pages.

| Component | Lines | Purpose |
|-----------|-------|---------|
| `App.tsx` | 76 | Shell with sidebar navigation |
| `components/Dashboard.tsx` | 298 | Live signals grid, KPI cards, NDI chart |
| Other components | ~500 | ScanTable, TickerAnalysis, ExpandedRow, Layout, NDIVelocimeter, NarrativePanel |
| Pages | ~200 | Dashboard, Intelligence, Data, About, Docs |

**Styling:** Shared `C` object from `styles.ts` — dark theme with 15+ color tokens. All components use inline style objects. Tailwind config and PostCSS config exist but are unused.

**Data fetching:** Axios to `REACT_APP_API_URL` (default: localhost:10000, production: `signaliq-l8mi.onrender.com`). Falls back to static data when backend unreachable. 5-minute polling with error recovery.

**Setup proxy:** `frontend/src/setupProxy.js` proxies `/api` to `signaliq-l8mi.onrender.com` in development.

**Standalone HTML dashboards** available in `web/`: `index.html` (dark institutional), `automatico.html` (automated), `test.html` (API test).

---

## Backend Services (`backend/app/`)

### DB Pool (`db.py`)

```python
ThreadedConnectionPool(
    minconn=1, maxconn=10,
    retries=3, retry_delay=0.5,
    sslmode="require"
)
```

Exponential backoff retry (3 attempts). Used by `main.py` via `execute_query_one()` / `execute_query()`.

### Auth (`auth.py`)

Two decorators:
- `require_api_key` — requires `X-API-Key` header (used by `/api/analyze`)
- `require_api_key_optional` — logs warning if key missing but allows access (used by most endpoints)

### Event Classifier (`classification/event_classifier.py`)

Classifies news into 9 event types using keyword matching:
- earnings, guidance, merger_acquisition
- analyst_upgrade, analyst_downgrade
- product_launch, regulatory, lawsuit, executive_change

### Signal Scoring (`scoring/signal_score.py`)

Weighted scoring engine (v1.0) with 4 components:
- Sentiment (35%)
- Relevance (25%)
- Source quality (20%) — Bloomberg: 100, Reuters: 90, etc.
- Event type (20%)

### LLM Service (`llm_service.py`)

Groq-based service with primary model `qwen/qwen3-32b` and fallback `llama-3.3-70b-versatile`. Mock mode when no API key.

---

## Configuration

### Thresholds (`config/thresholds.py`)

Centralized constants used by Layer 4:

```python
NDI_ACTIVE_THRESHOLD = 1.5
NDI_STRONG_THRESHOLD = 0.7
NDI_FLAT_PRICE_THRESHOLD = 0.005
PRICE_CHANGE_THRESHOLD = 0.02
MIN_PRICE_HISTORY_DAYS = 6
```

### Environment Variables

| Variable | Purpose |
|----------|---------|
| `PRIMARY_LLM` | LLM provider (gemini/glm/groq/mock) |
| `FALLBACK_LLM` | Fallback provider |
| `GROQ_API_KEY` | Groq API key |
| `GOOGLE_API_KEY` | Gemini API key |
| `GEMINI_API_KEY_1/2/3` | Gemini API keys (3 for redundancy) |
| `GLM_API_KEY` | ZhipuAI GLM API key |
| `FINNHUB_API_KEY` | Finnhub.io API key |
| `NEWS_API_KEY` | NewsAPI key |
| `DATABASE_URL` | PostgreSQL connection string |
| `DATABASE_URL_LOCAL` | Local PostgreSQL connection string |
| `NDI_THRESHOLD` | Signal threshold (default: 0.7) |
| `MAX_GAP_DAYS` | Max gap before streak reset (default: 3) |
| `LOOKBACK_DAYS` | Rolling window for z-scores (default: 30) |
| `CORS_ORIGINS` | CORS allowed origins (comma-separated) |
| `USE_JSON_LOGS` | Toggle JSON structured logging |
| `ENVIRONMENT` | Runtime environment (test/prod) |
| `TICKER_REGEX` | Ticker validation regex |
| `MAX_TICKER_LEN` | Max ticker length (default: 10) |
| `DEFAULT_TICKERS` | Comma-separated default ticker list |

Plus 20+ threshold environment variables for regime classification labels, colors, and recommendations.

**Note:** `load_dotenv()` is guarded by `ENVIRONMENT != 'test'` to prevent side effects during test imports.

---

## Testing

### Test Suite (pytest — single source of truth)

| Test File | Type | Tests | Dependencies | Status |
|-----------|------|-------|-------------|--------|
| `test_smoke.py` | Smoke | 4 | None | ✅ Pass |
| `test_architecture.py` | Architecture | 4 | None | ✅ Pass |
| `test_db_contract.py` | Integration | — | PostgreSQL | ⏭️ Skip if no DB |
| `test_integration.py` | Integration | — | Flask API | ⏭️ Skip if no API |

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
2. **No circular imports** — `layer4_measurement.py` does not import from `layers/__init__.py`
3. **NDI formula consistency** — All NDI functions use `sentiment_zscore - momentum_zscore`
4. **Zero sys.exit** — No `sys.exit()` in library code (only in `__main__` blocks)

### Code Quality

- **No linter configured** — No ruff, black, flake8, or mypy
- **Minimal type hints** — Some modules have type annotations, but most lack them
- **Mixed language** — Spanish and English used inconsistently

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
- **Base image:** python:3.12-slim
- **Entrypoint:** `python -m app.main`

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
| **ThreadedConnectionPool** | Efficient connection reuse with exponential backoff retry |
| **JSON structured logging** | Machine-parseable logs for production observability |
| **Pytest as single source of truth** | Replaced legacy test framework; compatible with CI/CD |
| **Environment-driven Config class** | All API configuration via env vars with sensible defaults |
| **Market Intelligence Blueprint** | Separate Flask Blueprint for organized route registration |

---

## Status Summary

### ✅ Completed
- All 6 layers implemented and integrated
- 22+ blockers resolved across 6+ refactoring rounds
- 8 tests pass with no external dependencies
- All API keys removed from source code
- Frontend refactored from monolith to focused components
- ~35% dead code removed, directory structure cleaned
- Database schema completed with all 4 schemas
- Rate limiting with Flask-Limiter
- Architecture invariants enforced by tests
- Centralized thresholds in `config/thresholds.py`
- Environment-driven `Config` class in API
- JSON structured logging throughout API
- Market Intelligence endpoint with deep ticker analysis
- Flask Blueprint for organized routing
- Cross-origin CORS support for Vercel deployment

### 🔶 Known Issues
- Triplicate NDI formula in live API path vs core L4 vs frontend
- 7 regimes (API) vs 4 regimes (core L4) — different thresholds and semantics
- API keys in git history (need `git filter-repo`)
- CORS origins still need maintenance
- `print()` in production modules (`layer4_orchestrator.py`)
- Connection pool lifecycle management
- ~120 hardcoded values remain
- No CI/CD pipeline
- Zero frontend tests
- Minimal type hints or linter
- Mixed language (ES/EN)
- Market Intelligence endpoint has some hardcoded values

### 🚀 Future Directions
- CI/CD with GitHub Actions
- Frontend tests (Jest + Cypress)
- Async task queue (Celery + Redis)
- Type hints + linter (ruff)
- Multi-replica deployment
- Performance benchmarking
- NDI formula unification across all layers
- Regime model reconciliation (core L4 ↔ API ↔ frontend)

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

# Backend API server
python backend/app/main.py

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
- `layers/system_config.py` exposes `DATA_DIR`, `db_url`, and all LLM provider settings
- `calculate_narrative_divergence_index()` is the canonical NDI function in `layer4_measurement.py`
- The live API `calculate_ndi()` in `main.py` uses a different formula (recent return z-score vs momentum period z-score) — known inconsistency
- `classify_regime()` in `main.py` supports 7 configurable regimes; core L4 uses 4 academic regimes
- The Market Intelligence Blueprint (`market_intelligence.py`) registers at `/api` prefix
- No `sys.exit()` in library code — exceptions propagate for graceful handling
- `load_dotenv()` guarded by `ENVIRONMENT != 'test'` — no import-time side effects
- Layer 1 installs no cron jobs automatically — run `scripts/install_crontab.sh`
- The frontend is a Create React App — run `npm install && npm start` from `frontend/`
- Architecture invariants enforced by `test_architecture.py` (4 tests)
- Fundamental engine requires `numpy`; all other layers remain stdlib-only
- `docker-compose.yml` reads API keys from `.env` via `${VAR:-}` references
- Production frontend URL: `https://signaliq-zeta-ten.vercel.app`
- Production API URL: `https://signaliq-l8mi.onrender.com`
