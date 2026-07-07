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

**Status:** All layers implemented. 22+ blockers resolved across 6+ refactoring rounds. ~35% dead code removed. 13 automated tests pass. Production deployment active. Market Intelligence endpoint added with deep ticker analysis.

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

2. **Live API Path (online):**
   `yfinance → calculated NDI (live) → JSON response`
   *Note: The live API now uses yfinance exclusively (no Finnhub). The NDI calculation uses a slightly different approach (recent return z-score vs momentum period z-score) — known architectural inconsistency.*

### 2.3 Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | Python 3.12, Flask 3.0, Flask-CORS, Flask-Limiter |
| Frontend | React 19, TypeScript 4.9, Recharts 3.8, Axios 1.17 |
| Database | PostgreSQL (4 schemas) |
| LLM | Google Gemini 2.0-flash, Groq (Qwen/Llama), GLM 4.7-flash |
| Data Sources | Yahoo Finance (yfinance 0.2), NewsAPI, 6 RSS feeds (Reuters, AP, CNBC, etc.) |
| Infrastructure | Docker, Vercel (frontend), Render (backend + DB) |

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

### Layer 3 — NLP Intelligence (`layers/`)

- **Modules:** `lm_lexicon.py` (Loughran-McDonald, 558 words, 6 categories), `layer3_entity.py` (two-phase resolution), `layer3_sentiment.py` (rolling z-scores), `layer3_momentum.py` (two-phase commit), `layer3_orchestrator.py` (TimeAligner, finalize_day)
- **Stdlib-only** — zero external dependencies
- **Two-phase commit for momentum:** Returns are stored as "pending" until `commit_pending_returns()` is called, preventing look-ahead bias in z-score calculations
- **Rolling window:** 20-day lookback, minimum 10 valid days required

### Layer 4 — Signal Generation (`layers/`)

- **Modules:** `layer4_measurement.py` (NDI formula), `layer4_persistence.py` (streak tracking), `layer4_classification.py` (confidence/risk), `layer4_orchestrator.py` (9-step pipeline + `Layer4Orchestrator` class with LLM integration)
- **Output schema (12 fields):** ticker, date, ndi, ndi_delta, ndi_trend, regime, signal_state, confidence, price_modifier, persistence_days, risk_level, attention

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

- **Singleton pattern** — 4 providers: Gemini (gemini-2.0-flash), GLM (glm-4.7-flash), Groq (qwen3-32b, llama-3.3-70b), MOCK
- **Fallback chain:** `PRIMARY_LLM → FALLBACK_LLM → MOCK`
- **Integration:** Called by `Layer4Orchestrator.process_signal()` for AI-enhanced narrative analysis

### Layer 6 — Frontend (`frontend/`)

- **React 19 + TypeScript**, 5 routes via React Router
- **Key components:** `NDIVelocimeter` (SVG semi-circular gauge), `NarrativePanel`, `TickerFocusStrip`, `useSignalAnalysis` hook
- **Dark theme** with shared `C` style constants (Tailwind installed but unused)
- **Data fetching:** Axios → `signaliq-api.onrender.com`, 5-minute polling, static fallback
- **Deployed on Vercel:** [signaliq-zeta-ten.vercel.app](https://signaliq-zeta-ten.vercel.app)

### Flask API (`backend/app/`)

- **14+ endpoints**, CORS-enabled, rate-limited (Flask-Limiter)
- **Key endpoints:**
  | Endpoint | Method | Description |
  |----------|--------|-------------|
  | `/` | GET | API root with version/environment info |
  | `/health` | GET | Health check with DB status |
  | `/api/prices` | GET | Historical prices for tickers (yfinance) |
  | `/api/signals` | GET | NDI signals for tickers |
  | `/api/analyze` | POST | LLM-based text analysis |
  | `/api/classify` | POST | Event classification |
  | `/api/regimes` | GET | All regime definitions |
  | `/api/tickers` | GET | Default ticker list + search |
  | `/api/ticker-info` | GET | Detailed ticker info from yfinance |
  | `/api/market-intelligence` | GET | Sector/ticker market intelligence |
  | `/api/market-intelligence/trends` | GET | Market trends across top tickers |
  | `/api/ticker/analysis/<ticker>` | GET | Deep ticker analysis (Market Intelligence) |
  | `/api/test` | GET | Blueprint test endpoint |

- **Data source:** yfinance exclusively (Finnhub tier removed, mock fallback removed)
- **Regime classification (API):** 7 regimes — Extreme Overheating, Overheating, Watching, Stable, Aligned, (Aligned negative), Strong Undervalued
- **JSON structured logging** with `JSONFormatter`
- **Database:** ThreadedConnectionPool (min=1, max=10, exponential backoff retry)
- **LLM integration:** Groq (Qwen/Llama) for ticker analysis; Gemini for text analysis and market summaries
- **Config class:** Environment-driven configuration with sensible defaults

---

## 4. Development Methodology

Based on `workflow.md` and git history (90+ commits):

The project follows a structured **Phase 0–6 methodology**:
- **Phase 0:** Conceptual foundation (pitch, economics, statistics, strategy)
- **Phase 1:** High-level design (6-layer architecture, NDI as core metric)
- **Phase 2:** Low-level design (detailed specs per layer)
- **Phase 3:** Production specification (frozen unified spec)
- **Phase 4:** Prompt generation (LLM-friendly module specs)
- **Phase 5:** Implementation (L4 → L3 → L2 → L1 → L5 → L6)
- **Phase 6:** Validation (walk-forward, KS test, AUC-ROC)

Actual build order was **bottom-up**: Layer 4 (signal math) was built first to validate the core metric, then supporting layers were added around it.

**Patterns observed:**
- Feature-driven with frequent deployment (deploy-to-test strategy)
- Conventional Commits-like prefixes (`feat:`, `fix:`, `refactor:`, `docs:`)
- Direct-to-main commits (no PR workflow)
- Rapid iteration on production issues (CORS, DB connections, blueprints)
- 6+ refactoring rounds with ~35% dead code removal
- Recent focus: Market Intelligence endpoint, CORS hardening, blueprint organization

---

## 5. Testing

### Test Framework
- **pytest** with markers: `smoke`, `integration`, `slow`
- **4 test files, 13 total tests** (8 smoke, 5 integration)

### Test Coverage

| Test | Type | What It Verifies |
|------|------|------------------|
| `test_import_layer4` | smoke | `process_asset` callable, `OUTPUT_FIELDS` exists |
| `test_import_config` | smoke | Config singleton has expected attributes |
| `test_import_layer1` | smoke | Layer 1 functions callable |
| `test_api_import` | smoke | Flask app exists |
| `test_only_one_layer4_orchestrator` | smoke | No duplicate orchestrator class |
| `test_no_circular_imports` | smoke | Module import graph is acyclic |
| `test_ndi_formula_consistency` | smoke | All NDI functions use `sentiment_zscore - momentum_zscore` |
| `test_no_sys_exit_in_libraries` | smoke | `sys.exit()` only in `__main__` blocks |
| `test_migrations_idempotent` | integration | DB migrations safe to re-run |
| `test_raw_functions_exist` | integration | DB wrapper functions present |
| `test_schemas_exist` | integration | DB schemas present |
| `test_full_system_boot` | integration | Flask API responds |
| `test_api_contract` | integration | API response shape correct |

### Architecture Invariants (enforced by tests)
1. Single `Layer4Orchestrator` class definition
2. No circular imports (specifically `layer4_measurement` → `layers/__init__`)
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
- New API endpoints (`/api/regimes`, `/api/tickers`, `/api/ticker-info`, `/api/market-intelligence`)

---

## 6. Known Issues & Technical Debt

### Critical

| Issue | Details |
|-------|---------|
| **Triplicate NDI formula** | Three different NDI implementations: (1) `sentiment_zscore - momentum_zscore` (core L4), (2) `calculate_ndi()` in API (recent return z-score minus momentum period z-score), (3) frontend `useSignalAnalysis` custom interpretation. These produce different values. |
| **API keys in git history** | `.env` contains live Groq, Google, Finnhub, NewsAPI keys committed to history. Requires `git filter-repo` for remediation. |
| **Production DB credentials exposed** | `DATABASE_URL` with credentials in committed `.env` |

### High

| Issue | Details |
|-------|---------|
| **7 regimes (API) vs 4 regimes (core L4)** | `classify_regime()` in `main.py` returns 7 regimes with buy/sell recommendations; core L4 uses 4 academic regimes. Different thresholds and semantics. |
| **No authentication** | All API endpoints publicly accessible (`require_api_key_optional` is a no-op) |
| **`print()` in production** | `layer4_orchestrator.py` uses `print()` instead of logging |
| **`time.sleep()` in production** | `db.py` retry logic uses `time.sleep()` (acceptable for retries, but blocks workers during retries) |
| **~120 hardcoded values** | Ticker lists, thresholds, sector maps duplicated across files |
| **Frontend/backend regime mismatch** | 7 regimes on API vs 4 in backend core — different thresholds and semantics |
| **No linter or type hints** | No ruff, black, flake8; minimal type annotations |
| **No CI/CD** | No GitHub Actions, no automated test execution |

### Medium

| Issue | Details |
|-------|---------|
| **Mixed language (ES/EN)** | Comments, logs, error messages in Spanish and English |
| **Connection pool lifecycle** | `atexit` handler won't fire on SIGTERM in production |
| **Zero frontend tests** | React app has no test coverage |
| **Missing GLM dep** | `zhipuai` import in `llm_router.py` not in any requirements file |
| **Dead code** | `write_headline_debug()`, unused CORS env var, duplicate imports in main.py |
| **`load_dotenv()` guard** | `ENVIRONMENT != 'test'` check but env var never set to `test` |
| **Market Intelligence hardcoded values** | `mediaBias` has hardcoded 60/20/20 split, sector hardcoded as Technology |

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
8. **Market Intelligence endpoint** — deep ticker analysis with narrative breakdown, exhaustion detection, and ranking

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
12. Add integration tests for all API endpoints, especially new Market Intelligence endpoints

### Long-Term (Infrastructure)
13. Replace blocking operations with async task queue (Celery + Redis)
14. Implement proper connection pool lifecycle management (graceful shutdown via signals)
15. Add API key authentication for external API access
16. Consolidate hardcoded values into centralized configuration
17. Extract all LLM-related code behind a clean interface for easier provider swapping

---

## 9. Repository Statistics

| Metric | Value |
|--------|-------|
| Python modules | ~40 |
| SQL migration files | 6 |
| TypeScript/React components | ~20 |
| API endpoints | 14+ |
| Database tables | 10 |
| Automated tests | 13 |
| Git commits | 90+ |
| LLM providers supported | 4 |
| News sources ingested | 6 |
| Tracked assets (Layer 1) | 5 |
| API tracked assets | 10 (NVDA, AAPL, MSFT, TSLA, GOOGL, META, AMD, AMZN, JPM, KO) |
| External Python dependencies | 8 |
| NDI regimes (core L4) | 4 |
| NDI regimes (API) | 7 |
| NDI regimes (frontend) | 7 |
| Estimated hardcoded values | ~120 |

---

## 10. Conclusion

SignalIQ is a functionally complete, production-deployed market intelligence system with a well-architected 6-layer design. The core analytics pipeline (Layers 3–4) demonstrates sophisticated design in its stdlib-only approach, two-phase commit for look-ahead bias prevention, and inverted-U confidence modeling.

Recent development has focused on the Market Intelligence feature — a deep ticker analysis endpoint that combines NDI signals with narrative breakdown, exhaustion detection, and sector ranking. The API has been refactored with a proper `Config` class and improved logging.

However, significant technical debt remains: the triplicate NDI formula creates an architectural inconsistency that undermines analytical integrity, API keys and database credentials are exposed in git history (a critical security concern), test coverage is sparse outside of smoke tests, and there is a growing divergence between the core L4 regime model (4 regimes) and the live API (7 regimes with buy/sell recommendations).

The project would benefit most from: (1) immediate credential remediation, (2) NDI formula unification, (3) regime model reconciliation between core/API/frontend, and (4) expanded test coverage before adding new features.

---

*Report generated via static analysis of the SignalIQ repository at `/home/daniel/repo_lab/SignalIQ`.*
