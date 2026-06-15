# SignalIQ Architecture

> **NDI = sentiment_zscore − momentum_zscore → deterministic classification → readable risk signal**

---

## System Purpose

SignalIQ measures divergence between market narrative (news sentiment) and market reality (price momentum). It does **not** predict prices. It measures risk conditions — exhaustion, distribution, and severe divergence — as systematic deviations between what the market is *saying* and what it is *doing*.

---

## Core Formula

```
NDI(t) = sentiment_zscore(t) − momentum_zscore(t)

sentiment_zscore  = (daily_sentiment − rolling_mean_20d) / rolling_std_20d
momentum_zscore   = (daily_return − rolling_mean_20d) / rolling_std_20d

daily_sentiment   = mean((pos_words − neg_words) / total_words)
                    across all headlines for that asset on that day
```

Range: approximately −6 to +6. Values beyond ±1.5 are considered divergent.

---

## Six-Layer Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    LAYER 6: APPLICATION/UI                   │
│  Global Dashboard | Company Profiles | Sector Views | AI    │
│  Analyst Interface                                           │
│  MVP: PDF reports emailed as attachments                     │
└─────────────────────────────────┬───────────────────────────┘
                                  │
┌─────────────────────────────────▼───────────────────────────┐
│                  LAYER 5: AI PROCESSING                      │
│  News Summarization | Entity Intelligence | Co-Pilot Chat    │
│  MVP: Claude API for summary text                            │
└─────────────────────────────────┬───────────────────────────┘
                                  │
┌─────────────────────────────────▼───────────────────────────┐
│                LAYER 4: SIGNAL GENERATION                     │
│  NDI Calculator | Bubble Risk Core | Market Stress Score     │
│  MVP: NDI + regime + confidence + risk (implemented)         │
│  → layer4_measurement.py, layer4_persistence.py              │
│  → layer4_classification.py, layer4_orchestrator.py          │
└─────────────────────────────────┬───────────────────────────┘
                                  │
┌─────────────────────────────────▼───────────────────────────┐
│                  LAYER 3: INTELLIGENCE                        │
│  Technical Engine | Fundamental Engine | NLP Engine          │
│  MVP: Loughran-McDonald sentiment + 20d momentum z-score     │
│  → reads from Layer 2, outputs in-memory dict to Layer 4     │
└─────────────────────────────────┬───────────────────────────┘
                                  │
┌─────────────────────────────────▼───────────────────────────┐
│                   LAYER 2: DATA STORAGE                      │
│  PostgreSQL (structured) | Vector DB (embeddings, post-MVP)  │
│  MVP: raw + config schemas, 7 tables, append-only event store│
│  → raw.prices, raw.news_headlines, raw.ingestion_runs        │
│  → config.monitored_assets, config.asset_aliases             │
│  → config.news_sources, config.ticker_vendor_mapping         │
└─────────────────────────────────┬───────────────────────────┘
                                  │
┌─────────────────────────────────▼───────────────────────────┐
│                  LAYER 1: DATA COLLECTION                    │
│  Market Data APIs | News Scrapers | Macro Feeds             │
│  MVP: yfinance (prices) + feedparser (6 RSS feeds)           │
│  → structural boundary: understands format, NOT meaning      │
└─────────────────────────────────────────────────────────────┘
```

---

## Layer Details

### Layer 1 — Data Collection

**Status:** Design spec (FINAL)

**Role:** Ingest raw market data and news headlines. Operates under a strict **structural vs. semantic boundary**: understands field names, schemas, and protocols but performs **zero** semantic interpretation.

**Allowed (structural):** RSS field names, URL parameters, timestamps, text normalization, SHA256 hashing, HTTP status codes.

**Prohibited (deferred to Layer 3):** Sentiment analysis, entity resolution, relevance filtering, source weighting.

**Components:**
- **Price Collection** — Yahoo Finance via `yfinance`. 5 assets in MVP (NVDA, AAPL, MSFT, SPX, BTC-USD). Runs once daily after 8 PM ET.
- **News Collection** — 6 hardcoded RSS feeds (Reuters, AP, Yahoo Finance General, Yahoo Finance Ticker, CNBC, MarketWatch). Runs every 4 hours 6 AM–8 PM ET + two high-impact windows (8:30 AM, 4:15 PM).

**Output:** Dict per headline with raw text, normalized text, SHA256 hash, timestamp, source, URL params, URL, ingestion timestamp.

---

### Layer 2 — Data Storage

**Status:** Design spec (MVP-ready)

**Role:** Append-only event store. Stores everything, transforms nothing. No domain logic encoded in the storage layer.

**Schema (MVP):**
- **`raw` schema** — immutable ingested data: `prices`, `news_headlines`, `ingestion_runs`
- **`config` schema** — mutable configuration: `monitored_assets`, `asset_aliases`, `news_sources`, `ticker_vendor_mapping`
- **`derived` schema** — explicitly deferred from MVP

**Key design decisions:**
- Every record carries `ingestion_run_id` for full traceability
- Unique constraint on `raw.prices`: `(ticker, date, source)`
- Unique constraint on `raw.news_headlines`: `(headline_hash, source)`
- MVP uses a single `signalq_app` PostgreSQL user — no role separation
- Schema migrations via version-controlled SQL in `/migrations/`

**Retention:** Prices and headlines indefinite; ingestion runs 90 days; config indefinite.

---

### Layer 3 — Intelligence / NLP

**Status:** Design spec (FROZEN — 16 decisions locked)

**Role:** Convert raw text and price data into structured signals. Two outputs: `sentiment_zscore` and `momentum_zscore`.

**16 frozen decisions:**
1. Sentiment lexicon: Loughran-McDonald (finance-specific, Tetlock 2007)
2. Score per headline: polarity `(pos − neg) / total`, range −1 to +1
3. Aggregation: mean of all headline scores per asset per day
4. Minimum headlines: `MIN_HEADLINES_PER_DAY = 3` (below this → NULL)
5. Normalization: 20-day rolling z-score
6. Minimum valid days for z-score: 10 of 20
7. Return type: simple daily return `(P_t − P_{t−1}) / P_{t−1}`
8. Momentum lookback: 20-day rolling z-score
9. Minimum momentum days: 10 of 20
10. Time alignment: 4:00 PM ET cutoff for headline-to-day assignment
11. Entity resolution priority: URL parameter exact match first
12. Alias matching: word-boundary substring, case-insensitive (ILIKE)
13. Conflict resolution: multi-ticker headlines → ALL matching tickers
14. Minimum alias length: 3 characters
15. NULL handling (prices): no interpolation
16. NULL handling (timestamps): fallback to `ingested_at`

**Output:** In-memory dict `{ticker: {sentiment_zscore, momentum_zscore}}` — no DB writes in MVP.

---

### Layer 4 — Signal Generation

**Status:** Implemented and tested (80 tests, all passing)

**Role:** Consume Layer 3 outputs, compute NDI, classify regime, determine risk level.

**Implemented modules:**

| Module | Sublayer | Responsibility |
|--------|----------|----------------|
| `layer4_measurement.py` | 4A | Validity gate, NDI calculation, 5-day return |
| `layer4_persistence.py` | 4B | Streak tracking, stale-gap detection, signal state, regime |
| `layer4_classification.py` | 4B | Confidence (inverted-U + streak boost), NDI trend, price pressure, risk, attention |
| `layer4_orchestrator.py` | 4C | 9-step pipeline, batch processing, input validation |

**9-step pipeline:**

```
 1. compute_measurements()   → validity gate, NDI, return_5d
 2. Short-circuit on invalid  → return early if validity_state != VALID
 3. NDI velocity              → ndi_delta, ndi_trend (before persistence update)
 4. get_signal_state()        → streak update with optional stale-gap reset
 5. get_regime()              → ALIGNED / ACCUMULATION / OVERHEATING
 6. Confidence                → base (inverted-U) + streak boost
 7. calculate_price_pressure()→ SUPPORTING / NEUTRAL / PRESSURING
 8. get_risk_level()          → NORMAL / ELEVATED / CRITICAL
 9. get_attention_text()      → one-line guidance
```

**Output (12-field dict):**
```
ticker, date, ndi, ndi_delta, ndi_trend, regime, signal_state,
confidence, price_modifier, persistence_days, risk_level, attention
```

**Key constants:**
- `NDI_THRESHOLD = 1.5` — regime boundary
- `PRICE_FLAT_THRESHOLD = 0.005` — price pressure flat zone
- `PERSISTENCE_REQUIRED = 2` — days to reach ACTIVE
- `PERSISTENCE_BOOST_STREAK = 3` — days to trigger confidence boost
- `MAX_GAP_DAYS = 3` — calendar gap before streak resets
- `CONFIDENCE_LOW_MAX = 0.8` — inverted-U lower bound
- `CONFIDENCE_HIGH_MAX = 2.2` — inverted-U upper bound
- `NDI_TREND_THRESHOLD = 0.3` — NDI velocity classification

**State management:** Only `PersistenceTracker` is stateful. Persists to `persistence_state.json` via explicit `save()` at end of batch. Per-ticker state: `{streak, last_ndi, last_updated}`.

---

### Layer 5 — AI Processing

**Status:** Design concept (post-MVP)

**Role:** Enrich signals with narrative intelligence: summarize news, explain entities, provide natural-language reasoning behind risk levels.

**MVP scope:** Single paragraph of summary text generated via Claude API.

**Full scope:** News summarization, entity intelligence, interactive Co-Pilot chat.

---

### Layer 6 — Application / UI

**Status:** Design concept (post-MVP)

**Role:** Present signals and analysis to end users.

**MVP scope:** PDF reports generated via `reportlab`, emailed via `smtplib`.

**Full scope:** Global dashboard, company profiles, sector deep dives, AI analyst interface.

---

## Production Build Order

Per the MVP execution plan, build proceeds **in reverse of architectural dependency order**:

```
Week 1     Layer 4 (simulated NDI) → validate formula with synthetic data
           Layer 6 (PDF mockup) → visual report with example numbers
Week 2     Sales → take mockup to prospects, identify 3 target assets
Week 2-3   Layer 1 + Layer 2 (real data pipeline) → yfinance + feedparser + PostgreSQL
           Layer 3 (NLP) → Claude API sentiment, momentum z-score
           Layer 4 + Layer 6 (real reports) → production output for paying clients
Week 5-6   Expand only if paid
```

---

## Data Flow

```
Layer 1                     Layer 2                     Layer 3
──────                      ──────                      ──────
yfinance ──→ raw.prices ──→ read 252d windows ──→ sentiment_zscore
feedparser ─→ raw.headlines                          momentum_zscore
                        config.asset_aliases ──→ entity resolution
                        config.monitored_assets
                               │
                               ▼
Layer 4                     Layer 5                     Layer 6
──────                      ──────                      ──────
ndi                         news summary ──→ PDF report
regime                      entity context    email delivery
risk_level
attention
```

---

## Output Schema (Layer 4 — Single Asset)

```json
{
  "ticker":            "NVDA",
  "date":              "2026-06-02",
  "ndi":               1.7,
  "ndi_delta":         0.2,
  "ndi_trend":         "ACCELERATING",
  "regime":            "OVERHEATING_DIVERGENCE",
  "signal_state":      "ACTIVE",
  "confidence":        "HIGH",
  "price_modifier":    "trend_stalling",
  "persistence_days":  2,
  "risk_level":        "ELEVATED",
  "attention":         "Narrative optimism with stalling price. Review position."
}
```

---

## Key Architectural Boundaries

| Boundary | Enforcement |
|----------|-------------|
| Layer 1 knows format, not meaning | No sentiment, entity resolution, or relevance filtering in collection |
| Layer 2 stores neutrally | No domain logic, no derived tables in MVP |
| Layer 3 interprets semantics | Entity matching, sentiment scoring, z-score normalization |
| Layer 4 is deterministic | No ML, no training, no optimization — pure threshold logic |
| Layer 5 adds narrative context | Summarization, explanation — not signal generation |
| Layer 6 presents | UI rendering only — no analytical logic |

---

## Repository Map

```
/Conceptual Analysis/         Commercial pitch, economic theory, strategy
/High-Level Design (HLD)/     Layer specs, MVP plan, product engineering
/Low-Level Design (LLD)/      Detailed implementation specs (Layer 4)
/Architecture/                 Implementation architecture (Layer 4)
/Prompts/                      LLM prompts derived from LLD + architecture

layer4_measurement.py          Layer 4 — measurement sublayer
layer4_persistence.py          Layer 4 — persistence sublayer
layer4_classification.py       Layer 4 — classification sublayer
layer4_orchestrator.py         Layer 4 — orchestrator sublayer
test_layer4.py                 Layer 4 — 80 integration tests

architecture.md                This file — full system architecture
```

---

## Implementation Status

| Layer | Status | Artifact |
|-------|--------|----------|
| 1 — Collection | Design spec (FINAL) | `HLD/Layer_01.md` |
| 2 — Storage | Design spec (MVP-ready) | `HLD/Layer_02.md` |
| 3 — Intelligence | Design spec (FROZEN) | `HLD/Layer_03.md` |
| 4 — Signal Generation | **Implemented** (80 tests) | Python modules + `Architecture/Layer_04_arch.md` |
| 5 — AI Processing | Design concept | `HLD/product_engineering.md` |
| 6 — Application/UI | Design concept | `HLD/product_engineering.md` |

Layer 4 is the only implemented layer. Layers 1–3 are fully specified and ready for implementation. Layers 5–6 are outlined at the architectural level only.
