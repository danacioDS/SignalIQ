
---

# SIGNALIQ: UNIFIED SPECIFICATION DOCUMENT (v1.0)
## Deliverables Summary

## Core Identity

> **SignalIQ measures the distance between what the market is saying and what the market is actually doing.**

**One-line technical definition:** A narrative-driven quantitative intelligence system that computes the divergence between normalized media sentiment and normalized price momentum, then classifies the resulting regime.

**Operating principle:** Measurement, not prediction. Attention signal, not trading signal.

---

## The Core Formula

```
NDI(t) = sentiment_zscore(t) − momentum_zscore(t)
```

Where:
- `sentiment_zscore(t)` = (daily_sentiment - rolling_mean_20d) / rolling_std_20d
- `momentum_zscore(t)` = (daily_return - rolling_mean_20d) / rolling_std_20d

---

## System Architecture

```
LAYER 1: DATA COLLECTION (Extract structure. Never interpret meaning.)
    │
    ├── Prices: Yahoo Finance (5 assets: NVDA, AAPL, MSFT, SPX, BTC-USD)
    │   └── Daily adjusted close, once daily after 8 PM ET
    │
    └── News: 6 hardcoded RSS feeds
        ├── Reuters, AP, Yahoo General, Yahoo Ticker, CNBC, MarketWatch
        └── Every 4 hours (6 AM-8 PM ET) + 8:30 AM + 4:15 PM
    │
    ▼
LAYER 2: DATA STORAGE (Append-only event store. Transform nothing.)
    │
    ├── Schemas: raw (immutable) + config (configuration only)
    ├── No derived schema in MVP
    ├── Full traceability: ingestion_run_id + source_record_id on every row
    └── Tables: prices, news_headlines, ingestion_runs, monitored_assets, 
                asset_aliases, news_sources, ticker_vendor_mapping
    │
    ▼
LAYER 3: INTELLIGENCE PROCESSING (Transform to z-scores. No storage write.)
    │
    ├── Sentiment: Loughran-McDonald lexicon, count-based polarity
    ├── Momentum: Simple daily returns
    ├── Windows: 20-day rolling for both (min 10 valid days)
    ├── Entity resolution: URL param priority → alias matching (word-boundary, case-insensitive)
    └── Output: sentiment_zscore + momentum_zscore per (asset, day)
    │
    ▼
LAYER 4: SIGNAL GENERATION (Deterministic. No training. No prediction.)
    │
    ├── NDI = sentiment_zscore − momentum_zscore
    ├── Price direction: 5-day simple return (threshold 0.5%)
    ├── Regime classification (5 regimes based on NDI + price direction)
    └── Output: NDI + Regime + Signal Color (Green/Yellow/Orange/Red)
```

---

## Parameter Summary (All Frozen for MVP)

| Parameter | Value | Layer |
|-----------|-------|-------|
| Sentiment lexicon | Loughran-McDonald | L3 |
| Sentiment scoring | Count-based polarity | L3 |
| Min headlines per day | 3 | L3 |
| Sentiment/momentum window | 20 days | L3 |
| Min valid days for z-score | 10 | L3 |
| Daily cutoff (ET) | 4:00 PM | L3 |
| Min alias length | 3 characters | L3 |
| NDI divergence threshold | ±1.5 | L4 |
| Price direction lookback | 5 days | L4 |
| Price direction threshold | ±0.5% | L4 |

---

## The Five Regimes (Commercial Output)

| NDI Range | Price Direction | Regime | Signal |
|-----------|-----------------|--------|--------|
| < -1.5 | Rising or Flat | 🔵 Silent Accumulation | 🟢 Green |
| -1.5 to 1.5 | Any | ⚪ Aligned | 🟢 Green |
| > 1.5 | Rising or Flat (> -0.5%) | 🟡 Narrative Exhaustion | 🟡 Yellow |
| > 1.5 | Flat (0 to -0.5%) | 🟠 Divergence Warning | 🟠 Orange |
| > 1.5 | Falling (< -0.5%) | 🔴 Severe Divergence | 🔴 Red |

---

## What SignalIQ Is NOT (Reinforced)

| ❌ NOT | ✅ IS |
|--------|-------|
| A prediction system | A measurement of current divergence |
| A buy/sell signal generator | A risk intelligence platform |
| A replacement for human analysts | A systematic second opinion |
| A crisis prediction tool | A narrative exhaustion detector |
| A backtest-optimized black box | A deterministic, transparent formula |

---

## MVP Scope Boundaries

| Included | Excluded (Post-MVP) |
|----------|---------------------|
| 5 assets (NVDA, AAPL, MSFT, SPX, BTC-USD) | 35+ assets |
| 6 news sources, uniform weighting | Source influence weighting |
| Headlines only | Full article text |
| Daily frequency | Intraday |
| Simple alias matching (ILIKE) | Regex, fuzzy matching |
| No database writes from L3/L4 | Derived schema, historical NDI storage |
| Email PDF report | Interactive dashboard |
| No probabilistic outputs | Bubble risk probability, confidence intervals |

---

## Validation Framework Design

### Core Principle

> Validation does not optimize parameters. Validation measures whether the existing deterministic system produces information not already available to a naive observer.

### Null Hypothesis (Must Disprove)

> *"The NDI regime classification contains no information beyond current price momentum alone."*

### Test Structure

**Test 1: Regime Sorting**

| Question | Method |
|----------|--------|
| Do higher NDI regimes predict worse forward returns? | Sort all (asset, day) observations by regime (Green → Yellow → Orange → Red). Compute mean forward 5-day, 10-day, 20-day returns for each regime. Expect monotonic degradation. |

**Test 2: Divergence vs Baseline**

| Question | Method |
|----------|--------|
| Does NDI > 1.5 with flat/falling prices produce worse outcomes than random days? | Sample 10,000 random days (matched by asset and volatility regime). Compare forward return distribution of divergence signals vs baseline using Mann-Whitney U test. |

**Test 3: Silent Accumulation Asymmetry**

| Question | Method |
|----------|--------|
| Does NDI < -1.5 predict different outcomes than NDI > 1.5? | Compare forward returns for negative divergence (Silent Accumulation) vs positive divergence (Narrative Exhaustion+). Expect asymmetry: negative divergence may precede continued upside, not correction. |

### Walk-Forward Validation (Post-MVP)

| Window | Training | Test | Purpose |
|--------|----------|------|---------|
| Expanding | First 252 days | Next 21 days | Simulate live deployment |
| Re-estimation | Quarterly | N/A | Coefficients re-fit (for L3 normalization only) |
| Reporting | Monthly | N/A | Track out-of-sample AUC-ROC, lift, KS test |

**Note:** Only Layer 3 normalization coefficients (rolling mean/std of sentiment and momentum) are re-estimated. Layer 4 thresholds (1.5, 0.5%) remain fixed.

### Success Criteria (MVP Go/No-Go)

| Metric | Threshold | Measurement |
|--------|-----------|-------------|
| Regime monotonicity | Mean forward returns strictly decreasing Green→Yellow→Orange→Red over 10+ days | Statistical test (Jonckheere-Terpstra) |
| Divergence lift | Forward 10-day return at least 200bps worse than baseline for Red regime | p < 0.05 |
| Silent accumulation | No requirement (exploratory) | Document findings |
| False positive rate | Red regime appears in < 15% of days | Descriptive |

### What Validation Explicitly Does NOT Do

| ❌ Not in Validation | Reason |
|---------------------|--------|
| Optimize NDI threshold (1.5) | Would overfit; threshold is theoretical (top 10% of distribution) |
| Optimize lookback windows (20, 5 days) | Would overfit; windows come from Tetlock and market convention |
| Add predictors based on backtest | Would turn measurement into prediction |
| Report Sharpe ratio or alpha | SignalIQ is not a trading strategy |

---

## MVP Technical Stack

| Component | Technology |
|-----------|------------|
| Data collection | `yfinance` + `feedparser` |
| Storage | PostgreSQL (≥14) |
| Sentiment + report generation | Anthropic Claude API |
| Calculations | `pandas` + `scipy` |
| Scheduling | `APScheduler` |
| PDF export | `reportlab` |
| Email delivery | `smtplib` |

---

## Production Build Order (Week by Week)

| Week | Deliverable | Success Criterion |
|------|-------------|-------------------|
| 1 | Simulated NDI in Python | NDI moves between -3 and +3; extremes appear ~10% of time |
| 1 | PDF report mockup (example data) | Non-technical prospect understands output |
| 2 | Sales: mockup to 10 prospects | At least 1 says "yes, for these 3 assets" |
| 2-3 | L1+L2 for 3 specific assets | Prices + headlines flowing into PostgreSQL |
| 3 | L3 (sentiment via API + momentum) | sentiment_zscore + momentum_zscore daily |
| 3-4 | L4 + real PDF report | First real report delivered |
| 4 | Collect payment | Pilot fee received |
| 5-6 | Expand only if paid | Additional assets, Bubble Risk, dashboard |

---

## The Golden Rules (Consolidated)

1. **Layer separation:** L1 extracts structure. L2 stores raw. L3 transforms to z-scores. L4 measures divergence. No layer does another layer's job.

2. **No business logic in L1:** L1 sees URL parameters as strings, not asset references.

3. **No derived tables in MVP:** L3 and L4 write nothing to the database.

4. **No prediction:** SignalIQ measures divergence. It does not forecast prices.

5. **No optimization:** Parameters are frozen. Validation tests, not trains.

6. **Build backward:** Mockup → Sell → Build data for chosen assets → Collect payment → Automate.

---

## Document Status

| Section | Status |
|---------|--------|
| Core Identity | FROZEN |
| Architecture | FROZEN |
| Layer 1 | FROZEN |
| Layer 2 | FROZEN |
| Layer 3 | FROZEN |
| Layer 4 | FROZEN |
| Parameters | FROZEN |
| Validation Framework | FROZEN |
| MVP Scope | FROZEN |
| Build Order | FROZEN |

**Unified Specification v1.0 is complete and ready for implementation.**

---

**SignalIQ** 🔹

*Where market narratives meet market reality.*
