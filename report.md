# SignalIQ — Repository Analysis Report

> **Author:** Daniel Canedo (ML Engineer at Anyone AI, MSc. Economics — Yokohama National University)
> **Repository:** [github.com/danacioDS/SignalIQ](https://github.com/danacioDS/SignalIQ)
> **Generated:** August 7, 2026
> **Analyzed revision:** `main` @ `130a686` (Aug 7, 2026) — 1 commit ahead of `origin/main`

---

## 1. Executive Summary

SignalIQ is a market intelligence framework that measures the divergence between market **narratives** (news sentiment) and **price action** (momentum) via the **Narrative Divergence Index (NDI)**:

```
NDI = (sentiment − momentum) × scale_factor
```

The project is production-deployed and **live**: the Vercel frontend (`signaliq-zeta-ten.vercel.app`) and the Flask API (`signaliq-api.onrender.com`, version 6.2) both return HTTP 200.

**Key change since the August 7 (revision `238a4f7`) report:** an 8-commit stabilization sprint landed directly on `main` the same day (Día 1–5, Aug 7, 2026):

- **Día 1 (estabilización):** deleted stale root files, made the `news_pipeline` import robust (relative → absolute fallback), added `logging_config.py`, labeled simulated data.
- **Día 2 (entrypoints):** `backend/Dockerfile` and `render.yaml` now run `python -m app.main` — the **fresh-checkout entrypoint bug is fixed and verified working**.
- **Día 3 (tests + CI):** `tests/pytest/test_smoke.py` and `test_architecture.py` rewritten; GitHub Actions CI added (`.github/workflows/ci.yml`: backend matrix 3.11/3.12, frontend build+test, ruff lint).
- **Día 4 (endpoints):** added `/api/prices` and `/api/signals-intel` to `main.py`; added `frontend/src/config/api.ts` to centralize API URLs.
- **Día 5 (security):** **flask-limiter is now actually applied** (default `200 per day` + `50 per hour`, per-endpoint 10–30/min); optional `API_KEY` auth decorator added (commented out); `.env.example` rewritten.
- Cleanup: `docker-compose.yml`, stale root `main.py`, `backend/main.py.back_up`, `Dashboard.tsx.backup_*`, `yahoo-finance-service.ts.bak4`, and `force_rebuild.txt` were **deleted**.

**However, the sprint introduced critical regressions and the verification claims do not hold on a fresh checkout:**

1. **Backend tests are still red — 4 of 8 fail**, now for *new* reasons (orchestrator count, missing `domain` module, undefined `get_ticker_data`).
2. **`main.py` contains undefined-function bugs (verified at runtime):** `/api/signals-intel` → **500 NameError `get_ticker_data`**, and the simulated-history path → **NameError `get_current_price`**. The cache stores a `float` but callers unpack a `(price, source)` tuple → "cannot unpack" errors on cache hits. `calculate_ndi` treats the dict returned by `get_price_history()` as a list → **every `/api/ticker` request falls through to minimal fallback data** (live response shows `news_count: 0`, `ndi: 0.0`, fallback price).
3. **The Día 4 frontend refactor broke the API calls:** in `ExpandedRow.tsx`, `TickerAnalysis.tsx`, and `yahoo-finance-service.ts` the constant `API_ENDPOINTS.*` was pasted **inside template literals without `${}`** — the app now requests literal URLs like `API_ENDPOINTS.signals?ticker=NVDA` (and `TickerAnalysis.tsx` has an unmatched `(`). These were previously-working hardcoded URLs.
4. **The live deployment lags the code:** the deployed API **404s** on the new `/api/prices` and `/api/signals-intel`, and the local repo is 1 commit ahead of `origin/main` (the Render auto-deploy pulls `main`). Frontend features built on those endpoints are broken in production.
5. **`feature/market_intelligence` was abandoned mid-flight:** the Día 1–5 work went straight to `main`; the dev branch is 2 commits behind and no longer the integration point.

**Status:** the sprint fixed the entrypoints, added CI, and applied rate limiting, but the codebase is now **red on CI, with new runtime bugs in the production API and a broken frontend fetch layer**. Live production still responds, but with degraded (fallback) data.

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

All layers now live under `backend/`:

```
backend/
├── app/
│   ├── main.py                    # 514-line production API (7 endpoints, rate-limited)
│   ├── api.py                     # 257-line alternative entry point (User-Agent rotation)
│   ├── news_pipeline.py           # 104-line TextBlob sentiment over 4 RSS feeds
│   ├── yahoo_proxy.py             # 14-line Blueprint — defined, never registered (dead)
│   ├── logging_config.py          # 65-line structured logging — NOT imported (dead, missing `import os`)
│   ├── config/thresholds.py       # Centralized thresholds
│   ├── layers/                    # Layers 3, 4, 5 + LLM Router (18 modules, ~2,664 lines)
│   └── main.py.pre_logging        # 400-line tracked backup of pre-logging main.py
├── Dockerfile, render.yaml, requirements.txt, run.sh
```

### 2.2 Data Flow

Three paths remain:

1. **Core Pipeline (offline/batch):**
   `Layer 1 → Layer 2 (DB) → Layer 3 → Layer 4 → Layer 5 → signals`

2. **Live API Path (production):**
   `Price Sources (Alpha Vantage → Twelve Data → Yahoo Finance → Fallback) → Real News (TextBlob sentiment) → NDI `(sentiment - momentum) × 3` (clamped [-3, 3]) → 7-Regime Classification → JSON Response`
   *Operates independently of the database. This is a different methodology than core L4's rolling 20-day z-score approach — the known architectural inconsistency persists.*

3. **Release Flow:**
   `main → auto-deploy Vercel frontend + Render API` *(the `feature/market_intelligence` dev branch is now stale)*

### 2.3 Live Production Verification (Aug 7, 2026)

| Endpoint | Result |
|----------|--------|
| `https://signaliq-zeta-ten.vercel.app` (frontend) | 200 OK |
| `https://signaliq-api.onrender.com/` (API root) | 200 OK — v6.2 |
| `https://signaliq-api.onrender.com/health` (API) | 200 OK — `alpha_vantage_twelve_yahoo` |
| `https://signaliq-api.onrender.com/api/ticker/NVDA` | 200 OK — **degraded**: `news_count: 0`, `ndi: 0.0`, fallback price `850.10` |
| `https://signaliq-api.onrender.com/api/prices` | **404** — endpoint not present in the deployed build |
| `https://signaliq-api.onrender.com/api/signals-intel` | **404** — endpoint not present in the deployed build |
| `https://signaliq-l8mi.onrender.com/health` (legacy) | **404** — still referenced in `frontend/.env.development` |

### 2.4 Tech Stack

| Component | Technology |
|-----------|------------|
| Backend (production) | Python 3.12, Flask 3.0, Flask-CORS, flask-limiter 3.5 (**now applied**), yfinance 0.2.36, numpy, requests, feedparser, TextBlob |
| Backend (declared deps) | Also pins flask-talisman, redis, python-dotenv, python-json-logger — **never imported** |
| Frontend | React 19.2, TypeScript 4.9, Recharts 3.8, Axios 1.17, React Router 7, CRA 5 |
| Database | PostgreSQL (4 schemas) — offline pipeline only |
| LLM | Google Gemini 2.5-flash, Groq (Llama 3.3-70B), GLM 4.7-flash |
| Data Sources | Yahoo Finance, Alpha Vantage, Twelve Data, Google News RSS, Yahoo Finance RSS, MarketWatch RSS |
| Infrastructure | Docker, Vercel (frontend), Render (backend), GitHub Actions (CI — added, currently red) |

---

## 3. Layer-by-Layer Analysis

### Layer 1 — Ingestion (`ingestion/`, 755 lines, 5 modules)

- **Modules:** `http_client.py`, `collect_prices.py`, `collect_news.py`, `writer.py`, `orchestrator.py`
- **Assets tracked:** NVDA, AAPL, MSFT, SPX, BTC-USD
- **Key patterns:** O_EXCL filesystem locks, SHA256 dedup, NFKC normalization, two-phase write for prices
- **Status:** Unchanged and healthy. Zero `sys.exit()` in library code (enforced by the passing architecture test).

### Layer 2 — Database (`sql/`, 267 lines, 6 migrations)

- `001_create_layer2_schema.sql`, `002_fix_schema.sql`, `003_create_signal_tables.sql`, `master_build.sql`, `rollback.sql`, `test_queries.sql`
- 10 tables, 2 views, 13 functions, 6 triggers, 4 schemas
- Idempotent DDL throughout. Used by the offline pipeline only — production API has no DB dependency.

### Layer 3 — NLP Intelligence (`backend/app/layers/`)

- `lm_lexicon.py` (558 Loughran-McDonald words, 6 categories), `layer3_entity.py`, `layer3_sentiment.py`, `layer3_momentum.py`, `layer3_orchestrator.py`, `layer3_config.py`
- Stdlib-only; two-phase commit prevents look-ahead bias; rolling 20-day window, min 10 valid days.

### Layer 4 — Signal Generation (`backend/app/layers/`)

- `layer4_measurement.py`, `layer4_persistence.py`, `layer4_classification.py`, `layer4_orchestrator.py`, `integration.py`
- 12-field output schema; 4 academic regimes; 3 signal states; inverted-U confidence.
- `layer4_orchestrator.py` still imports `layers.llm_router` at module load — meaning **the core L4 pipeline requires `dotenv` and any configured LLM keys to even import**.

#### Regime Classification (Core L4 — 4 regimes)

| Regime | NDI Range | Description |
|--------|-----------|-------------|
| ALIGNED | \|NDI\| < 1.5 | Narrative matches price action |
| ACCUMULATION_DIVERGENCE | NDI < -1.5 | Price stronger than narrative |
| OVERHEATING_DIVERGENCE | NDI > 1.5 | Narrative stronger than price |
| INSUFFICIENT_DATA | < 2 valid points | Not enough data |

#### Regime Classification (Production API + Frontend — 7 regimes)

| Regime | NDI Range | Recommendation |
|--------|-----------|---------------|
| EXTREME OVERHEATING | NDI > 2.0 | SELL |
| OVERHEATING | 1.5 < NDI ≤ 2.0 | REDUCE |
| WATCHING | 0.5 < NDI ≤ 1.5 | MONITOR |
| NEUTRAL / STABLE | -0.5 < NDI ≤ 0.5 | HOLD |
| ALIGNED | -1.5 < NDI ≤ -0.5 | BUY |
| STRONG UNDERVALUED | -2.0 < NDI ≤ -1.5 | STRONG BUY |
| CAPITULATION / EXTREME UNDERVALUED | NDI ≤ -2.0 | ACCUMULATE |

*Frontend labels differ slightly from API keys (STABLE vs NEUTRAL, EXTREME_UNDERVALUED vs CAPITULATION).*

### Layer 5 — Fundamental Analysis (`backend/app/layers/fundamental/`)

- `metrics_calculator.py`, `score_aggregator.py`, `fundamental_engine.py` (+ `__init__.py`)
- numpy dependency; sector-benchmarked 0–100 scoring; NDI risk adjustment.

### LLM Router (`backend/app/layers/llm_router.py`)

- Singleton, 4 providers (Gemini / GLM / Groq / MOCK), fallback chain `PRIMARY_LLM → FALLBACK_LLM → MOCK`.
- **Default mismatch persists:** `llm_router.py` defaults both to `"mock"`; `system_config.py` defaults `PRIMARY_LLM="glm"`, `FALLBACK_LLM="groq"`.

### Layer 6 — Frontend (`frontend/`, 37 TS/TSX files)

- **Builds cleanly** (`npm run build` succeeds — verified Aug 7, 2026).
- **Test fails:** the only test (`App.test.tsx`, render test) cannot resolve `react-router-dom` under react-scripts 5 / Jest (`Cannot find module 'react-router/dom'`).
- 15 components, 9 pages, 1 hook (`useSignalAnalysis`, 165 lines, 7 regimes, inverted-U confidence).
- **NEW: `src/config/api.ts`** centralizes `API_BASE` / `API_ENDPOINTS` / `DEFAULT_TICKERS`; `Dashboard.tsx` now imports from it correctly.
- **Regression (Día 4):** three fetch sites paste `API_ENDPOINTS.*` **inside template literals without `${}`**, producing literal-string URLs:
  - `components/ExpandedRow.tsx:45` — `` fetch(`API_ENDPOINTS.signals?ticker=${ticker}`) ``
  - `components/TickerAnalysis.tsx:24` — `` fetch(`API_ENDPOINTS.ticker(${ticker}`) `` (also missing closing `)`)
  - `services/yahoo-finance-service.ts:38` — `` const url = `API_ENDPOINTS.prices/${ticker}` ``
- `yahoo-finance-service.ts` requests `/api/prices/<ticker>` (per-ticker), but the backend only exposes `/api/prices` (all tickers) — no per-ticker route exists.
- `.env.production` → `signaliq-api.onrender.com` (correct); **`.env.development` → `signaliq-l8mi.onrender.com` (dead)**; `setupProxy.js` now targets `signaliq-api.onrender.com` (fixed).

### Flask API — Production (`backend/app/main.py`, 514 lines)

- **Endpoints (7):** `/` (v6.2), `/health`, `/api/ticker/<ticker>`, `/api/signals-live`, `/api/tickers`, `/api/prices` (NEW), `/api/signals-intel` (NEW).
- **Price cascade:** Alpha Vantage → Twelve Data → Yahoo Finance → `FALLBACK_PRICES`.
- **NDI:** `(sentiment - momentum) * 3`, clamped to [-3.0, 3.0]; sentiment simulated from price change + volatility when no news.
- **Caching:** thread-safe dict, TTL price=300s / history=600s / ticker=300s / signals=60s.
- **Rate limiting (NEW — applied):** `Limiter(key_func=get_remote_address)`; default limits `200 per day` + `50 per hour`; per-endpoint `10 per minute` (ticker), `20 per minute` (signals-live, signals-intel), `30 per minute` (tickers, prices). **In-memory storage** (not Redis) — a warning is emitted at startup.
- **Auth (NEW — not enabled):** optional `API_KEY` env + `require_api_key` decorator; the only usage is commented out.
- **Import robustness (fixed):** `from .news_pipeline import process_news_for_ticker` with `except ImportError → from news_pipeline import ...`. Verified working: `python -m app.main` (Docker + render.yaml), `cd backend/app && python main.py`, `cd backend && python app/main.py`. Gunicorn is no longer in `requirements.txt` (entrypoint is `python -m app.main`).

**Critical runtime bugs (verified with the Flask test client, Aug 7, 2026):**

| # | Bug | Location | Impact |
|---|-----|----------|--------|
| 1 | `get_ticker_data` is **not defined** | `main.py:468, 479` (`/api/signals-intel`) | Endpoint returns **500 NameError** |
| 2 | `get_current_price` is **not defined** | `main.py:163` (`get_price_history` simulation branch) | NameError whenever real history is unavailable |
| 3 | `get_price()` caches a **float** but returns `(price, source)` | `main.py:80-126` | Cache hits break tuple unpacking → "cannot unpack non-iterable float object" in `/api/prices` and `/api/ticker` |
| 4 | `calculate_ndi` treats the **dict** from `get_price_history()` as a list | `main.py:212-265` (`len(history)`, `history[-1]`, `history[-20:]` on dict keys) | Every `/api/ticker` call raises and falls back to minimal data (`news_count: 0`, `ndi: 0.0`) |
| 5 | All price sources labeled `"alphavantage"` | `main.py:108, 119, 126` | Twelve Data / Yahoo / fallback misreported |
| 6 | CORS origin duplicated | `main.py:345-346` | `signaliq-api.onrender.com` listed twice (5 unique origins) |
| 7 | `flask_limiter` imported twice | `main.py:11-12, 27-28` | Dead import |
| 8 | Version mismatch | root reports `6.2`, startup log prints `v6.1` | Cosmetic |

**CORS:** 6 list entries but only **5 unique origins** (duplicate `signaliq-api.onrender.com`). The legacy host is no longer in the list.

**`logging_config.py` (65 lines, new):** structured JSON logging helper — **never imported by any module**, and **broken** (uses `os.environ` without `import os` → `NameError` at import).

### Flask API — Alternative (`backend/app/api.py`, 257 lines)

- Nearly identical to `main.py` but with User-Agent rotation, exponential backoff, `/api/health` (both prefixes), and `/api/ticker/analysis/<ticker>`. No `/api/ticker/<ticker>`, `/api/signals-live`, `/api/prices`, or `/api/signals-intel`. **Not wired to production.** CORS updated to `signaliq-api.onrender.com`.

### Dead / Orphaned Files (current)

| File | Status |
|------|--------|
| `backend/app/yahoo_proxy.py` | Blueprint defined, never registered |
| `backend/app/logging_config.py` | Never imported; missing `import os` (would raise `NameError`) |
| `backend/app/main.py.pre_logging` | 400-line tracked backup |
| `backend/app/main.py.bak_final`, `backend/app/main.py.fixed` | **Untracked** scratch files (`main.py.fixed` is a 2-line placeholder) |
| `frontend/.env.development` | Points at dead `signaliq-l8mi.onrender.com` |
| `backend/check_cache.py`, `backend/preload_cache.py` | Utilities, unscripted |
| `news_pipeline.py` | Still uses `print()` on lines 44 and 84 |
| `.gitignore` | Contains `api_*.py` pattern that would exclude legitimate future modules |

**Removed since the previous report:** `docker-compose.yml` (broken, deleted), stale root `main.py` (deleted), `backend/main.py.back_up` (1,323 lines, deleted), `force_rebuild.txt` (deleted), `Dashboard.tsx.backup_final/.backup_layout` (deleted), `yahoo-finance-service.ts.bak4` (deleted).

---

## 4. Development Methodology

- **Branch flow changed:** the Día 1–5 sprint was committed **directly to `main`** (the docs' "`main` = prod, `feature/*` = dev" model no longer matches reality). `feature/market_intelligence` is 2 commits behind `main` and inactive. CI (GitHub Actions) is the new verification gate — but it is **red**.
- **249 commits** on `main`; last code change **Aug 7, 2026** (Día 1–5 sprint + bugfix). Local `main` is 1 commit ahead of `origin/main` (`130a686`).
- **NDI sensitivity tuning:** scale factor went 1.0 → 1.5 → 2.0 → 2.5 → 3.0 (Jul 8–10). **No scale-factor changes since Jul 10** — ~4 weeks of stability, still no automated guard.
- **Phase 0–6 methodology** in `workflow.md` remains the design reference.
- **Direct commits, no PR workflow;** CI added Aug 7.

---

## 5. Testing

### Backend — `pytest tests/pytest/ -m "not integration" -v`

**Result: 4 passed, 4 failed** (verified Aug 7, 2026 on a fresh local run):

| Test | Type | Result | Cause |
|------|------|--------|-------|
| `test_import_layer4` | smoke | **FAIL** | `ModuleNotFoundError: No module named 'dotenv'` (local venv lacks python-dotenv; CI installs it via `backend/requirements.txt`) |
| `test_import_config` | smoke | PASS | `config.thresholds.NDI_OVERHEATING == 1.5` |
| `test_import_news_pipeline` | smoke | PASS | Relative→absolute fallback works |
| `test_api_import` | smoke | **FAIL** | `assert hasattr(main, 'get_ticker_data')` — **`get_ticker_data` is not defined in `main.py`** |
| `test_only_one_layer4_orchestrator` | architecture | **FAIL** | Walks `backend/app/layers` and finds **2** orchestrators (`layer3_orchestrator.py`, `layer4_orchestrator.py`) — asserts `== 1` |
| `test_no_circular_imports` | architecture | PASS | Real AST import-cycle scan (no longer a stub); no self-imports |
| `test_ndi_formula_consistency` | architecture | **FAIL** | `ModuleNotFoundError: No module named 'domain'` — imports `domain.ndi_calculator`, which **does not exist** anywhere in the repo |
| `test_no_sys_exit_in_libraries` | architecture | PASS | Ingestion + layers scan |

**The test suite went from 4 fails (stale paths) to 4 fails (new causes).** The prior claim that the architecture tests passed "vacuously" is resolved — the rewritten tests now scan real paths — but they fail for the wrong reasons (`domain` module never existed; orchestrator count assertion is wrong; `get_ticker_data` assert is wrong).

**CI (`ci.yml`) — will be red:**
- `backend-tests` runs `cd backend && python -m pytest ../tests/pytest/ ...`. From the `backend` cwd, the architecture tests resolve relative paths as `backend/backend/app/layers` (doesn't exist) → `test_only_one_layer4_orchestrator` fails on the `os.path.exists` assert; `test_api_import` fails regardless.
- `frontend-tests`: `npm run build` PASS; `npm test -- --watchAll=false --passWithNoTests || true` — the failing suite is masked by `|| true`.
- `lint`: `ruff check backend/app --ignore=E501` — ruff is not pinned to a version and the codebase has unused/duplicate imports and bare `except`s; likely to fail.

Integration tests (`test_db_contract.py`, `test_integration.py`, 5 tests) require DB/API and are skipped. Note `test_integration.py` still probes `/api/health` and `/api/stats`, but `main.py` serves `/health` and has no `/api/stats` — the integration contract is stale even for the live server.

### Frontend

- `npm run build` — **PASS** (clean compile, verified).
- `npm test` — **FAIL**: 1 suite, 0 tests pass; Jest cannot resolve `react-router-dom` (react-scripts 5 / Jest 27 + React Router 7 incompatibility: `Cannot find module 'react-router/dom'`).

### What's NOT Tested (unchanged)
- Layer 3 logic, Layer 4 classification/persistence/measurement, LLM Router, fundamental engine, ingestion, news pipeline, production API logic (`calculate_ndi`, `classify_regime`, `get_price`), the new `/api/prices` + `/api/signals-intel` endpoints, `logging_config.py`, and the frontend beyond the broken render test.

---

## 6. Known Issues & Technical Debt

### Critical

| Issue | Details |
|-------|---------|
| **`/api/signals-intel` is broken (500)** | Calls undefined `get_ticker_data` (main.py:468, 479). Also: frontend `ExpandedRow.tsx` expects an `events`/`narrative` shape the endpoint was never built to return. |
| **`/api/ticker` always degrades to fallback data** | `calculate_ndi` treats the `get_price_history()` **dict** as a list (`len(history)`, `history[-1]`, `history[-20:]` on dict keys) → exception → minimal response. Live confirms: `news_count: 0`, `ndi: 0.0`, fallback price. |
| **Cache stores float, callers unpack tuple** | `get_price()` sets the cache to a `float` but returns `(price, source)` → "cannot unpack non-iterable float object" on cache hits in `/api/prices` and `/api/ticker`. |
| **Frontend fetch URLs broken by Día 4 refactor** | `API_ENDPOINTS.*` pasted inside template literals without `${}` in `ExpandedRow.tsx`, `TickerAnalysis.tsx` (also unmatched `(`), and `yahoo-finance-service.ts`. Requests go to literal strings like `API_ENDPOINTS.signals?ticker=NVDA`. |
| **Live API 404s on new endpoints** | Deployed `signaliq-api.onrender.com` lacks `/api/prices` and `/api/signals-intel` (repo is 1 commit ahead of `origin/main`; deployed build lags further). Frontend features using them fail in production. |
| **Test suite still red (4/8)** | New causes: missing `domain` module, orchestrator count, undefined `get_ticker_data`, local `dotenv` gap. CI is therefore red on push. |

### High

| Issue | Details |
|-------|---------|
| **Triplicate NDI formula** | (1) core L4 `sentiment_zscore - momentum_zscore`, (2) production API `(sentiment - momentum) × 3` clamped [-3, 3], (3) frontend `useSignalAnalysis` confidence logic. Different values per layer. |
| **7 regimes (API/frontend) vs 4 regimes (core L4)** | Different thresholds and semantics. |
| **All price sources reported as `"alphavantage"`** | Twelve Data, Yahoo, and fallback all hardcode the label `"alphavantage"` (main.py:108, 119, 126). |
| **Duplicate CORS origin + duplicate limiter import** | `signaliq-api.onrender.com` listed twice in CORS; `from flask_limiter import ...` twice. |
| **No authentication enabled** | `require_api_key` decorator exists but is commented out; all endpoints public. |
| **Rate limiting uses in-memory storage** | flask-limiter warns it is not recommended for production (no Redis wired). |
| **Legacy host in dev config** | `frontend/.env.development` → `signaliq-l8mi.onrender.com` (404). |
| **`logging_config.py` dead + broken** | Never imported; missing `import os` → `NameError`. |
| **Frontend test suite red** | react-scripts 5 / React Router 7 resolution failure. |
| **CI red** | Backend tests fail; lint unversioned; frontend test failure masked with `|| true`. |

### Medium

| Issue | Details |
|-------|---------|
| **`yahoo-finance-service` calls `/api/prices/<ticker>`** | Backend exposes `/api/prices` (all tickers) only — no per-ticker route. |
| **Version string mismatch** | Root says `6.2`, startup log says `v6.1`. |
| **Unused pinned deps** | redis, flask-talisman, python-json-logger never imported. |
| **Backup/tracked cruft** | `main.py.pre_logging` tracked; untracked `main.py.bak_final` + `main.py.fixed` (2-line placeholder). |
| **Mixed language (ES/EN)** | Comments, logs, error messages, and API fields mix Spanish and English. |
| **Duplicate API entry points** | `main.py` vs `api.py` with diverging routes. |
| **Integration test contract stale** | `/api/health` and `/api/stats` do not match `main.py` routes. |
| **Hardcoded values** | ~120 remain (tickers, fallback prices, thresholds, sector maps). |
| **Simulated price fallback** | Random-walk history when all APIs fail could mislead users. |
| **`.gitignore` anti-pattern** | `api_*.py` pattern may exclude legitimate modules. |
| **LLM default mismatch** | `llm_router.py` (`mock`) vs `system_config.py` (`glm`/`groq`). |
| **`print()` in production path** | `news_pipeline.py` lines 44, 84. |

### Security (verified)
- `.env` is **not** tracked; only `.env.example` / `.env.template` with placeholders. A grep for real key patterns (`sk-`, `AIza…`, `ghp_…`, live `postgres://` creds) found **no live secrets** in tracked files.
- New `API_KEY` variable documented in `.env.example`; auth path exists but is disabled by default.

---

## 7. Strengths

1. **Entrypoint bug fixed and verified** — `python -m app.main` works for Docker (`CMD`) and `render.yaml` (`startCommand`); the import is now relative-with-absolute-fallback.
2. **Rate limiting is now actually applied** — flask-limiter wired with default + per-endpoint limits (in-memory backend).
3. **CI added** — GitHub Actions with backend matrix, frontend build/test, and ruff lint (currently red, but the gate exists).
4. **Meaningful cleanup executed** — `docker-compose.yml`, stale root `main.py`, `main.py.back_up`, `Dashboard.tsx.backup_*`, `.bak4`, and `force_rebuild.txt` deleted.
5. **Frontend API config centralized** — `src/config/api.ts` + `Dashboard.tsx` uses it; `setupProxy.js` and `api.py` CORS updated to the live host.
6. **Production is genuinely live** — frontend and API respond 200 (though with degraded fallback data on the API).
7. **Clean 6-layer separation** with each layer independently replaceable.
8. **Stdlib-only core analytics** (Layers 3–4) — stability and portability.
9. **Frontend builds cleanly** with a modern stack (React 19, Recharts 3.8, Router 7).
10. **NDI scale factor stable** for 4 weeks (no drift since Jul 10); **no live secrets** in tracked files.

---

## 8. Recommendations

### Immediate (must fix)
1. **Fix the production API bugs** — (a) define `get_ticker_data` or remove `/api/signals-intel`; (b) define/fix `get_current_price` or the history-simulation branch; (c) cache the `(price, source)` tuple (or return the cached float as a tuple); (d) fix `calculate_ndi` to read `history['history']` instead of slicing the dict.
2. **Fix the frontend template literals** — wrap `API_ENDPOINTS.*` in `${...}` in `ExpandedRow.tsx`, `TickerAnalysis.tsx` (and add the missing `)`), and `yahoo-finance-service.ts`; align the prices service with the `/api/prices` (all-tickers) contract.
3. **Fix the test suite** — remove the nonexistent `domain` import in `test_ndi_formula_consistency` (or create the module); allow both `layer3_orchestrator.py` + `layer4_orchestrator.py` in `test_only_one_layer4_orchestrator`; drop the `get_ticker_data` assert (or define the function); ensure CI runs pytest from the repo root (not `backend`).
4. **Make CI green** — pin ruff, remove the `|| true` mask on the frontend test step, and fix the failing assertions.
5. **Push `130a686` and trigger a Render redeploy** so `/api/prices` + `/api/signals-intel` go live; verify against the deployed host.
6. **Remove residual cruft** — delete tracked `main.py.pre_logging` and untracked `main.py.bak_final` / `main.py.fixed`; update `frontend/.env.development` to `signaliq-api.onrender.com`.

### Short-Term (quality)
7. Fix duplicate CORS origin, duplicate `flask_limiter` imports, and the `"alphavantage"` source labels; align version strings.
8. Wire `logging_config.py` into `main.py` (and add the missing `import os`) or delete it.
9. Fix the frontend test (pin a compatible React Router version or upgrade Jest/config) so CI stops masking a known failure.
10. Replace `print()` with logging in `news_pipeline.py`.
11. Add tests for production API logic (`calculate_ndi`, `classify_regime`, `get_price`, new endpoints).

### Medium-Term (consistency)
12. Unify NDI formula across core L4, API, and frontend; freeze scale factor with a unit test.
13. Reconcile regime models (4 vs 7).
14. Move rate-limit storage to Redis; optionally enable API-key auth (decorator is ready).
15. Wire or remove `yahoo_proxy.py`.
16. Update integration tests to match real routes (`/health`, `/api/signals-live`, `/api/prices`, `/api/signals-intel`).

### Long-Term (infrastructure)
17. Decide architecture direction: database-backed API vs pure yfinance serverless vs hybrid.
18. Add Redis or persistent cache if the yfinance-only route is kept.
19. Centralize remaining hardcoded values; add ruff + type hints.

---

## 9. Repository Statistics (current)

| Metric | Value |
|--------|-------|
| Active backend API modules (`app/`) | 5 (main 514, api 257, news_pipeline 104, yahoo_proxy 14, logging_config 65) |
| Core layers under `backend/app/layers/` | 18 modules (incl. fundamental 4), ~2,664 lines |
| Ingestion modules | 5 (755 lines) |
| Scripts | 15 (1,600 lines) |
| SQL migrations | 6 (267 lines) |
| Frontend TS/TSX files | 37 — 15 components, 9 pages, 1 hook |
| Backend smoke/architecture tests | 8 (**4 fail**, 4 pass) |
| Integration tests | 5 (skipped; contract stale) |
| Frontend test suites | 1 (**fails**) |
| Frontend build | PASS |
| CI | Added (GitHub Actions, 3 jobs — **currently red**) |
| Git commits | 249 on `main`; `main` 1 ahead of `origin/main` |
| API endpoints (code / live) | 7 / 5 (`/api/prices` + `/api/signals-intel` 404 on live) |
| Rate limiting | **Applied** (flask-limiter, in-memory) |
| Authentication | Optional `API_KEY` (disabled) |
| Database tables / schemas / triggers | 10 / 4 / 6 |
| LLM providers | 4 |
| Live news sources (API) | 4 RSS (Google News ×2, Yahoo Finance, MarketWatch) |
| Price sources (API cascade) | 3 + fallback |
| API tracked assets | 10 (NVDA, AAPL, MSFT, TSLA, GOOGL, META, AMD, AMZN, JPM, KO) |
| NDI regimes (core L4 / API / frontend) | 4 / 7 / 7 |
| NDI scale factor | 3.0 (stable since Jul 10) |
| Live API version | 6.2 |
| Live frontend / API URLs | `signaliq-zeta-ten.vercel.app` / `signaliq-api.onrender.com` (both 200) |
| Dead URL still referenced | `signaliq-l8mi.onrender.com` (404, in `.env.development`) |

---

## 10. Conclusion

The Aug 7 stabilization sprint was a mixed result. On the positive side: the **production entrypoint is fixed and verified**, **rate limiting is finally applied**, **CI exists**, and a large batch of stale artifacts (broken compose file, stale root `main.py`, tracked backups) was deleted.

But the sprint **introduced critical regressions that are now live in the codebase**: the new `/api/signals-intel` endpoint 500s (undefined `get_ticker_data`), `/api/ticker` silently degrades to fallback data (dict-as-list bug), the cache/unpack mismatch breaks `/api/prices` on cache hits, and the frontend's `config/api.ts` refactor produced literal-string URLs in three fetch calls. The rewritten test suite still fails 4 of 8 (new causes), and CI is red — so none of this is caught automatically. Meanwhile the **deployed** API 404s on the two new endpoints, meaning the frontend features built for them are broken in production.

The highest-impact next steps, in order:
1. Fix the four `main.py` runtime bugs (undefined functions, cache tuple, dict/list mismatch) and redeploy to Render.
2. Fix the three frontend template-literal regressions.
3. Fix the test suite + CI so it is green and actually gates changes.
4. Then pursue the longer-standing items: NDI unification, regime reconciliation, Redis-backed rate limiting + auth, and expanded unit coverage.

The project is again one focused cleanup sprint away from a fully green, CI-verified, production-accurate repository — but the fixes must be verified by running the app, not by commit messages.

---

*Report generated via static analysis + live endpoint verification of the SignalIQ repository at `/home/daniel/repo_lab/SignalIQ` (revision `130a686`).*
