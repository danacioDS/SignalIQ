# SignalIQ

postgresql://signaliq_user:7QwQbmPXrNJBdXdy0hwuu4es0hzSS0rw@dpg-d8io1osm0tmc73bqfosg-a/signaliq_db

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
python demo.py          # end-to-end synthetic demo (stdlib only, no DB needed)
```

---

## System Overview

| Layer | Description | Status | Tests |
|-------|-------------|--------|-------|
| **1** | Data ingestion (Yahoo Finance OHLCV + 6 RSS feeds) | Complete | 15 tests, 61 checks |
| **2** | PostgreSQL persistence (10 tables, 13 functions, 6 triggers) | Complete | 24 SQL validation queries |
| **3** | NLP intelligence (entity resolution, Loughran-McDonald sentiment, momentum z-scores) | Complete | 16 tests, 100+ checks |
| **4** | NDI signal generation (measurement, persistence, classification, regimes) | Complete | 15 tests, 80+ checks |
| **5** | Fundamental analysis (valuation, growth, profitability scoring) | Complete | 1 smoke test |
| **AI** | LLM Router (Gemini, GLM, Groq) + Flask REST API | Complete | Mock tests |
| **6** | React TypeScript frontend + HTML institutional dashboards | Partial | — |

---

## Key Features

- **NDI = sentiment_zscore − momentum_zscore** — measures narrative vs. price divergence
- **4 risk regimes**: Aligned, Accumulation Divergence, Overheating Divergence, Insufficient Data
- **3 signal states**: Inactive → Watching → Active (requires 2 consecutive threshold breaches)
- **Inverted-U confidence**: mid-range NDI (0.8–2.2) is most reliable; extreme values are down-weighted
- **LLM Router** with multi-provider support: Gemini, GLM (ZhipuAI), Groq, and MOCK mode
- **Fundamental overlay** adjusts NDI risk/confidence based on valuation, growth, and financial health
- **Stdlib-only core** — only Layer 1 (requests, feedparser, psycopg2) and Layer 5 (numpy) have external deps

---

## Project Structure

```
├── layer1/                  # Data ingestion (5 modules)
├── layers/                  # Layers 3, 4 & 5
│   ├── layer3_*.py          # NLP intelligence
│   ├── layer4_*.py          # NDI signal generation
│   ├── integration.py       # Pipeline entry point (L3→L4)
│   ├── lm_lexicon.py        # Loughran-McDonald lexicon (558 words)
│   ├── signal_analyzer.py   # LLM integration helper
│   └── fundamental/         # Fundamental analysis engine
├── signaliq/core/           # LLM Router + config + persistence
├── frontend/                # React TypeScript UI
├── data_storage/            # SQL migrations (4 files)
├── tests/                   # Official test suite
├── scripts/                 # Cron, log rotation, backtesting
├── synthetic/               # Data generator for demo
├── config/                  # entity_aliases.json
├── docs/                    # HLD, LLD, conceptual, prompts
├── api_signaliq.py          # Flask REST API
├── dashboard.html           # Institutional dark-themed dashboard
├── demo.py                  # End-to-end synthetic demo
└── simple_ndi.py            # Simplified NDI generator
```

---

## Layers in Detail

### Layer 1 — Data Ingestion
Collects daily prices (Yahoo Finance) and news (6 RSS feeds), normalizes, and writes to PostgreSQL.
```bash
python -m layer1.orchestrator --type both
python -m layer1.collect_prices --dry-run
python -m layer1.collect_news --source reuters
```

### Layer 2 — PostgreSQL Persistence
Schema: `raw` (prices, news_headlines), `ops` (ingestion_runs, health), `config` (assets, aliases, sources).
```bash
psql $DATABASE_URL -f data_storage/master_build.sql
```

### Layer 3 — NLP Intelligence
Entity resolution (two-phase: URL param → alias regex), Loughran-McDonald sentiment (558 words, 6 categories), momentum z-scores (20-day rolling window, two-phase commit to prevent look-ahead bias).

### Layer 4 — NDI Signal Generation
4 sublayers with one-direction dependency: Measurement → Persistence → Classification → Orchestration.
12-field output: ticker, date, ndi, ndi_delta, ndi_trend, regime, signal_state, confidence, price_modifier, persistence_days, risk_level, attention.

### Layer 5 — Fundamental Analysis
Valuation ratios (P/E, P/B, P/S), growth metrics (EPS/revenue CAGR), profitability (margins, ROE, ROA), cash flow (FCF yield), financial health (D/E, current ratio). Sector-benchmarked scoring (0–100).

### AI / LLM Layer
Multi-provider LLM Router: Gemini, GLM (ZhipuAI), Groq. Flask API at port 5000 with `/analyze`, `/batch`, `/summary`, `/health` endpoints.

### Layer 6 — Frontend
React TypeScript (Recharts, Axios, Tailwind) + HTML dashboard alternatives.

---

## Testing

```bash
# Official test suite (no network or DB needed — all mock external deps)
python -m tests.test_layer1_integration   # 15 tests, 61 checks
python -m tests.test_layer3               # 16 tests, 100+ checks
python -m tests.test_layer4               # 15 tests, 80+ checks
python -m tests.test_fundamental_engine   # Fundamental smoke test

# Demo
python demo.py                            # 20 synthetic days
```

---

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | — | PostgreSQL connection string |
| `PRIMARY_LLM` | `mock` | LLM provider: `gemini`, `glm`, `groq`, `mock` |
| `GEMINI_API_KEY` | — | Google Gemini API key |
| `NDI_THRESHOLD` | `0.7` | Signal threshold |
| `MAX_GAP_DAYS` | `3` | Max calendar gap before streak reset |
| `LOOKBACK_DAYS` | `30` | Rolling window for z-scores |

---

## Documentation

- `docs/conceptual/` — Strategy & theory (6 docs: pitch, economics, statistics, commercial, data, operations)
- `docs/hld/` — High-level design per layer
- `docs/lld/` — Low-level design per layer
- `docs/production_specification/` — Production architecture specs
- `docs/prompts/` — Development prompts
- `as_built/` — Build transcripts and development history

---

## Core Idea

Markets are driven by stories as much as by numbers. Stories are created, spread, overheat, and exhaust themselves. Numbers (prices, volatility, volume) are slower and heavier. SignalIQ measures the distance between the hot (narrative) and the cold (prices). When that distance becomes abnormal, SignalIQ reports it.
