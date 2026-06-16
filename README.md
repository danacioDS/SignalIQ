Aquí tienes el **README.md actualizado** con todas las secciones que necesitas:

```markdown
# SignalIQ

> Where market narratives meet market reality.

SignalIQ is a market intelligence framework that measures the distance between what the market is *saying* (news sentiment) and what the market is *actually doing* (price momentum). It quantifies this gap using the **Narrative Divergence Index (NDI)**:

```
NDI = sentiment_zscore − momentum_zscore
```

When narrative runs ahead of price action, SignalIQ flags it as exhaustion, distribution, or severe divergence — not a prediction, but a systematic measurement of risk conditions.

---

## 🚀 Live Demo

**Production Dashboard:** [https://signaliq-zeta.vercel.app](https://signaliq-zeta.vercel.app)

The dashboard shows real-time signals for major tickers (NVDA, AAPL, MSFT, TSLA) with:
- NDI values and regime classification (Overheating, Watching, Aligned)
- Interactive ticker analyzer
- NDI historical evolution chart
- Economic foundation and methodology sections

---

## Quick Start

### Virtual environment (auto-activate)

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements_layer1.txt
```

**Auto-activate on `cd`** — add this to your `~/.bashrc` or `~/.zshrc`:

```bash
# Auto-activate venv when entering a directory with venv/
cd() {
    builtin cd "$@"
    if [ -f "$PWD/venv/bin/activate" ]; then
        source "$PWD/venv/bin/activate"
    fi
}
```

Or use [`direnv`](https://direnv.net/) (recommended):

```bash
echo 'layout python3' > .envrc && direnv allow
```

Or with a `.envrc` pointing to existing venv:

```bash
echo 'source venv/bin/activate' > .envrc && direnv allow
```

### Run

```bash
cp .env.example .env    # edit with your DATABASE_URL
python scripts/demo.py  # end-to-end synthetic demo (stdlib only, no DB needed)
python api_signaliq.py  # Flask API on port 5000
cd frontend && npm install && npm start  # React UI on http://localhost:3001
```

---

## Daily Commands

### Local Development

```bash
# 1. Navigate to project
cd ~/repo_lab/SignalIQ

# 2. Activate virtual environment
source venv/bin/activate

# 3. Check git status
git status

# 4. Start local dashboard
cd frontend && npm start
# Dashboard available at http://localhost:3001 (or next available port)
```

### Production Verification

```bash
# Check if production dashboard is live
curl -I https://signaliq-zeta.vercel.app

# Open dashboard in browser
open https://signaliq-zeta.vercel.app
```

### Deployment

```bash
# Deploy to Vercel (from frontend directory)
cd frontend
CI=false vercel --prod --force
```

### Switch Branches

```bash
# Production code
git checkout main

# Documentation (original plans, specs, theory)
git checkout docs
```

---

## System Overview

| Layer | Description | Status | Tests |
|-------|-------------|--------|-------|
| **1** | Data ingestion (Yahoo Finance OHLCV + 6 RSS feeds) | Complete | 15 tests, 61 checks |
| **2** | PostgreSQL persistence (10 tables, 13 functions, 6 triggers) | Complete | 24 SQL validation queries |
| **3** | NLP intelligence (entity resolution, Loughran-McDonald sentiment, momentum z-scores) | Complete | 16 tests, 100+ checks |
| **4** | NDI signal generation (measurement, persistence, classification, regimes) | Complete | 15 tests, 80+ checks |
| **5** | Fundamental analysis (valuation, growth, profitability scoring) | Complete | Smoke test |
| **AI** | LLM Router (Gemini, GLM, Groq) + Flask REST API | Complete | Mock tests |
| **6** | React TypeScript frontend + HTML institutional dashboards | Complete | — |

---

## Project Structure

```
├── backend/              # Flask API (port 10000) + DB pool
├── ingestion/            # Layer 1 — price & news ingestion
├── layers/               # Layers 3, 4 & 5 — NLP, signal, fundamental
├── sql/                  # Layer 2 — SQL migrations (6 files)
├── frontend/             # Layer 6 — React TypeScript UI
├── scripts/              # Cron, log rotation, backtesting, demo
├── web/                  # Standalone HTML dashboards
├── config/               # Thresholds + entity aliases
├── tests/pytest/         # Pytest suite (single source of truth)
├── docs/                 # Original project documentation (branch: docs)
└── logs/                 # Runtime logs (in .gitignore)
```

---

## Layers in Detail

### Layer 1 — Data Ingestion
```bash
python -m ingestion.orchestrator --type both
python -m ingestion.collect_prices --dry-run
python -m ingestion.collect_news --source reuters
```

### Layer 2 — PostgreSQL Persistence
```bash
psql $DATABASE_URL -f sql/master_build.sql
```

### Layer 3 — NLP Intelligence
Entity resolution (two-phase: URL param → alias regex), Loughran-McDonald sentiment, momentum z-scores (20-day rolling, two-phase commit prevents look-ahead bias).

### Layer 4 — NDI Signal Generation
4 sublayers: Measurement → Persistence → Classification → Orchestration. Output: ticker, date, ndi, regime, signal_state, confidence, risk_level, attention.

### Layer 5 — Fundamental Analysis
Valuation (P/E, P/B, P/S), growth (CAGR), profitability (margins, ROE), cash flow (FCF yield), health (D/E). Sector-benchmarked 0–100 score.

### AI / LLM Layer
Multi-provider LLM Router: Gemini, GLM (ZhipuAI), Groq, MOCK. Flask API at port 5000.

### Layer 6 — Frontend
React TypeScript (Recharts, Axios, Tailwind) dashboard deployed on Vercel.

---

## Testing

```bash
# Pytest (no network or DB needed)
pytest tests/pytest/ -m "not integration" -v

# Integration tests (requires DB or API running)
pytest tests/pytest/ -m integration -v
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

## Deployment

### Frontend (Vercel)
- **Production URL:** [https://signaliq-zeta.vercel.app](https://signaliq-zeta.vercel.app)
- **Deployment:** Automatic from `main` branch

### Backend (Render)
- **API URL:** `https://signaliq.onrender.com`
- **Deployment:** Automatic from `main` branch

---

## Branches

| Branch | Purpose | URL |
|--------|---------|-----|
| `main` | Production code (dashboard + backend) | [https://github.com/danacioDS/SignalIQ/tree/main](https://github.com/danacioDS/SignalIQ/tree/main) |
| `docs` | Original documentation (plans, specs, theory) | [https://github.com/danacioDS/SignalIQ/tree/docs](https://github.com/danacioDS/SignalIQ/tree/docs) |

---

## Core Idea

Markets are driven by stories as much as by numbers. Stories are created, spread, overheat, and exhaust themselves. Numbers (prices, volatility, volume) are slower and heavier. SignalIQ measures the distance between the hot (narrative) and the cold (prices). When that distance becomes abnormal, SignalIQ reports it.

---

## License

© 2026 SignalIQ · Intelligence Beyond Narratives
```

---

## 📋 **CÓMO ACTUALIZAR EL README EN GITHUB**

```bash
cd ~/repo_lab/SignalIQ

# 1. Reemplazar el README con el contenido de arriba
nano README.md
# (Pegar el contenido, Ctrl+O, Enter, Ctrl+X)

# 2. Commit y push
git add README.md
git commit -m "docs: actualizar README con secciones de daily commands y deployment"
git push origin main
```

---

## ✅ **CAMBIOS PRINCIPALES**

| Sección | Cambio |
|---------|--------|
| **Live Demo** | ✅ Agregado link al dashboard en producción |
| **Daily Commands** | ✅ Nueva sección con comandos de uso diario |
| **Layer 6** | ✅ Cambiado de "Partial" a "Complete" |
| **Deployment** | ✅ Nueva sección con URLs de Vercel y Render |
| **Branches** | ✅ Nueva sección explicando `main` vs `docs` |

---

**¿Quieres que ajuste algo más del README?** 🚀