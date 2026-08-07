# SignalIQ — Repository Analysis Report

> **Author:** Daniel Canedo (ML Engineer at Anyone AI, MSc. Economics — Yokohama National University)
> **Repository:** [github.com/danacioDS/SignalIQ](https://github.com/danacioDS/SignalIQ)
> **Generated:** August 7, 2026
> **Analyzed revision:** `feature/market_intelligence` @ `238a4f7` (Jul 23, 2026) — 1 commit ahead of `main`

---

## 1. Executive Summary

SignalIQ is a market intelligence framework that measures the divergence between market **narratives** (news sentiment) and **price action** (momentum) via the **Narrative Divergence Index (NDI)**:

```
NDI = (sentiment − momentum) × scale_factor
```

The project is production-deployed and **live**: the Vercel frontend (`signaliq-zeta-ten.vercel.app`) and the Flask API (`signaliq-api.onrender.com`, version 6.2) both return HTTP 200 and the API is serving real news sentiment (9 headlines observed for NVDA) with multi-source pricing.

**Key change since the July 10, 2026 report:** a large cleanup took place. The ~13 dead backend modules described previously are **gone**, and the core `layers/` + `config/` packages were moved from the repo root into `backend/app/`. The active branch is now `feature/market_intelligence` (development) with `main` reserved for production. This is a genuine improvement in code hygiene.

**However, the repository is in a *broken test* state:** running the documented test suite (`pytest tests/pytest/ -m "not integration"`) produces **4 failures out of 8 tests**. The frontend's single test suite also fails (cannot resolve `react-router-dom`), although `npm run build` succeeds cleanly. The documented production entrypoints (Docker `CMD` and `backend/render.yaml` `startCommand`) **fail to import** on a fresh checkout due to an absolute `from news_pipeline import ...` statement, and the stale root `main.py` references modules that no longer exist.

**Status:** Architecture is clean and lean; live production works; automated verification and entrypoint documentation have not kept pace with the cleanup.

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
│   ├── main.py                    # 400-line production API (multi-source prices + real news)
│   ├── api.py                     # 257-line alternative entry point (User-Agent rotation)
│   ├── news_pipeline.py           # 104-line TextBlob sentiment over 4 RSS feeds
│   ├── yahoo_proxy.py             # 15-line Blueprint — defined, never registered (dead)
│   ├── config/thresholds.py       # Centralized thresholds
│   ├── layers/                    # Layers 3, 4, 5 + LLM Router (18 modules, ~2,664 lines)
│   └── force_rebuild.txt          # Render deploy-hack marker
├── check_cache.py / preload_cache.py
├── main.py.back_up                # 1,323-line stale backup tracked in git
├── Dockerfile, render.yaml, requirements.txt, run.sh
```

### 2.2 Data Flow

Two paths remain, plus a new two-branch release flow:

1. **Core Pipeline (offline/batch):**
   `Layer 1 → Layer 2 (DB) → Layer 3 → Layer 4 → Layer 5 → signals`

2. **Live API Path (production):**
   `Price Sources (Alpha Vantage → Twelve Data → Yahoo Finance → Fallback) → Real News (TextBlob sentiment) → NDI `(sentiment - momentum) × 3` (clamped [-3, 3]) → 7-Regime Classification → JSON Response`
   *Operates independently of the database. This is a different methodology than core L4's rolling 20-day z-score approach — the known architectural inconsistency persists.*

3. **Release Flow (new since July):**
   `feature/market_intelligence (dev) → merge to main → auto-deploy Vercel frontend + Render API`

### 2.3 Live Production Verification (Aug 7, 2026)

| Endpoint | Result |
|----------|--------|
| `https://signaliq-zeta-ten.vercel.app` (frontend) | 200 OK |
| `https://signaliq-api.onrender.com/health` (API) | 200 OK — v6.2, mode `alpha_vantage_twelve_yahoo` |
| `https://signaliq-l8mi.onrender.com/health` | **404** — stale URL still referenced in `.env.development`, `setupProxy.js`, `render.yaml` CORS, and the previous report |

### 2.4 Tech Stack

| Component | Technology |
|-----------|------------|
| Backend (production) | Python 3.12, Flask 3.0, Flask-CORS, yfinance 0.2.36, numpy, requests, feedparser, TextBlob |
| Backend (declared deps) | Also pins flask-limiter, flask-talisman, redis, python-dotenv, python-json-logger — **several never imported** |
| Frontend | React 19.2, TypeScript 4.9, Recharts 3.8, Axios 1.17, React Router 7, CRA 5 |
| Database | PostgreSQL (4 schemas) — offline pipeline only |
| LLM | Google Gemini 2.5-flash, Groq (Llama 3.3-70B), GLM 4.7-flash |
| Data Sources | Yahoo Finance, Alpha Vantage, Twelve Data, Google News RSS, Yahoo Finance RSS, MarketWatch RSS |
| Infrastructure | Docker, Docker Compose, Vercel (frontend), Render (backend) |

---

## 3. Layer-by-Layer Analysis

### Layer 1 — Ingestion (`ingestion/`, 755 lines, 5 modules)

- **Modules:** `http_client.py`, `collect_prices.py`, `collect_news.py`, `writer.py`, `orchestrator.py`
- **Assets tracked:** NVDA, AAPL, MSFT, SPX, BTC-USD
- **Key patterns:** O_EXCL filesystem locks, SHA256 dedup, NFKC normalization, two-phase write for prices
- **Status:** Unchanged and healthy. Zero `sys.exit()` in library code (enforced by the one passing architecture test).

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

### Layer 6 — Frontend (`frontend/`, 39 TS files, 4,430 lines)

- **Builds cleanly** (`npm run build` succeeds).
- **Test fails:** the only test (`App.test.tsx`, render test) cannot resolve `react-router-dom` under react-scripts 5 / Jest.
- 16 components, 10 pages, 1 hook (`useSignalAnalysis`, 165 lines, 7 regimes, inverted-U confidence).
- **5 hardcoded API URLs** in source: `Dashboard.tsx` (`API_BASE`), `TickerAnalysis.tsx`, `ExpandedRow.tsx` ×2, `yahoo-finance-service.ts` — all point to `signaliq-api.onrender.com`, ignoring `REACT_APP_API_URL`.
- **Frontend references two endpoints that do not exist in the backend:** `/api/prices` and `/api/signals-intel` (used by `yahoo-finance-service.ts` and `ExpandedRow.tsx`). Those UI features will 404 against the current API.

### Flask API — Production (`backend/app/main.py`, 400 lines)

- **Endpoints:** `/` (v6.2), `/health`, `/api/ticker/<ticker>`, `/api/signals-live`, `/api/tickers`
- **Price cascade:** Alpha Vantage → Twelve Data → Yahoo Finance → `FALLBACK_PRICES`
- **NDI:** `(sentiment - momentum) * 3`, clamped to [-3.0, 3.0]; sentiment simulated from price change + volatility when no news
- **Caching:** thread-safe dict, TTL price=300s / history=600s / ticker=300s / signals=60s
- **CORS:** 6 origins (includes the now-404 `signaliq-l8mi.onrender.com`)
- **No auth, no rate limiting** (flask-limiter pinned but never applied), `logging.info` used for key events, `news_pipeline.py` still uses `print()` on lines 44 and 84.
- **Import fragility:** `from news_pipeline import process_news_for_ticker` is an absolute import. It only works when the process cwd or sys.path includes `backend/app` (e.g. `cd backend/app && python main.py`). The Docker `CMD` (`gunicorn app.main:app`) and `render.yaml` `startCommand` both fail on a fresh checkout — verified by import test. Local dev via `start.sh` works because running a script adds its directory to `sys.path`.

### Flask API — Alternative (`backend/app/api.py`, 257 lines)

- Nearly identical to `main.py` but with User-Agent rotation, exponential backoff, `/api/health` (both prefixes), and `/api/ticker/analysis/<ticker>`. No `/api/ticker/<ticker>` and no `/api/signals-live`. **Not wired to production.**

### Dead / Orphaned Files (current)

| File | Status |
|------|--------|
| `backend/app/yahoo_proxy.py` | Blueprint defined, never registered |
| `backend/main.py.back_up` | 1,323-line stale backup, tracked in git |
| `root main.py` | **Stale and broken** — imports `app.auth`, `app.db`, `app.market_intelligence` which no longer exist |
| `docker-compose.yml` | References missing `worker.py` and Redis services; stack will not start |
| `backend/check_cache.py`, `backend/preload_cache.py` | Utilities, unscripted |
| `backend/app/force_rebuild.txt` | Deploy-hack marker |
| `frontend/src/pages/Dashboard.tsx.backup_final` / `.backup_layout` | Tracked backups |
| `frontend/src/services/yahoo-finance-service.ts.bak4` | Tracked backup |
| `.gitignore` | Contains `api_*.py` pattern that would exclude legitimate future modules |

---

## 4. Development Methodology

- **Branch flow (new):** `main` = production (Vercel + Render auto-deploy); `feature/market_intelligence` = local dev, 1 commit ahead. Documented in `new_featrure.md`.
- **241 commits** on the current branch; last code change Jul 10 (NDI scale 3.0), last commit Jul 23 (docs only).
- **NDI sensitivity tuning:** scale factor went 1.0 → 1.5 → 2.0 → 2.5 → 3.0 (Jul 8–10). **No scale-factor changes since Jul 10** — stability for ~4 weeks, but still no automated guard.
- **Phase 0–6 methodology** in `workflow.md` remains the design reference.
- **Direct commits, no PR workflow**; one dedicated dev branch.

---

## 5. Testing

### Backend — `pytest tests/pytest/ -m "not integration" -v`

**Result: 4 passed, 4 failed** (verified Aug 7, 2026):

| Test | Type | Result | Cause |
|------|------|--------|-------|
| `test_import_layer4` | smoke | **FAIL** | `from layers.layer4_orchestrator import ...` → root `layers/` no longer exists (moved to `backend/app/layers/`) |
| `test_import_config` | smoke | **FAIL** | Same root `layers` path issue |
| `test_import_layer1` | smoke | PASS | `ingestion/` unchanged |
| `test_api_import` | smoke | **FAIL** | `backend.app.main` → `ModuleNotFoundError: news_pipeline` (absolute import not on sys.path) |
| `test_only_one_layer4_orchestrator` | architecture | **FAIL** | `os.walk('layers')` scans repo root — directory gone |
| `test_no_circular_imports` | architecture | PASS (stub) | Still just `pass` |
| `test_ndi_formula_consistency` | architecture | PASS | No `calculate_ndi` in `layers` paths found (trivially true — root `layers/` gone) |
| `test_no_sys_exit_in_libraries` | architecture | PASS | `ingestion/` + root `layers/` (latter empty → trivially true) |

**The architecture tests that do not crash are passing *vacuously*** — because they walk `layers` at the repo root, which no longer exists. The claim "8 tests pass" in the previous report is **no longer true**.

Integration tests (`test_db_contract.py`, `test_integration.py`, 5 tests) require DB/API and are skipped. Note `test_integration.py` still probes `/api/health` and `/api/stats`, but `main.py` serves `/health` and has no `/api/stats` — the integration contract is stale even for the live server.

### Frontend

- `npm run build` — **PASS** (clean compile).
- `npm test` — **FAIL**: 1 suite, 0 tests pass; Jest cannot resolve `react-router-dom` (react-scripts 5 / Jest 27 + React Router 7 incompatibility).

### What's NOT Tested (unchanged)
- Layer 3 logic, Layer 4 classification/persistence/measurement, LLM Router, fundamental engine, ingestion, news pipeline, production API logic (`calculate_ndi`, `classify_regime`, `get_price`), scripts, and the frontend beyond the broken render test.

---

## 6. Known Issues & Technical Debt

### Critical

| Issue | Details |
|-------|---------|
| **Test suite is red (4/8)** | The cleanup moved `layers/` and removed dead modules but did not update the tests. Every CI run fails immediately. |
| **Production entrypoint import is fragile/broken** | `from news_pipeline import ...` (main.py:17) fails under `gunicorn app.main:app` (Dockerfile + render.yaml) and `python -m app.main`. Only `cd backend/app && python main.py` (or `python app/main.py`) works. |
| **Stale root `main.py`** | Imports removed modules (`app.auth`, `app.db`, `app.market_intelligence`) — misleading and broken. |
| **`docker-compose.yml` cannot start** | References `worker.py` (missing), Redis, and a build context that no longer matches the app's import assumptions. |
| **Frontend references non-existent endpoints** | `/api/prices` and `/api/signals-intel` are called by `yahoo-finance-service.ts` and `ExpandedRow.tsx` but are absent from `main.py`/`api.py`. |

### High

| Issue | Details |
|-------|---------|
| **Triplicate NDI formula** | (1) core L4 `sentiment_zscore - momentum_zscore`, (2) production API `(sentiment - momentum) × 3` clamped [-3, 3], (3) frontend `useSignalAnalysis` confidence logic. Different values per layer. |
| **7 regimes (API/frontend) vs 4 regimes (core L4)** | Different thresholds and semantics. |
| **Two API hostnames in circulation** | `signaliq-api.onrender.com` (live) vs `signaliq-l8mi.onrender.com` (404). Live frontend uses the correct one, but dev config, setupProxy, CORS list, and docs reference the dead one. |
| **`signaliq-l8mi.onrender.com` in CORS + dev config** | Dead origin; harmless but misleading. |
| **No authentication, no rate limiting** | All endpoints public; flask-limiter pinned but never wired. |
| **No CI/CD** | No GitHub Actions; the failing suite is never caught automatically. |
| **`print()` in production path** | `news_pipeline.py` lines 44, 84. |
| **LLM default mismatch** | `llm_router.py` (`mock`) vs `system_config.py` (`glm`/`groq`). |
| **Frontend test suite red** | react-scripts 5 / React Router 7 resolution failure. |

### Medium

| Issue | Details |
|-------|---------|
| **Hardcoded API base in 5 frontend files** | `REACT_APP_API_URL` is effectively ignored in the components that matter. |
| **Backup/tracked cruft** | `backend/main.py.back_up` (1.3k lines), `Dashboard.tsx.backup_*` ×2, `yahoo-finance-service.ts.bak4`, `force_rebuild.txt`. |
| **Mixed language (ES/EN)** | Comments, logs, error messages, and API fields mix Spanish and English. |
| **Duplicate API entry points** | `main.py` vs `api.py` with diverging routes. |
| **`test_no_circular_imports` is a stub** | `pass`. |
| **Architecture tests walk stale paths** | `os.walk('layers')` / `os.walk('ingestion')` relative to cwd — break depending on where pytest runs. |
| **Integration test contract stale** | `/api/health` and `/api/stats` do not match `main.py` routes. |
| **Hardcoded values** | ~120 remain (tickers, fallback prices, thresholds, sector maps). |
| **Simulated price fallback** | Random-walk history when all APIs fail could mislead users. |
| **`.gitignore` anti-pattern** | `api_*.py` pattern may exclude legitimate modules. |

### Security (verified)
- `.env` is **not** tracked; only `.env.example` / `.env.template` with placeholders. A grep for real key patterns (`sk-`, `AIza…`, `ghp_…`, live `postgres://` creds) found **no live secrets** in tracked files. The credential exposure reported on Jul 10 appears remediated on the current history.

---

## 7. Strengths

1. **Dead-code cleanup executed** — `backend/app` went from ~16 modules (13 unused) to 5 active modules + a self-contained `layers/` package. Major hygiene win.
2. **Production is genuinely live** — frontend and API respond 200 with real news sentiment and multi-source prices (verified).
3. **Clean 6-layer separation** with each layer independently replaceable.
4. **Stdlib-only core analytics** (Layers 3–4) — stability and portability.
5. **Sophisticated patterns intact:** two-phase commit (no look-ahead bias), inverted-U confidence, O_EXCL locks, singletons, idempotent DDL.
6. **Frontend builds cleanly** with a modern stack (React 19, Recharts 3.8, Router 7).
7. **Branch-based release flow** (`main` = prod, `feature/*` = dev) — proper isolation of experiments.
8. **NDI scale factor stable** for 4 weeks (no drift since Jul 10).
9. **No live secrets in tracked files** — security posture improved.
10. **Multi-source price cascade + real RSS news** with a safe fallback chain.

---

## 8. Recommendations

### Immediate (must fix)
1. **Fix the test suite** — point tests at `backend/app/layers` (or re-create root shims), fix `test_api_import` by making the `news_pipeline` import robust (relative import or package-relative resolution).
2. **Fix the production entrypoint** — make `main.py` importable as `app.main` (e.g. `from .news_pipeline import ...` + a `backend/app/__init__.py` sys.path bootstrap, or run gunicorn with `--chdir app`).
3. **Delete or repair root `main.py`** — it references modules that no longer exist.
4. **Remove tracked backups and cruft** (`main.py.back_up`, `Dashboard.tsx.backup_*`, `.bak4`, `force_rebuild.txt`).
5. **Fix or delete `docker-compose.yml`** — `worker.py` does not exist.

### Short-Term (quality)
6. **Reconcile frontend API calls with backend routes** — add `/api/prices` and `/api/signals-intel` to the API or remove the frontend usage.
7. **Consolidate the API base URL** to a single `REACT_APP_API_URL`; drop `signaliq-l8mi.onrender.com` from dev config, setupProxy, and CORS.
8. **Fix the frontend test** — pin a compatible React Router version or upgrade Jest/config.
9. **Add GitHub Actions CI** running the (fixed) pytest suite + `npm run build`.
10. **Replace `print()` with logging** in `news_pipeline.py`.

### Medium-Term (consistency)
11. **Unify NDI formula** across core L4, API, and frontend; freeze scale factor with a unit test.
12. **Reconcile regime models** (4 vs 7).
13. **Apply rate limiting and optional API-key auth** using the already-pinned flask-limiter.
14. **Wire or remove `yahoo_proxy.py`**.
15. **Add tests** for production API logic (`calculate_ndi`, `classify_regime`, `get_price`, news pipeline).

### Long-Term (infrastructure)
16. Decide architecture direction: database-backed API vs pure yfinance serverless vs hybrid.
17. Add Redis or persistent cache if the yfinance-only route is kept.
18. Centralize remaining hardcoded values; add ruff + type hints.
19. Update integration tests to match real routes (`/health`, `/api/signals-live`).

---

## 9. Repository Statistics (current)

| Metric | Value |
|--------|-------|
| Active backend API modules (`app/`) | 4 (main 400, api 257, news_pipeline 104, yahoo_proxy 15) |
| Core layers under `backend/app/layers/` | 18 modules (incl. fundamental 4), ~2,664 lines |
| Ingestion modules | 5 (755 lines) |
| Scripts | 15 (1,560 lines) |
| SQL migrations | 6 (267 lines) |
| Frontend TS/TSX files | 39 (4,430 lines) — 16 components, 10 pages, 1 hook |
| Backend smoke/architecture tests | 8 (**4 fail**, 4 pass, 2 vacuous) |
| Integration tests | 5 (skipped; contract stale) |
| Frontend test suites | 1 (**fails**) |
| Frontend build | PASS |
| Git commits (branch) | 241; `feature/market_intelligence` 1 ahead of `main` |
| API endpoints (production) | 5 |
| Database tables / schemas / triggers | 10 / 4 / 6 |
| LLM providers | 4 |
| Live news sources (API) | 3 (Google News ×2 queries, Yahoo Finance, MarketWatch) |
| Price sources (API cascade) | 3 + fallback |
| API tracked assets | 10 (NVDA, AAPL, MSFT, TSLA, GOOGL, META, AMD, AMZN, JPM, KO) |
| NDI regimes (core L4 / API / frontend) | 4 / 7 / 7 |
| NDI scale factor | 3.0 (stable since Jul 10) |
| Live API version | 6.2 |
| Live frontend / API URLs | `signaliq-zeta-ten.vercel.app` / `signaliq-api.onrender.com` (both 200) |
| Dead URL still referenced | `signaliq-l8mi.onrender.com` (404) |

---

## 10. Conclusion

SignalIQ's architecture is in its **best structural state yet**: the dead-code purge and consolidation of the analytics layers under `backend/app/layers/` produced a lean, coherent codebase, and production is verifiably live on `signaliq-api.onrender.com` with real news sentiment and multi-source pricing.

The critical gap is **verification and entrypoint hygiene**. The documented test suite fails 4 of 8 tests, the architecture tests are partially passing vacuously, the frontend test cannot run, the Docker/`render.yaml` entrypoints fail on a fresh checkout, and stale artifacts (root `main.py`, `docker-compose.yml`, backups, dead hostnames) contradict the live deployment.

The highest-impact next steps, in order:
1. Fix the test suite and entrypoint imports so CI can be green.
2. Delete stale artifacts and reconcile the two backend hostnames.
3. Add CI so this cleanup doesn't regress.
4. Then pursue the longer-standing items: NDI unification, regime reconciliation, auth + rate limiting, and expanded unit coverage.

The project is one focused cleanup sprint away from a fully green, CI-verified, production-accurate repository.

---

*Report generated via static analysis + live endpoint verification of the SignalIQ repository at `/home/daniel/repo_lab/SignalIQ` (revision `238a4f7`).*
