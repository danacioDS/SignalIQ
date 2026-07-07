# SignalIQ — Repository Analysis Report

> **Author:** Daniel Canedo (ML Engineer at Anyone AI, MSc. Economics — Yokohama National University)
> **Repository:** [github.com/danacioDS/SignalIQ](https://github.com/danacioDS/SignalIQ)
> **Generated:** July 7, 2026

---

## 1. Executive Summary

SignalIQ is a market intelligence framework that measures the divergence between market **narratives** (news sentiment) and **price action** (momentum) via a custom metric called the **Narrative Divergence Index (NDI)**:

```
NDI = sentiment_zscore − momentum_zscore
```

The project is architecturally complete across 6 layers (Ingestion → Database → NLP → Signal Generation → Fundamental Analysis → Frontend), with a Flask API backend and a React TypeScript dashboard deployed to production on Vercel + Render. Core analytics layers (3–4) are pure Python stdlib with zero external dependencies — a deliberate design choice for stability and portability.

The live API has been recently simplified to a yfinance-only, no-database architecture. The production `main.py` (213 lines) serves 6 endpoints with NDI calculation, regime classification, and ticker analysis using real-time Yahoo Finance data.

**Status:** All layers implemented. 22+ blockers resolved across 6+ refactoring rounds. ~35% dead code removed. 8 automated tests pass (smoke + architecture invariants). Production deployment active. API simplified to yfinance-only with no database dependency.

---

## 2. Architecture Overview

### 2.1 Six-Layer Design

```
Layer 1: Ingestion      │  Yahoo Finance OHLCV (5 assets) + 6 RSS feeds
Layer 2: Database       │  PostgreSQL (4 schemas, 10 tables, 13 functions, 6 triggers)
Layer 3: NLP            │  Entity resolution + Loughran-McDonald sentiment + momentum z-scores
Layer 4: Signals        │  NDI calculation + regime classification + streak tracking + confidence
Layer 5: Fundamental    │  Valuation/growth/profitability scoring (0–100), NDI risk adjustment
Layer 6: Frontend       │  React 19 + TypeScript + Recharts dashboard (Vercel)
        LLM Router      │  Gemini / Groq / GLM / MOCK — cross-cutting enhancement layer
```

### 2.2 Data Flow

Two paths exist:

1. **Core Pipeline (offline/batch):**
   `Layer 1 → Layer 2 (DB) → Layer 3 → Layer 4 → Layer 5 → signals`

2. **Live API Path (online, production):**
   `yfinance → NDI calculation (inline) → regime classification → JSON response`
   *The live API (`main.py`) operates independently of the database. NDI is calculated from yfinance OHLCV data using a different methodology than core L4: recent return z-score vs momentum period z-score. This is a known architectural inconsistency.*

### 2.3 Tech Stack

| Component | Technology |
|-----------|------------|
| Backend (production) | Python 3.12, Flask 3.0, Flask-CORS |
| Backend (full) | Python 3.12, Flask 3.0, Flask-CORS, psycopg2-binary, numpy |
| Frontend | React 19, TypeScript 4.9, Recharts 3.8, Axios 1.17, React Router 7 |
| Database | PostgreSQL (4 schemas) — used by offline pipeline only |
| LLM | Google Gemini 2.0-flash, Groq (Qwen/Llama), GLM 4.7-flash |
| Data Sources | Yahoo Finance (yfinance 0.2), NewsAPI, 6 RSS feeds (Reuters, AP, CNBC, etc.) |
| Infrastructure | Docker, Vercel (frontend), Render (backend) |

---

## 3. Layer-by-Layer Analysis

### Layer 1 — Ingestion (`ingestion/`)

- **5 modules:** `http_client.py`, `collect_prices.py`, `collect_news.py`, `writer.py`, `orchestrator.py`
- **Assets tracked:** NVDA, AAPL, MSFT, SPX, BTC-USD
- **News sources:** Reuters, AP, Yahoo General/Finnhub, CNBC, MarketWatch (6 RSS feeds)
- **Key patterns:** O_EXCL filesystem locks (prevents concurrent runs), SHA256 dedup for headlines, NFKC normalization, numpy type conversion in writer
- **Cron:** Prices daily @20:05, news 3× daily (06, 12, 18)
- **Quality:** Clean separation of concerns; zero `sys.exit()` in library code

### Layer 2 — Database (`sql/`)

- **6 migration files:** 001 (core tables), 002 (schemas/views/wrappers), 003 (extension tables), master_build, rollback, test_queries
- **Constraints:** `UNIQUE(ticker, price_date, source)` on prices, `UNIQUE(sha256_hash)` on headlines, `UNIQUE(ticker, signal_date)` on ndi_signals
- **Idempotent DDL:** `IF NOT EXISTS` / `ON CONFLICT DO NOTHING` throughout
- **24 validation queries** in `test_queries.sql`
- **Note:** The production API no longer uses the database; Layer 2 serves the offline batch pipeline only.

### Layer 3 — NLP Intelligence (`layers/`)

- **Modules:** `lm_lexicon.py` (Loughran-McDonald, 558 words, 6 categories), `layer3_entity.py` (two-phase resolution), `layer3_sentiment.py` (rolling z-scores), `layer3_momentum.py` (two-phase commit), `layer3_orchestrator.py` (TimeAligner, finalize_day)
- **Stdlib-only** — zero external dependencies
- **Two-phase commit for momentum:** Returns are stored as "pending" until `commit_pending_returns()` is called, preventing look-ahead bias in z-score calculations
- **Rolling window:** 20-day lookback, minimum 10 valid days required

### Layer 4 — Signal Generation (`layers/`)

- **Modules:** `layer4_measurement.py` (NDI formula), `layer4_persistence.py` (streak tracking), `layer4_classification.py` (confidence/risk), `layer4_orchestrator.py` (9-step pipeline + `Layer4Orchestrator` class with LLM integration)
- **Output schema (12 fields):** ticker, date, ndi, ndi_delta, ndi_trend, regime, signal_state, confidence, price_modifier, persistence_days, risk_level, attention
- **Stdlib-only** — zero external dependencies

#### Regime Classification (Core L4 — 4 regimes)

| Regime | NDI Range | Description |
|--------|-----------|-------------|
| ALIGNED | \|NDI\| < 1.5 | Narrative matches price action |
| ACCUMULATION_DIVERGENCE | NDI < -1.5 | Price stronger than narrative |
| OVERHEATING_DIVERGENCE | NDI > 1.5 | Narrative stronger than price |
| INSUFFICIENT_DATA | < 2 valid points | Not enough data |

#### Signal States
- **INACTIVE** (0 breaches) → **WATCHING** (1 breach) → **ACTIVE** (2+ consecutive breaches)

#### Confidence Model
- **Inverted-U:** NDI between 0.8–2.2 = HIGH confidence; below 0.8 or above 2.2, confidence decreases quadratically
- **Streak boost:** After 3+ consecutive days, confidence increases one level

### Layer 5 — Fundamental Analysis (`layers/fundamental/`)

- **Modules:** `metrics_calculator.py` (P/E, P/B, P/S, CAGR, margins, ROE, ROA, FCF yield, D/E), `score_aggregator.py` (sector-benchmarked 0–100), `fundamental_engine.py` (NDI risk adjustment)
- **External dep:** numpy
- **Sectors:** Technology, Financials, Healthcare, Consumer, Energy, Industrial
- **Quality ratings:** Excellent / Good / Fair / Weak / Distressed

### LLM Router (`layers/llm_router.py`)

- **Singleton pattern** — 4 providers: Gemini (gemini-2.5-flash/gemini-1.5-flash), GLM (glm-4.7-flash), Groq (llama-3.3-70b-versatile), MOCK
- **Fallback chain:** `PRIMARY_LLM → FALLBACK_LLM → MOCK` (both default to `"mock"`)
- **Integration:** Called by `Layer4Orchestrator.process_signal()` for AI-enhanced narrative analysis
- **Note:** `system_config.py` defaults primary to `"glm"` and fallback to `"groq"` — inconsistent with `llm_router.py` defaults

### Layer 6 — Frontend (`frontend/`)

- **React 19 + TypeScript**, 6 routes via React Router v7
- **31 components** across `components/` and `components/market-intelligence/`
- **Key components:** `NDIVelocimeter` (SVG semi-circular gauge), `NarrativePanel`, `TickerFocusStrip`, `useSignalAnalysis` hook
- **Dark theme** with shared `C` style constants (Tailwind installed but unused)
- **Data fetching:** Axios → `signaliq-api.onrender.com`, 5-minute polling, static fallback
- **Deployed on Vercel:** [signaliq-zeta-ten.vercel.app](https://signaliq-zeta-ten.vercel.app)

### Flask API — Production (`backend/app/main.py`)

**213-line Flask application** — yfinance-only, no database dependency.

- **6 endpoints:**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API root with version, mode, status |
| `/health` | GET | Health check |
| `/api/health` | GET | Health check (alternative path) |
| `/api/ticker/analysis/<ticker>` | GET | Deep ticker analysis with NDI, regime, quantitative metrics |
| `/api/tickers` | GET | Default ticker list (10 tickers) |

- **Data source:** yfinance exclusively — no PostgreSQL, no Finnhub, no mock fallback
- **NDI calculation:** Inline `calculate_ndi()` with clamping to [-3.0, 3.0]. Uses recent return z-score for sentiment and 20-period momentum z-score — different from core L4's rolling z-score approach.
- **Regime classification (API):** 7 regimes — EXTREME OVERHEATING (SELL), OVERHEATING (REDUCE), WATCHING (MONITOR), NEUTRAL (HOLD), ALIGNED (BUY), STRONG UNDERVALUED (STRONG BUY), CAPITULATION (ACCUMULATE)
- **CORS:** 5 explicitly allowed origins (localhost, Vercel, Render)
- **No rate limiting** — Flask-Limiter not applied
- **No Config class** — environment variables accessed directly via `os.environ.get()`
- **No authentication** — all endpoints publicly accessible
- **No database** — all data from yfinance, with hardcoded mock narrative data (consensus 74%, intensity 52%, media bias 60/20/20)

### Flask API — Full (`backend/app/api.py`)

**257-line alternative entry point** — nearly identical to `main.py` but with:
- Exponential backoff retry for yfinance requests (User-Agent rotation)
- More robust error handling
- Used as a development/debug variant alongside `main.py`

### Flask API — Legacy Components (`backend/app/`)

The following modules exist but are **not imported or used** by the production `main.py`:

| Module | Status |
|--------|--------|
| `market_intelligence.py` | Blueprint defined but never registered |
| `db.py` | ThreadedConnectionPool — unused by production API |
| `auth.py` | API key decorators — unused by production API |
| `llm_service.py` | Groq-based LLM service — unused by production API |
| `event_extractor.py` | News event extraction — unused by production API |
| `narrative_builder.py` | Narrative construction — unused by production API |
| `news_fetcher.py` | NewsAPI integration — unused by production API |
| `classification/event_classifier.py` | 9 event types — unused by production API |
| `scoring/signal_score.py` | Weighted scoring — unused by production API |
| `extract_events_job.py` | CLI — unused by production API |
| `ingest_news_job.py` | CLI — unused by production API |
| `store_intel_job.py` | CLI — unused by production API |
| `entity_linking.py` | Company→ticker — unused by production API |

**~13 of 16 backend modules are effectively dead code in the current production deployment.**

---

## 4. Development Methodology

Based on `workflow.md` and git history (50+ recent commits):

The project follows a structured **Phase 0–6 methodology**:
- **Phase 0:** Conceptual foundation (pitch, economics, statistics, strategy)
- **Phase 1:** High-level design (6-layer architecture, NDI as core metric)
- **Phase 2:** Low-level design (detailed specs per layer)
- **Phase 3:** Production specification (frozen unified spec)
- **Phase 4:** Prompt generation (LLM-friendly module specs)
- **Phase 5:** Implementation (L4 → L3 → L2 → L1 → L5 → L6)
- **Phase 6:** Validation (walk-forward, KS test, AUC-ROC)

Actual build order was **bottom-up**: Layer 4 (signal math) was built first to validate the core metric, then supporting layers were added around it.

**Recent development patterns:**
- **Major simplification:** Production API migrated to yfinance-only, removing database, auth, rate limiting, and most legacy endpoints
- **CORS-heavy iteration:** 9+ commits dedicated to CORS origin configuration
- **Market Intelligence endpoint:** Added to production API with hardcoded mock data
- **Direct-to-main commits:** No PR workflow, rapid deployment cycle
- **Frequent production fixes:** User-Agent rotation, error handling, exponential backoff for yfinance

---

## 5. Testing

### Test Framework
- **pytest** with markers: `smoke`, `integration`, `slow`
- **4 test files, 8 active tests** (4 smoke, 4 architecture invariants)

### Test Coverage

| Test | Type | What It Verifies |
|------|------|------------------|
| `test_import_layer4` | smoke | `process_asset` callable, `OUTPUT_FIELDS` exists |
| `test_import_config` | smoke | Config singleton has expected attributes |
| `test_import_layer1` | smoke | Layer 1 functions callable |
| `test_api_import` | smoke | Flask app exists |
| `test_only_one_layer4_orchestrator` | architecture | No duplicate orchestrator class |
| `test_no_circular_imports` | architecture | Module import graph is acyclic (STUB — currently `pass`) |
| `test_ndi_formula_consistency` | architecture | All NDI functions use `sentiment_zscore - momentum_zscore` |
| `test_no_sys_exit_in_libraries` | architecture | `sys.exit()` only in `__main__` blocks |

### Architecture Invariants (enforced by tests)
1. Single `Layer4Orchestrator` class definition
2. No circular imports (specifically `layer4_measurement` → `layers/__init__`) — **test is a stub**
3. All NDI functions use `sentiment_zscore - momentum_zscore`
4. No `sys.exit()` in library code

### What's NOT Tested
- Layer 3 sentiment, momentum, entity resolution, orchestrator
- Layer 4 classification (confidence, risk, attention)
- NDI measurement formulas
- PersistenceTracker logic
- LLM Router behavior
- Fundamental engine scoring
- Any ingestion modules
- Any frontend code
- Any scripts
- Market Intelligence endpoint
- New API endpoints
- Integration tests (require DB/API — skipped by default)

---

## 6. Known Issues & Technical Debt

### Critical

| Issue | Details |
|-------|---------|
| **Triplicate NDI formula** | Three different NDI implementations: (1) `sentiment_zscore - momentum_zscore` with rolling 20-day z-scores (core L4), (2) `calculate_ndi()` in production API (recent return z-score minus momentum period z-score, clamped to [-3, 3]), (3) frontend `useSignalAnalysis` custom interpretation. These produce different values. |
| **API keys in git history** | `.env` contains live Groq, Google, Finnhub, NewsAPI keys committed to history. Requires `git filter-repo` for remediation. |
| **Production DB credentials exposed** | `DATABASE_URL` with credentials in committed `.env` |
| **~13 of 16 backend modules are dead code** | `main.py` only uses Flask + yfinance + numpy; all other `backend/app/` modules (`market_intelligence.py`, `db.py`, `auth.py`, `llm_service.py`, etc.) are imported but never invoked by the production entry point. The Blueprint `market_intelligence.py` is defined but never registered. |

### High

| Issue | Details |
|-------|---------|
| **7 regimes (API) vs 4 regimes (core L4)** | `classify_regime()` in `main.py` returns 7 regimes with buy/sell recommendations; core L4 uses 4 academic regimes. Different thresholds and semantics. |
| **No authentication** | All API endpoints publicly accessible |
| **No rate limiting** | Flask-Limiter not applied despite being imported and configured |
| **`print()` in production** | `layer4_orchestrator.py` uses `print()` instead of logging |
| **~120 hardcoded values** | Ticker lists, thresholds, sector maps duplicated across files; `main.py` has hardcoded mock data (consensus 74%, media bias 60/20/20) |
| **Frontend/backend regime mismatch** | 7 regimes on API vs 4 in backend core — different thresholds and semantics |
| **No linter or type hints** | No ruff, black, flake8; minimal type annotations |
| **No CI/CD** | No GitHub Actions, no automated test execution |
| **Mock data in production API** | `narrativeBreakdown`, `narrativeExhaustion`, `newsSummary`, `relativeContext` all return hardcoded values — not actual market data |

### Medium

| Issue | Details |
|-------|---------|
| **Mixed language (ES/EN)** | Comments, logs, error messages in Spanish and English; API response fields mix both |
| **Duplicate API entry points** | `main.py` and `api.py` are nearly identical — both serve as production entry points with subtle differences |
| **Zero frontend tests** | React app has no test coverage |
| **Missing GLM dep** | `zhipuai` import in `llm_router.py` not in any requirements file |
| **Dead code** | `write_headline_debug()`, unused CORS env var, duplicate imports, 13 unused backend modules |
| **`load_dotenv()` guard** | `ENVIRONMENT != 'test'` check but env var never set to `test` |
| **Architecture test stub** | `test_no_circular_imports` contains only `pass` |
| **Config default mismatch** | `llm_router.py` defaults both LLMs to `"mock"`; `system_config.py` defaults to `"glm"` / `"groq"` |

---

## 7. Strengths

1. **Clean 6-layer architecture** with clear separation of concerns — each layer independently testable and replaceable
2. **Stdlib-only core** (Layers 3–4) — maximizes stability and portability of the analytics pipeline
3. **Sophisticated design patterns:**
   - Two-phase commit for momentum prevents look-ahead bias
   - Inverted-U confidence model (theoretically grounded — mid-range NDI most reliable)
   - O_EXCL filesystem locks for concurrency safety
   - Singletons for config, LLM router, orchestrator
   - Idempotent DDL for safe migration re-execution
4. **Architecture invariants enforced by automated tests** — prevents regression in fundamental design constraints
5. **Centralized configuration** via `Config` class (environment-driven) and `config/thresholds.py`
6. **Practical deployment** — full Docker support, cron-based ingestion, Vercel + Render production setup
7. **Backtesting framework** included (`scripts/backtest_engine.py`) with Sharpe/Calmar/drawdown metrics
8. **Production API simplification** — yfinance-only architecture reduces operational complexity (no database management, no connection pooling, no migration overhead)

---

## 8. Recommendations

### Immediate (Security)
1. Run `git filter-repo` to scrub all API keys and credentials from git history
2. Rotate all exposed API keys and database credentials
3. Add authentication middleware to all API endpoints
4. Replace `print()` with Python `logging` throughout

### Short-Term (Quality)
5. Reconcile the three NDI formula implementations — pick one canonical formula and enforce it
6. Align frontend regime classification with backend — decide on 4 vs 7 regimes
7. Add type hints and configure ruff for linting
8. Set up GitHub Actions CI with automated test execution

### Medium-Term (Coverage)
9. Add tests for Layer 3 (sentiment, momentum, entity resolution, orchestrator)
10. Add tests for Layer 4 (classification, persistence, measurement)
11. Add frontend tests (Jest + React Testing Library)
12. Remove dead code — clean up unused backend modules or document their purpose
13. Implement actual market data for narrative analysis (replace hardcoded mock values)

### Long-Term (Infrastructure)
14. Decide on API architecture direction: (a) full database-backed API, (b) pure yfinance serverless, or (c) hybrid with caching
15. Implement proper connection pool lifecycle management (if database is re-integrated)
16. Consolidate hardcoded values into centralized configuration
17. Extract all LLM-related code behind a clean interface for easier provider swapping
18. If keeping yfinance-only: add Redis caching layer to reduce API rate limit pressure from Yahoo Finance

---

## 9. Repository Statistics

| Metric | Value |
|--------|-------|
| Python modules (layers/) | 18 |
| Python modules (backend/app/) | 16 |
| Python modules (ingestion/) | 5 |
| Python modules (scripts/) | 12 |
| SQL migration files | 6 |
| TypeScript/React components | ~45 (31 components + 10 pages) |
| API endpoints (production) | 5 |
| Database tables | 10 |
| Automated tests (active) | 8 |
| Git commits (recent) | 50+ |
| LLM providers supported | 4 |
| News sources ingested | 6 |
| Tracked assets (Layer 1) | 5 |
| API tracked assets | 10 (NVDA, AAPL, MSFT, TSLA, GOOGL, META, AMD, AMZN, JPM, KO) |
| External Python dependencies | ~8 |
| NDI regimes (core L4) | 4 |
| NDI regimes (API) | 7 |
| NDI regimes (frontend) | 7 |
| Estimated hardcoded values | ~120 |
| Dead backend modules | ~13 of 16 |

---

## 10. Conclusion

SignalIQ is a functionally complete, production-deployed market intelligence system with a well-architected 6-layer design. The core analytics pipeline (Layers 3–4) demonstrates sophisticated design in its stdlib-only approach, two-phase commit for look-ahead bias prevention, and inverted-U confidence modeling.

The production API has recently undergone a significant simplification: it now runs as a lightweight yfinance-only Flask server with no database, no rate limiting, and no authentication. This reduces operational complexity but introduces new concerns: the NDI formula in the live API differs from the core L4 formula, ~13 of 16 backend modules are now dead code, and the narrative/market intelligence features return hardcoded mock data rather than real market analysis.

The project faces significant technical debt:
1. **Triplicate NDI formula** — the core L4, production API, and frontend all calculate NDI differently
2. **API keys in git history** — a critical security risk requiring `git filter-repo`
3. **Massive dead code burden** — ~80% of backend modules are unused by the production entry point
4. **Mock data in production** — the Market Intelligence endpoint returns fabricated narrative data
5. **Sparse test coverage** — only 8 tests, all smoke/architecture-level, with no unit or integration coverage for most modules

The project would benefit most from: (1) immediate credential remediation, (2) a clear architectural decision on API direction (database-backed vs pure yfinance), (3) NDI formula unification, (4) removal or reactivation of dead code, and (5) expanded test coverage.

---

*Report generated via static analysis of the SignalIQ repository at `/home/daniel/repo_lab/SignalIQ`.*
