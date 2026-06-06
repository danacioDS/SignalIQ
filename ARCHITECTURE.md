# SignalIQ Architecture

## System Architecture

```
  Yahoo Finance ──→ layer1 ──→ data_storage ──→ layers/layer3_* ──→ layers/layer4_* ──→ signaliq/core ──→ frontend/
                     prices      raw.prices         sentiment            signal state         LLM Router       React UI
  6 RSS Feeds  ──→  news        raw.news_headlines  momentum             persistence           Flask API       Dashboards
                     http_client ops.ingestion_runs  entity resolution    classification        Gemini / GLM
                     orchestrator config.*           orchestrator         orchestrator          Groq / MOCK
                                                                          integration
                                                                          fundamental
```

Data flows in two paths:

- **Core pipeline:** fetch → normalize → write (L1) → store (L2) → analyze (L3) → generate signals (L4) → fundamental overlay (L5)
- **AI enhancement:** L4 signals → LLMRouter → AI analysis → Flask API → frontend

---

## Layer 1 — Data Ingestion

**Path:** `layer1/` (5 modules)

| Module | File | Responsibility |
|--------|------|---------------|
| HTTP Client | `http_client.py` | Shared `fetch_with_retry()` with configurable retry policy |
| Price Collector | `collect_prices.py` | Yahoo Finance OHLCV for 5 assets (NVDA, AAPL, MSFT, SPX, BTC-USD) |
| News Collector | `collect_news.py` | 6 RSS feeds (reuters, ap, yahoo_general, yahoo_ticker, cnbc, marketwatch) |
| Writer | `writer.py` | PostgreSQL atomic writes with named params |
| Orchestrator | `orchestrator.py` | Coordination, O_EXCL locks, pipe-delimited logging |

**Key design decisions:**
- Prices = transactional (all-or-nothing), news = per-row idempotent
- NFKC unicode normalization for headlines
- Author resolution: `feedparser.authors[].name` → `<author>` fallback
- O_EXCL lock files prevent concurrent ingestion runs
- Pipe-delimited logging to `logs/ingestion.log`

```bash
python -m layer1.orchestrator --type both
python -m layer1.orchestrator --type prices --dry-run
```

**Cron:** `scripts/install_crontab.sh` (prices daily 8:05 PM ET, news at 6/12/18 ET)

---

## Layer 2 — PostgreSQL Persistence

**Path:** `data_storage/` (4 SQL files)

| File | Lines | Purpose |
|------|-------|---------|
| `001_create_layer2_schema.sql` | 61 | Core schema: 10 tables, 13 functions, 6 triggers, 4 roles |
| `master_build.sql` | — | Transactional idempotent build wrapper |
| `rollback.sql` | — | Complete teardown |
| `test_queries.sql` | — | 24 validation queries |

**Schema:**
- `raw.prices` — OHLCV data with SHA256 dedup
- `raw.news_headlines` — Headlines with SHA256 dedup
- `raw.ndi_signals` — NDI output with 12-field schema
- `ops.ingestion_runs` — Run tracking
- `ops.ingestion_health` — Health monitoring
- `config.monitored_assets`, `config.asset_aliases`, `config.news_sources`, `config.vendor_mappings`

**Key functions:**
| Function | Purpose |
|----------|---------|
| `raw.insert_price_record(...)` | Atomic price insert with auto-hash |
| `raw.insert_headline_record(...)` | Atomic headline insert with auto-hash |
| `get_prices_history(ticker, end_date, window)` | L3 read-only price query |
| `get_headlines_range(start, end, tier)` | L3 read-only headline query |
| `get_active_config()` | L3 startup config as JSON |

```bash
psql $DATABASE_URL -f data_storage/master_build.sql
psql $DATABASE_URL -f data_storage/test_queries.sql
```

---

## Layer 3 — NLP Intelligence

**Path:** `layers/layer3_*.py` (6 modules)

```
layer3_config.py         Frozen dataclass (min_headlines, windows, cutoffs)
layer3_entity.py         Two-phase entity resolution: URL param → alias regex
layer3_sentiment.py      Loughran-McDonald polarity + rolling 20-day z-score
layer3_momentum.py       Daily returns, two-phase commit, rolling 20-day z-score
layer3_orchestrator.py   Pipeline coordination, time alignment, finalization
lm_lexicon.py            Loughran-McDonald lexicon (558 words, 6 categories)
```

### Entity Resolution
```
resolve(headline, url_param=None):
  1. Try url_param → if matches known ticker, return it
  2. Fall back to alias regex matching against normalized headline
```

### Sentiment
- Word lists: positive (surge, gain, beat...) and negative (fall, miss, decline...)
- `polarity(text)` = (pos − neg) / total_tokens
- Rolling z-score against 20-day history (min 10 prior observations required)

### Momentum
- Two-phase commit: pending returns → committed history (prevents look-ahead bias)
- Rolling z-score against 20-day history (min 10 prior observations required)

### Loughran-McDonald Lexicon
`lm_lexicon.py` provides:
- `score_text(text)` → counts per category (positive, negative, uncertainty, litigious, constraining, superfluous)
- `net_sentiment(text)` → net score in [-1, 1]

### Output shape
```python
{
    "NVDA": {
        "2026-06-02": {
            "sentiment_zscore": 0.45,
            "momentum_zscore": 0.02,
            "sentiment_raw": 0.33,
            "momentum_return": 0.005,
        }
    }
}
```

**Zero external dependencies (stdlib only).**

---

## Layer 4 — NDI Signal Generation

**Path:** `layers/layer4_*.py` (5 modules)

```
Sub-layer 4A (measurement):
  layer4_measurement.py    Validity gate, NDI = Z_sent − Z_mom, 5d return

Sub-layer 4B (signal state):
  layer4_persistence.py     PersistenceTracker — streak tracking, stale-gap detection
                            Regime classification (ALIGNED / ACCUMULATION / OVERHEATING / INSUFFICIENT)

Sub-layer 4C (classification):
  layer4_classification.py  Confidence (inverted-U), price pressure, risk, attention text

Sub-layer 4D (orchestration):
  layer4_orchestrator.py    9-step pipeline, batch processing, LLM integration
  integration.py             run_pipeline() / run_batch_pipeline() — single entry points
```

### NDI Formula
```
NDI = sentiment_zscore − momentum_zscore
```

### 12-Field Output Schema
```json
{
  "ticker":            "NVDA",
  "date":              "2026-06-02",
  "ndi":               1.7,
  "ndi_delta":         null,
  "ndi_trend":         "ACCELERATING",
  "regime":            "OVERHEATING_DIVERGENCE",
  "signal_state":      "WATCHING",
  "confidence":        "HIGH",
  "price_modifier":    "trend_supporting",
  "persistence_days":  1,
  "risk_level":        "NORMAL",
  "attention":         "Watching for persistence (needs 2nd consecutive day)."
}
```

### Signal States
```
INACTIVE (streak=0) → WATCHING (streak=1) → ACTIVE (streak>=2)
                     stale gap (>3 days) → reset to 0
```

### Confidence (Inverted-U)
```
|NDI| > 2.2  → MEDIUM  (extreme = noise)
|NDI| ≥ 0.8  → HIGH    (stable divergence = reliable)
|NDI| < 0.8  → LOW     (below threshold)
Streak ≥ 3   → boost one level
```

### Risk Escalation
```
OVERHEATING_DIVERGENCE + NEUTRAL price    → ELEVATED
OVERHEATING_DIVERGENCE + PRESSURING price → CRITICAL
All other regimes                         → NORMAL
```

---

## Layer 5 — Fundamental Analysis

**Path:** `layers/fundamental/` (3 modules)

| Module | Responsibility |
|--------|---------------|
| `metrics_calculator.py` | `FundamentalMetrics` dataclass + calculators for P/E, P/B, P/S, margins, ROE, ROA, FCF yield, D/E, etc. |
| `score_aggregator.py` | Weighted scoring across 5 categories (valuation 25%, growth 30%, profitability 20%, cash flow 15%, health 10%) |
| `fundamental_engine.py` | Main engine: `process_metrics()` → metrics → scores → textual analysis |

- Sector-benchmarked (Technology, Financials, Healthcare, Consumer, Energy, Industrial + Default)
- Output: 0–100 score with rating (Excellent / Good / Fair / Weak / Poor)
- Integrates with Layer 4 via `process_signal(fundamental_data=...)` — adjusts risk/confidence

**Depends on `numpy`** (all other layers are stdlib-only).

---

## AI / LLM Layer

**Path:** `signaliq/core/` (3 modules)

| Module | Responsibility |
|--------|---------------|
| `config.py` | `SignalIQConfig` singleton — loads `.env`, sets LLM provider |
| `llm.py` | `LLMRouter` singleton — supports Gemini, GLM (ZhipuAI), Groq, MOCK |
| `persistence.py` | `SignalPersistence` — PostgreSQL + JSON state file |

### LLM Router
- Singleton pattern (global `llm_router` instance)
- Primary LLM from `PRIMARY_LLM` env var
- Fallback chain: primary → fallback (Groq) → MOCK
- Gemini model fallback: `gemini-2.5-flash` → `gemini-1.5-flash` → `gemini-pro`
- Prompt: financial signal analysis in English (2-3 paragraph executive summary)

### Flask API
**File:** `api_signaliq.py` (also multiple variants: `api_final.py`, `api_final_correcta.py`, etc.)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Service status, active LLM clients |
| `/analyze` | POST | Single signal analysis `{ticker, ndi, news}` |
| `/batch` | POST | Multi-signal analysis `{signals: [...]}` |
| `/summary` | GET | Executive summary + performance stats |

Runs on port 5000, CORS-enabled.

---

## Layer 6 — Frontend

**Path:** `frontend/` (React TypeScript + Tailwind + Recharts)

| Component | Description |
|-----------|-------------|
| `App.tsx` | KPI cards (High Confidence count, Avg NDI, Avg Bubble Risk, Market Regime) |
| Signal table | Color-coded NDI, confidence badges, bubble risk bars |
| NDI bar chart | Distribution visualization |
| Connects to remote API at port 8000 |

**HTML alternatives:** `dashboard.html` (dark-themed institutional), `frontend_test.html` (API test UI)

---

## Data Flow Diagrams

### Daily Pipeline
```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  Layer 1 │───→│  Layer 2 │───→│  Layer 3 │───→│  Layer 4 │───→│   AI /   │
│ Fetch    │    │ Store    │    │ Analyze  │    │ Generate │    │  LLM     │
│ Prices & │    │ Prices & │    │ Sentiment│    │ NDI      │    │ Analyze  │
│ News     │    │ News     │    │ & Mom.   │    │ Signals  │    │ Signals  │
└──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘
                                                      │
                                                      ▼
                                               ┌──────────┐
                                               │  Layer 5 │
                                               │ Fund.    │
                                               │ Overlay  │
                                               └──────────┘
                                                      │
                                                      ▼
                                               ┌──────────┐
                                               │  Layer 6 │
                                               │ Frontend │
                                               └──────────┘
```

### AI Enhancement Path
```
Layer 4 Signal → LLMRouter (Gemini/GLM/Groq) → AI Analysis → Flask API → Dashboard/Frontend
```

---

## Complete File Map

```
repo root/
├── ARCHITECTURE.md                          # This file
├── README.md                                # Repo readme
├── .env.example                             # Environment template
├── requirements_layer1.txt                  # psycopg2-binary, requests, feedparser
├── persistence_state.json                   # Runtime state (gitignored)
│
├── layer1/                                  # Layer 1 — Data Ingestion
│   ├── __init__.py
│   ├── http_client.py                       # fetch_with_retry()
│   ├── collect_prices.py                    # Yahoo Finance OHLCV (5 assets)
│   ├── collect_news.py                      # RSS feed collection (6 sources)
│   ├── writer.py                            # PostgreSQL atomic writes
│   └── orchestrator.py                      # Coordination, locks, logging
│
├── layers/                                  # Layers 3, 4 & 5
│   ├── __init__.py                          # Exports L4 + integration + lexicon
│   ├── lm_lexicon.py                        # Loughran-McDonald (558 words, 6 cats)
│   ├── layer3_config.py                     # Frozen config dataclass
│   ├── layer3_entity.py                     # Two-phase entity resolution
│   ├── layer3_sentiment.py                  # Lexicon sentiment + rolling z-score
│   ├── layer3_momentum.py                   # Daily returns + rolling z-score
│   ├── layer3_orchestrator.py               # Pipeline coordination
│   ├── layer4_measurement.py                # Validity gate, NDI, 5d return
│   ├── layer4_persistence.py                # Streak tracking, stale-gap, regimes
│   ├── layer4_classification.py             # Confidence, risk, attention
│   ├── layer4_orchestrator.py               # 9-step pipeline
│   ├── integration.py                       # L3→L4 entry points
│   ├── signal_analyzer.py                   # LLM integration helper
│   └── fundamental/                         # Layer 5
│       ├── __init__.py
│       ├── fundamental_engine.py            # Main engine
│       ├── metrics_calculator.py            # Valuation, growth, profitability
│       └── score_aggregator.py              # Sector-benchmarked scoring
│
├── signaliq/                                # AI/LLM runtime
│   └── core/
│       ├── config.py                        # Singleton config
│       ├── llm.py                           # LLMRouter (Gemini, GLM, Groq, MOCK)
│       ├── llm_simple.py                    # Direct Gemini connection
│       └── persistence.py                   # PostgreSQL + JSON state
│
├── frontend/                                # Layer 6 — React TypeScript
│   ├── public/
│   ├── src/App.tsx                          # KPI cards, signal table, NDI chart
│   ├── package.json                         # React 19, Recharts 3.8, Axios, Tailwind
│   ├── tsconfig.json
│   └── tailwind.config.js
│
├── data_storage/                            # Layer 2 — SQL migrations
│   ├── 001_create_layer2_schema.sql         # Core schema
│   ├── master_build.sql                     # Build wrapper
│   ├── rollback.sql                         # Teardown
│   └── test_queries.sql                     # 24 validation queries
│
├── api_signaliq.py                          # Flask REST API (main)
├── api_final.py                             # API variant (forced Gemini)
├── api_final_correcta.py                    # API variant (Gemini direct)
├── api_dual_gemini.py                       # API variant (dual key rotation)
├── api_triple_gemini.py                     # API variant (triple key rotation)
├── api_new_gemini.py                        # API variant (new Gemini SDK)
├── api_simple_final.py                      # API variant (SimpleLLM)
├── api_automatica.py                        # API variant (auto NDI calc)
├── api_final_2projects.py                   # API variant (2-project keys)
├── api_signaliq_fixed.py                    # API variant (fixed Gemini)
│
├── scripts/
│   ├── install_crontab.sh                   # Cron installer
│   ├── rotate_logs.sh                       # Log rotation (90-day)
│   ├── backtest_engine.py                   # NDI backtesting
│   ├── backtest_improved.py                 # Enhanced backtesting
│   └── run_backtest_real.py                 # Production backtest runner
│
├── tests/
│   ├── test_layer1_integration.py           # 15 tests, 61 checks
│   ├── test_layer3.py                       # 16 tests, 100+ checks
│   ├── test_layer4.py                       # 15 tests, 80+ checks
│   ├── test_fundamental_engine.py           # 1 smoke test
│   └── legacy/                              # Legacy tests
│
├── synthetic/data_generator.py              # Synthetic price + headline generator
├── config/entity_aliases.json               # L3 alias entries (5 tickers)
│
├── dashboard.html                           # Dark institutional dashboard
├── frontend_test.html                       # API test UI
├── demo.py                                  # End-to-end synthetic demo
├── simple_ndi.py                            # Simplified NDI generator
│
├── docs/
│   ├── conceptual/                          # 6 strategy docs
│   ├── hld/                                 # High-level design
│   ├── lld/                                 # Low-level design
│   ├── production_specification/            # Production specs
│   └── prompts/                             # Development prompts
│
└── as_built/                                # Build transcripts
```

---

## Commands Reference

```bash
# Layer 1
python -m layer1.collect_prices
python -m layer1.collect_news --source reuters
python -m layer1.orchestrator --type both

# Layer 2
psql $DATABASE_URL -f data_storage/master_build.sql
psql $DATABASE_URL -f data_storage/test_queries.sql

# Tests
python -m tests.test_layer1_integration
python -m tests.test_layer3
python -m tests.test_layer4
python -m tests.test_fundamental_engine

# Demo
python demo.py

# API
python api_signaliq.py              # Flask on :5000

# LLM
python -m tests.test_llm            # LLM Router test

# Frontend
cd frontend && npm install && npm start

# Backtesting
python scripts/backtest_engine.py
python scripts/run_backtest_real.py

# Cron
./scripts/install_crontab.sh
```

---

## Design Decisions

- **NDI = Z_sent − Z_mom** (not a ratio) — additive divergence measured in standard deviation units
- **Two-phase commit for momentum** — prevents look-ahead bias in z-score calculation
- **Inverted-U confidence** — extreme |NDI| > 2.2 down-weighted (often noise bursts)
- **Stale-gap detection** — 3-day max gap before streak reset (covers weekends)
- **Persistence via JSON file** — streaks survive process restarts without requiring DB
- **Stdlib preference** — only Layer 1 and Layer 5 have external dependencies; core analytics are pure Python
- **Entity resolution via URL param** — RSS feeds from ticker-specific pages bypass alias matching
