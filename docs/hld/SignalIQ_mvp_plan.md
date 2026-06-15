
---
# SignalIQ: Validation & MVP Execution Plan

## One Sentence Summary

> Simulate the NDI. Build the report mockup. Sell the concept. Build real data only for the assets the prospect chooses. Collect payment before automating.

---

## Guiding Principle

**Build in reverse order of computational complexity, not in layer order.**

The technical architecture shows 6 layers from bottom to top (Ingestion → Storage → Intelligence → Signals → AI → UI). Building them in that order is a strategic error for a solo founder.

The correct order starts from the output (Layer 4) and works backward.

---

## Reference Nomenclature

This document uses two orthogonal dimensions from the base architecture:

| Dimension | Purpose | Example |
|-----------|---------|---------|
| **Layers (1–6)** | Technical components — *how you process it* | Ingestion, Storage, Intelligence, Signals, AI, UI |
| **Levels (1–8)** | Analysis domains — *what you monitor* | Prices, bonds, commodities, indices, sectors, narrative, fundamentals, bubble |

**MVP scope:** Layers 1–4 (partial). Levels 1, 5, 6 (partial).

---

## The Core Insight: When to Sell vs. When to Build

The greatest risk is not technical failure. It is building for 6 weeks for a prospect who never existed, or building 35 companies when the prospect only wanted 3.

**The rule is simple:** Every line of code after the mockup must be paid for by a pilot commitment.

| If the prospect has not yet said yes | Then |
|----------------------------------------|----------|
| Do not build anything that requires real data | Only mockups and simulated NDI |
| Do not expand coverage | You do not know which assets they want |
| Do not automate | The waiting time is the prospect's, not yours |

| If the prospect says yes | Then |
|-----------------------------|----------|
| Build only for their specific assets | Not for 35 companies |
| Automate only what is necessary to deliver | Do the rest manually if it works |
| Collect payment before automating | Payment validates real interest |

---

## Production Order (Weeks 1–6)

| Priority | Component | What You Build | Estimated Time |
|----------|-----------|----------------|-----------------|
| 1 | Layer 4 (partial) | NDI with simulated data — validate logic before touching real data | Days 1–2 |
| 2 | Layer 6 (minimum) | PDF report mockup — no real data, only format and language | Days 3–5 |
| 3 | Sales | Take mockup to prospects. Ask: "Which three assets?" | Week 2 |
| 4 | Layers 1 + 2 (minimum) | Real prices + basic PostgreSQL for the chosen assets | Week 2–3 |
| 5 | Layer 3 (partial) | NLP via API + simple price momentum for chosen assets | Week 3 |
| 6 | Layer 4 + Layer 6 | Real NDI + real PDF report for the pilot | Week 3–4 |
| 7 | Everything else | Full Bubble Risk, Stress Score, Co-Pilot, dashboards, 35 companies | Post-MVP (only if paid) |

---

## Weekly Deliverables (Detailed)

### Week 1 (Days 1-2): Simulated NDI

**Objective:** Validate that the NDI logic produces interpretable signals without any real data.

**What you build:**
- Two simulated 252-day series: sentiment and momentum (normally distributed, mean 0)
- Apply the NDI formula: `NDI = (sentiment - μ_s)/σ_s - (momentum - μ_m)/σ_m`
- Observe the output distribution

**Success criteria:**
- Simulated NDI moves between -3 and +3
- Extreme values (>1.5 or < -1.5) appear approximately 10-15% of the time
- You can explain what a positive NDI vs negative NDI means

**What you do not do:**
- Connect real data sources
- Store anything in PostgreSQL
- Automate anything

---

### Week 1 (Days 3-5): Report Mockup (No Real Data)

**Objective:** Create a two-page PDF report that looks like the final product but contains example numbers.

**What you build:**
- PDF template with your branding
- Example NDI chart (simulated data)
- Two analysis paragraphs per asset (using simulated NDI values)
- "Sample Data — For Illustration Only" watermark (transparent)

**What the report contains:**
- Asset ticker and date
- Numerical NDI
- Regime classification (5 categories from the Commercial Pitch)
- Signal color (Green/Yellow/Orange/Red)
- Two-paragraph analysis (narrative + technical interpretation)

**Success criteria:** A non-technical prospect can understand what the report delivers.

---

### Week 2: Sales — Take Mockup to Prospects

**Objective:** Get a pilot commitment before building real data pipelines.

**What you do (not build):**
- Email cold prospects: *"I am piloting a daily risk report for 3 assets of your choice. This is the format. Which three assets do you follow?"*
- Show the mockup. Do not say "it's just an example." Say: *"This is the format. The NDI behind these numbers already works in my test system."*

**Success criteria:** At least one prospect says "yes, I want the pilot for AAPL, MSFT, and NVDA."

**If no one says yes:** Do not build anything else. The problem is positioning or the prospect list, not the technology.

---

### Week 2-3: Build Real Data Only for the Chosen Assets

**Objective:** Implement the minimum pipeline for exactly the assets the prospect chose.

**What you build (only for 3 assets, not 35):**

| Component | Implementation |
|-----------|----------------|
| Daily prices | `yfinance` |
| Cumulative return (momentum) | Self-calculated over 5 days |
| Daily sentiment | Claude API classifying RSS headlines from 6 free sources |
| Storage | PostgreSQL (minimal schema) |
| NDI calculation | As validated in Week 1 |
| Regime classification | Lookup table (5 regimes) |

**What you do not build:**
- 35 companies
- 7 sectors
- Source influence weighting
- Vector databases
- Any automation beyond what is strictly necessary to deliver the pilot report

---

### Week 3-4: Deliver First Real Report — Collect Payment

**Objective:** Deliver the first real PDF report to the prospect and collect payment.

**What you deliver:**
- Daily PDF report sent by email at 7 AM
- Contains real NDI, real regime, real analysis for the 3 chosen assets
- Two analysis paragraphs generated via API (Claude)

**What you do before delivering:**
- Internal validation on one known case (e.g., NVDA from the Commercial Pitch)
- Verify that NDI crossed into Narrative Exhaustion before a historical correction

**Success criteria:** The prospect receives the report, reads it, and pays the pilot fee.

---

### Week 5-6: Expand Only If Paid

**Objective:** Add features only if the pilot client asks and pays.

**Potential expansions (only if client demands):**
- More assets (beyond the original 3)
- Bubble Risk Score
- Sector-level NDI
- Interactive dashboard

**Do not build these speculatively.**

---

## What the MVP Includes (Weeks 1–6)

### Active Layers

| Layer | Component | MVP Implementation |
|-------|-----------|-------------------|
| Layer 1 | Data collection | Prices (yfinance) + RSS news (6 free sources) |
| Layer 2 | Storage | PostgreSQL — minimal schema for 3 assets |
| Layer 3 | Intelligence | Sentiment via Claude API + price momentum z-score |
| Layer 4 | Signal generation | NDI + regime classification (5 categories) |
| Layer 5 | AI processing | News summary only for the report — no Co-Pilot |
| Layer 6 | UI | Email with PDF attachment — no dashboard |

### Active Levels (Analysis Domains)

| Level | Domain | Status in MVP |
|-------|---------|---------------|
| Level 1 | Global prices (FX, indices, commodities) | Included for chosen assets only |
| Level 5 | Sectors and companies | Only the 3 chosen assets |
| Level 6 | Narrative — news and sentiment | Included |
| Levels 2, 3, 4, 7, 8 | Bonds, deep commodities, fundamentals, bubble | Excluded from MVP |

---

## What You Do NOT Build in the MVP

| Component | Decision |
|----------------------------------|----------|
| Vector database for embeddings | No |
| Fundamental engine (P/E, ROE, margins) | No — expensive data |
| Source influence weighting | No — uniform weight at the start |
| Co-Pilot or interactive chat | No — it is a separate product |
| Global or sector dashboards | No |
| Full Bubble Risk Score | No |
| Market Stress Score | No |
| 35 companies / 7 sectors | No — only the 3 assets the prospect chose |

---

## MVP Technical Stack

| Component | Technology |
|-----------|------------|
| Daily prices | `yfinance` |
| RSS headlines | `feedparser` (Reuters, CNBC, AP, Yahoo, MarketWatch) |
| Sentiment + report generation | Anthropic API (Claude) |
| NDI calculation, z-scores | `pandas` / `scipy` |
| Storage | PostgreSQL |
| Scheduling | `APScheduler` (daily pipeline) |
| PDF export | `reportlab` |
| Email delivery | `smtplib` |

---

## The NDI: What It Is and What It Is Not

**What it is:** The divergence between news sentiment and price momentum.

**Formula:**
```
NDI(t) = sentiment_zscore(t) − momentum_zscore(t)
```

**What it is not:** A predictor. It is a **measure of misalignment**.

### The Five Regimes (from the Commercial Pitch)

| NDI Range | Regime | Interpretation |
|-----------|--------|----------------|
| NDI < -1.5 | 🔵 Silent Accumulation | Prices rising without narrative support. Often precedes sustained uptrends. |
| NDI ≈ 0 | ⚪ Aligned | Narrative-price alignment. Healthy, sustainable trend. |
| NDI > 1.5 | 🟡 Narrative Exhaustion | Optimism persists but momentum weakens. The story is running out of new buyers. |
| NDI > 1.5 with flat prices | 🟠 Divergence Warning | Institutional money may be exiting while public enthusiasm remains elevated. |
| NDI extreme with falling prices | 🔴 Severe Divergence | Maximum-risk environment. Historically associated with abrupt corrections. |

**Note:** Silent Accumulation (NDI < -1.5) is the inverse signal — a potential entry opportunity. The MVP does not need to act on this signal, but the classification must be present for consistency.

---

## Internal Validation (Before Delivering to Prospect)

Before sending the first real report, validate that the NDI behaves as expected:

| Test | Method | Success Criteria |
|------|--------|------------------|
| **Known case** | Take historical data from a period where you believe the signal would have worked (e.g., NVDA). Calculate NDI day by day. | NDI crossed into Narrative Exhaustion or Divergence Warning before the correction. |
| **Statistical distribution** | Calculate NDI for 252 consecutive days. Compare to N(0,2) using a KS test. | Distribution is approximately normal with variance ~2. |
| **False positives** | Count how many times NDI > 1.5 occurred without a subsequent correction. | Not zero, but the rate is informative (not random). |

---

## Outstanding Decisions Before Building

Two points need explicit resolution before Week 1 implementation:

| Decision | Question | Recommended Answer |
|----------|----------|--------------------|
| **Output language** | The analysis paragraphs in the prototype are in Spanish. The rest of the suite is in English. | **English** for pilot (prospect-facing). Translate later if needed. |
| **Test asset for pilot** | You need a demonstration asset with real NDI history — ideally a case where the signal worked (equivalent to NVDA in the Commercial Pitch). | **Use NVDA** as the internal validation asset. It matches the pitch and has public historical data. |

---

## The Golden Rule (Repeated for Emphasis)

> Simulate the NDI. Build the report mockup. Sell the concept. Build real data only for the assets the prospect chooses. Collect payment before automating. Everything else is post-pilot.

Your real differentiator is not the complete architecture. It is delivering a useful report for a specific client's specific assets, fast, before they lose interest.

---

**SignalIQ** — Unified MVP Production Strategy
