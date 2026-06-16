## ✅ **README COMPLETO Y PRÁCTICO**

# SignalIQ

> Where market narratives meet market reality.

SignalIQ is a market intelligence framework that measures the distance between what the market is *saying* (news sentiment) and what the market is *actually doing* (price momentum). It quantifies this gap using the **Narrative Divergence Index (NDI)**:

```
NDI = sentiment_zscore − momentum_zscore
```

---

## 🚀 **Live Demo**

**Production Dashboard:** [https://signaliq-zeta.vercel.app](https://signaliq-zeta.vercel.app)

The dashboard shows real-time signals for major tickers with:
- NDI values and regime classification (Overheating, Watching, Aligned)
- Interactive ticker analyzer
- Sector performance visualization
- Economic foundation and methodology sections

---

## ⚡ **Quick Start**

### 1. Clone the repository

```bash
git clone https://github.com/danacioDS/SignalIQ.git
cd SignalIQ
```

### 2. Set up Python environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements_layer1.txt
```

### 3. Start the local frontend

```bash
cd frontend
npm install
npm start
```

**Dashboard will open at:** `http://localhost:3001`

### 4. (Optional) Start the backend API

```bash
cd backend
cp .env.example .env   # edit with your DATABASE_URL
python app/main.py
```

**API will be available at:** `http://localhost:10000`

---

## 🚀 **Easy Deploy**

### Deploy Frontend to Vercel

```bash
cd frontend
npm run build
CI=false vercel --prod --force
```

**When prompted:**
- Which team? → `Daniel Canedo's projects`
- Link to existing project? → `yes`
- Which project? → `signaliq`
- Environment variables? → `no`

### Deploy Backend to Render

1. Go to: https://dashboard.render.com
2. Select service `signaliq-api`
3. Manual Deploy → Deploy latest commit

### Verify Deployment

```bash
# Frontend
curl -I https://signaliq-zeta.vercel.app

# Backend
curl https://signaliq-api.onrender.com/api/health
```

### One-Command Deploy

```bash
cd ~/repo_lab/SignalIQ && \
git add . && \
git commit -m "deploy: actualización" && \
git push origin main && \
cd frontend && \
npm run build && \
CI=false vercel --prod --force
```

---

## 🔧 **Emergency Recovery - Stable Version**

### Restore from GitHub Tag

```bash
git checkout v2.0.0-stable
```

### Restore from Local Backup

```bash
cd ~/repo_lab
cp -r SignalIQ_backup_entrevista SignalIQ
```

### Create New Backup

```bash
cd ~/repo_lab/SignalIQ && \
git tag -a v2.0.0-stable -m "Versión estable - $(date)" && \
git push origin v2.0.0-stable && \
cd ~/repo_lab && \
cp -r SignalIQ SignalIQ_backup_$(date +%Y%m%d) && \
echo "✅ Backup completado"
```

---

## 📊 **System Overview**

| Layer | Description | Status |
|-------|-------------|--------|
| **1** | Data ingestion (Yahoo Finance + 6 RSS feeds) | Complete |
| **2** | PostgreSQL persistence | Complete |
| **3** | NLP intelligence (sentiment + momentum) | Complete |
| **4** | NDI signal generation | Complete |
| **5** | Fundamental analysis | Complete |
| **AI** | LLM Router (Gemini → Groq → GLM) | Complete |
| **6** | React TypeScript frontend | Complete |

---

## 🏗️ **Architecture**

```
┌───────────────────────────────┐
│    Frontend (React + TS)      │
│    Tailwind + Recharts        │
└───────────────┬───────────────┘
                │
┌───────────────▼───────────────┐
│       Flask API / Backend     │
│    (Gunicorn + Flask-Limiter) │
└───────────────┬───────────────┘
                │
        ┌───────┴────────┐
        │                │
┌───────▼──────┐  ┌──────▼──────┐
│   NDI Engine │  │  LLM Router │
│  (Layer 4)   │  │  (Multi-LLM)│
└───────┬──────┘  └──────┬──────┘
        │                │
        │        ┌───────┴───────┐
        │        │ Gemini │ Groq │
        │        │        GLM    │
        │        └───────┬───────┘
        │                │
┌───────▼────────────────▼───────┐
│    NLP + Entity Resolution     │
│   Sentiment (Loughran-McDonald)│
│   Momentum (20-day z-score)    │
└───────────────┬───────────────┘
                │
┌───────────────▼───────────────┐
│      PostgreSQL (Neon)        │
└───────────────┬───────────────┘
                │
┌───────────────▼───────────────┐
│    Data Ingestion Layer       │
│  Yahoo Finance (prices)       │
│  6 RSS feeds (news)           │
└───────────────────────────────┘
```

---

## 🔗 **Important Links**

| Resource | URL |
|----------|-----|
| **Production Dashboard** | [https://signaliq-zeta.vercel.app](https://signaliq-zeta.vercel.app) |
| **Backend API** | [https://signaliq-api.onrender.com](https://signaliq-api.onrender.com) |
| **Source Code** | [https://github.com/danacioDS/SignalIQ](https://github.com/danacioDS/SignalIQ) |
| **Stable Release** | `v2.0.0-stable` |

---

## 📋 **Configuration**

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | — | PostgreSQL connection string |
| `PRIMARY_LLM` | `mock` | LLM provider: `gemini`, `groq`, `glm` |
| `GEMINI_API_KEY` | — | Google Gemini API key |
| `FINNHUB_API_KEY` | — | Finnhub API key |

---

## 👨‍💻 **Author**

**Daniel Canedo**

- 🤖 ML Engineer at Anyone AI
- 🎓 MSc. Economics — Yokohama National University
- 📊 Economist — Universidad Católica Boliviana

---

## 📄 **License**

© 2026 SignalIQ · Intelligence Beyond Narratives
```

---

## 🚀 **GUARDAR EL README**

```bash
cd ~/repo_lab/SignalIQ
nano README.md
# (Pegar el contenido de arriba)
# Ctrl+O, Enter, Ctrl+X

git add README.md
git commit -m "docs: README completo con easy deploy y emergency recovery"
git push origin main
```