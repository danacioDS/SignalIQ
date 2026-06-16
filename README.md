# SignalIQ

> Where market narratives meet market reality.

SignalIQ is a market intelligence framework that measures the distance between what the market is *saying* (news sentiment) and what the market is *actually doing* (price momentum). It quantifies this gap using the **Narrative Divergence Index (NDI)**:

```
NDI = sentiment_zscore − momentum_zscore
```

When narrative runs ahead of price action, SignalIQ flags it as exhaustion, distribution, or severe divergence — not a prediction, but a systematic measurement of risk conditions.

---

## Quick Start

```bash
pip install -r requirements_layer1.txt
cp .env.example .env    # edit with your DATABASE_URL
python scripts/demo.py  # end-to-end synthetic demo (stdlib only, no DB needed)
```

---

## System Overview

| Layer | Description | Status | Tests |
|-------|-------------|--------|-------|
| **1** | Data ingestion (Yahoo Finance OHLCV + 6 RSS feeds) | Complete | 5 modules in `ingestion/` |
| **2** | PostgreSQL persistence (10 tables, 2 views, 13 functions, 6 triggers) | Complete | 6 migration files in `sql/` |
| **3** | NLP intelligence (entity resolution, Loughran-McDonald sentiment, momentum z-scores) | Complete | 6 modules in `layers/` |
| **4** | NDI signal generation (measurement, persistence, classification, regimes) | Complete | 5 modules in `layers/` |
| **5** | Fundamental analysis (valuation, growth, profitability scoring) | Complete | 3 modules in `layers/fundamental/` |
| **AI** | LLM Router (Gemini, GLM, Groq) + Flask REST API | Complete | 2 modules in `layers/` |
| **6** | React TypeScript frontend + HTML institutional dashboards | Partial | `frontend/` + `web/` |

---

## Key Features

- **NDI = sentiment_zscore − momentum_zscore** — measures narrative vs. price divergence
- **4 risk regimes**: Aligned, Accumulation Divergence, Overheating Divergence, Insufficient Data
- **3 signal states**: Inactive → Watching → Active (requires 2 consecutive threshold breaches)
- **Inverted-U confidence**: mid-range NDI (0.8–2.2) is most reliable; extreme values are down-weighted
- **LLM Router** with multi-provider support: Gemini, GLM (ZhipuAI), Groq, and MOCK mode
- **Fundamental overlay** adjusts NDI risk/confidence based on valuation, growth, and financial health
- **Stdlib-only core** — only `ingestion/` and `layers/fundamental/` have external deps

---

## Project Structure

```
├── backend/                # Flask REST API (port 10000, CORS, rate-limited)
│   ├── app/
│   │   ├── main.py         # CORS Flask API with Flask-Limiter
│   │   ├── db.py           # ThreadedConnectionPool
│   │   ├── classification/ # Event classifier (9 event types)
│   │   └── scoring/        # Weighted signal scoring
│   └── requirements.txt
├── ingestion/              # Layer 1 — Data ingestion (5 modules)
│   ├── http_client.py      # Shared HTTP with retry
│   ├── collect_prices.py   # Yahoo Finance OHLCV (5 assets)
│   ├── collect_news.py     # RSS feed collection (6 sources)
│   ├── writer.py           # PostgreSQL atomic writes
│   └── orchestrator.py     # Coordination, O_EXCL locks
├── layers/                 # Layers 3, 4 & 5 — NLP, Signal, Fundamental
│   ├── layer3_*.py         # NLP intelligence (entity, sentiment, momentum)
│   ├── layer4_*.py         # NDI signal generation (measurement, persistence, classification)
│   ├── integration.py      # Pipeline entry point (L3→L4)
│   ├── lm_lexicon.py       # Loughran-McDonald lexicon (558 words)
│   ├── llm_router.py       # LLMRouter (Gemini, GLM, Groq, MOCK)
│   ├── system_config.py    # SignalIQConfig singleton
│   └── fundamental/        # Fundamental analysis engine (3 modules)
├── frontend/               # Layer 6 — React TypeScript UI (Recharts, Tailwind)
│   ├── src/
│   │   ├── App.tsx         # Main app with 6 sections
│   │   └── pages/          # Dashboard.tsx, Landing.tsx
│   ├── package.json
│   └── tsconfig.json
├── sql/                    # Layer 2 — SQL migrations (6 files)
│   ├── 001_create_layer2_schema.sql
│   ├── 002_fix_schema.sql
│   ├── 003_create_signal_tables.sql
│   ├── master_build.sql
│   ├── rollback.sql
│   └── test_queries.sql
├── tests/                  # Official test suite (pytest)
│   └── pytest/
│       ├── test_smoke.py           # 4 smoke tests
│       ├── test_architecture.py    # 4 architecture invariants
│       ├── test_db_contract.py     # 3 DB contract tests
│       └── test_integration.py     # 2 integration tests
├── scripts/                # Operations, demo, backtesting
│   ├── demo.py             # End-to-end synthetic demo (stdlib only)
│   ├── simple_ndi.py       # Simplified NDI signal generator
│   ├── generate_ndi.py     # DB-backed NDI generation
│   ├── backtest_engine.py  # NDI backtesting engine
│   ├── backtest_improved.py
│   ├── run_backtest_real.py
│   ├── validate_ndi.py     # NDI predictive power validation
│   ├── install_crontab.sh  # Idempotent cron installer
│   └── rotate_logs.sh      # Daily rotation, 90-day retention
├── web/                    # Standalone HTML dashboards
│   ├── index.html          # Dark-themed institutional dashboard
│   ├── automatico.html     # Automated analysis dashboard
│   └── test.html           # Simple API test UI
├── config/                 # Configuration
│   ├── thresholds.py       # Production-critical thresholds
│   └── entity_aliases.json # Alias entries for Layer 3
├── docs/                   # HLD, LLD, conceptual, prompts
├── api_signaliq.py         # Legacy Flask REST API (port 5000)
├── Dockerfile              # Backend Docker build
├── docker-compose.yml      # Multi-service orchestration
├── pytest.ini              # Pytest config (smoke/integration/slow markers)
└── .env.example            # Environment variable template
```

---

## Layers in Detail

### Layer 1 — Data Ingestion
Collects daily prices (Yahoo Finance) and news (6 RSS feeds), normalizes, and writes to PostgreSQL.
```bash
python -m ingestion.orchestrator --type both
python -m ingestion.collect_prices --dry-run
python -m ingestion.collect_news --source reuters
```

### Layer 2 — PostgreSQL Persistence
Schema: `raw` (prices, news_headlines), `ops` (ingestion_runs, health), `config` (assets, aliases, sources), `layer4` (signal tables). 10 tables, 2 views, 13 functions, 6 triggers, 4 roles.
```bash
psql $DATABASE_URL -f sql/master_build.sql
```

### Layer 3 — NLP Intelligence
Entity resolution (two-phase: URL param → alias regex), Loughran-McDonald sentiment (558 words, 6 categories), momentum z-scores (20-day rolling window, two-phase commit to prevent look-ahead bias).

### Layer 4 — NDI Signal Generation
4 sublayers with one-direction dependency: Measurement → Persistence → Classification → Orchestration.
12-field output: ticker, date, ndi, ndi_delta, ndi_trend, regime, signal_state, confidence, price_modifier, persistence_days, risk_level, attention.

### Layer 5 — Fundamental Analysis
Valuation ratios (P/E, P/B, P/S), growth metrics (EPS/revenue CAGR), profitability (margins, ROE, ROA), cash flow (FCF yield), financial health (D/E, current ratio). Sector-benchmarked scoring (0–100) against Technology, Financials, Healthcare, Consumer, Energy, Industrial benchmarks.

### AI / LLM Layer
Multi-provider LLM Router: Gemini, GLM (ZhipuAI), Groq. `LLMRouter` singleton with fallback chain (primary → fallback → MOCK). Two Flask API servers: `backend/app/main.py` (port 10000, 8 endpoints, rate-limited) and `api_signaliq.py` (port 5000, legacy).

### Layer 6 — Frontend
React TypeScript (Recharts, Axios, Tailwind) with Dashboard and Landing pages. HTML alternatives in `web/`.

---

## Testing

```bash
# Smoke tests (no network or DB needed)
pytest tests/pytest/ -m "not integration" -v   # 8 tests (4 smoke + 4 architecture)

# Integration tests (requires DB/API)
pytest tests/pytest/ -m integration -v          # 5 tests (3 DB contract + 2 integration)

# Demo
python scripts/demo.py                          # 20 synthetic days
```

---

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | — | PostgreSQL connection string |
| `PRIMARY_LLM` | `gemini` | LLM provider: `gemini`, `glm`, `groq`, `mock` |
| `FALLBACK_LLM` | `mock` | Fallback LLM provider |
| `GEMINI_API_KEY` | — | Google Gemini API key |
| `NDI_THRESHOLD` | `0.7` | Signal threshold |
| `MAX_GAP_DAYS` | `3` | Max calendar gap before streak reset |
| `LOOKBACK_DAYS` | `30` | Rolling window for z-scores |
| `CORS_ORIGINS` | `http://localhost:3000` | Allowed CORS origins |

---

## API Endpoints

| Endpoint | Method | Rate Limit | Purpose |
|----------|--------|------------|---------|
| `/api/health` | GET | — | Health check (REAL/MOCK mode) |
| `/api/signals` | GET | — | Last 50 signals |
| `/api/analyze/<ticker>` | GET | 10/min | Gemini-powered stock analysis |
| `/api/classify` | POST | 30/min | Classify news into event type |
| `/api/score/<ticker>` | GET | — | Latest signal for ticker |
| `/api/stats` | GET | — | DB statistics |
| `/api/version` | GET | — | Build version |
| `/api/routes` | GET | — | List all registered routes |

---

## Documentation

- `docs/conceptual/` — Strategy & theory (6 docs: pitch, economics, statistics, commercial, data, operations)
- `docs/hld/` — High-level design per layer
- `docs/lld/` — Low-level design per layer
- `docs/production_specification/` — Production architecture specs
- `docs/prompts/` — Development prompts

---

## Deployment

```bash
docker compose up -d
```

---

## Core Idea

Markets are driven by stories as much as by numbers. Stories are created, spread, overheat, and exhaust themselves. Numbers (prices, volatility, volume) are slower and heavier. SignalIQ measures the distance between the hot (narrative) and the cold (prices). When that distance becomes abnormal, SignalIQ reports it.
