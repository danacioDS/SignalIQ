
---

# SignalIQ: Technical Core & Architectural Flow

## Architectural Overview

The technology stack serves as a direct pipeline executing the progression from unstructured information to verified risk metrics.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        LAYER 1: DATA COLLECTION                        │
│  - Market Data APIs      - News Scrapers (NLP Input)    - Macro Feeds  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        LAYER 2: DATA STORAGE                           │
│  - Relational (PostgreSQL)                  - Vector DB (Embeddings)   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        LAYER 3: INTELLIGENCE PROCESSING                │
│  - Quant / Technical Engine   - Fundamental Engine   - NLP Text Engine │
└───────────────────────────────────┬────────────────────────────────────┘
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        LAYER 4: SIGNAL GENERATION                      │
│  - NDI Calculator             - Bubble Risk Core     - Stress Scoring  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        LAYER 5: AI PROCESSING                          │
│  - News Summarization         - Entity Intelligence   - Co-Pilot Chat  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        LAYER 6: APPLICATION & UI                       │
│  - Global/Asset Dashboards    - Sector Overviews     - AI Analyst Chat │
└────────────────────────────────────────────────────────────────────────┘
```

---

## Deep-Dive Functional Layer Breakdown

### Layer 1: Data Collection (ETL Pipelines)

The collection framework comprises three distinct ingestion pipelines designed for resilience and consistency.

**Market Collector:** Ingests daily and intraday structural pricing for global equities, indices, commodities, forex, and sovereign bonds.

**News Collector:** Scrapes and normalizes unstructured editorial output from an intentionally diversified media ecosystem (including Reuters, CNBC, AP, Yahoo Finance, and MarketWatch). For every ingested text asset, the system extracts a structured payload:

- headline
- article content
- author
- date/time
- source publisher
- target entity/ticker
- market sector

**Macro Collector:** Pulls macro indices and absolute yields from global benchmarks, tracking currency dynamics, sovereign debt curves, physical commodity inputs, and benchmark interest rates.

---

### Layer 2: Data Storage Systems

Data separation enforces processing efficiency by splitting fast numerical operations from heavy semantic queries.

**Structured Storage Engine (PostgreSQL):** Hosts historical price matrices, returns, volume, quantitative technical indicators, and corporate fundamentals.

**Unstructured Storage Engine (Vector Database):** Stores raw news content, summarized strings, and high-dimensional semantic embeddings. Supported instances include Qdrant, Weaviate, or Chroma, enabling fast semantic search and similarity matching.

---

### Layer 3: Intelligence Processing Layer

Three specialized analytic components run simultaneously to transform the ingested records into relative metrics.

```
              ┌─────────────────────────────────┐
              │       INTELLIGENCE LAYER        │
              └────────────────┬────────────────┘
                               │
     ┌─────────────────────────┼─────────────────────────┐
     ▼                         ▼                         ▼
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│Technical Engine │       │Fundamental Engine│       │NLP Text Engine  │
├─────────────────┤       ├─────────────────┤       ├─────────────────┤
│ Calculates:     │       │ Calculates:     │       │ Performs:       │
│ - RSI, MACD     │       │ - P/E & Fwd P/E │       │ - Sentiment     │
│ - EMAs/SMAs     │       │ - Margins & ROE │       │ - Topic Spotting│
│ - Momentum      │       │ - EPS Growth    │       │ - Narrative Cons│
│ - Volatility    │       │ - Free Cash Flow│       │ - Source Weights│
└────────┬────────┘       └────────┬────────┘       └────────┬────────┘
         │                         │                         │
         ▼                         ▼                         ▼
[Technical Score]       [Fundamental Score]       [Narrative Score]
```

**Technical Analysis Engine:** Processes mathematical price arrays to compute relative strength indexes (RSI), moving average convergence divergence (MACD), exponential and simple moving averages, rolling momentum, statistical volatility, historical drawdowns, and cross-asset relative strength. *Output: Technical Score.*

**Fundamental Analysis Engine:** Computes valuation ratios and operational performance metrics including price-to-earnings (P/E), forward P/E, revenue and earnings per share (EPS) growth vectors, corporate debt loads, operating margins, return on equity (ROE), and free cash flow generation. *Output: Fundamental Score.*

**Narrative Intelligence Engine:** Ingests text strings and extracts semantic orientation via four sequential steps:

1. **Sentiment Analysis:** Identifies polarity distributions (Positive, Neutral, Negative)
2. **Topic Detection:** Tags conceptual drivers (e.g., AI investment, interest rate path, inflation pressures, earnings outcomes, geopolitical risk)
3. **Narrative Consensus Scoring:** Measures alignment, disagreement, and semantic polarization across media networks
4. **Source Influence Weighting:** Scales the impact of the score based on publisher profiles (e.g., placing authoritative institutional agencies like Reuters above retail investment blogs)

*Output: Narrative Score.*

---

### Layer 4: Signal Generation Layer

The signal generation layer synthesizes raw data from Layer 3 into normalized indicators.

**Narrative Divergence Index (NDI):** Calculates the divergence between news sentiment and price momentum.

```
NDI(t) = [ S_news(t) - μ_s ] / σ_s - [ M_price(t) - μ_m ] / σ_m
```

**Statistical Validation Framework:** All NDI outputs are validated through a rigorous walk-forward methodology. The model is trained on expanding 252-day windows and tested on subsequent 21-day periods, with coefficients re-estimated quarterly. Validation metrics include Kolmogorov-Smirnov goodness-of-fit tests (to ensure NDI distribution approximates N(0,2)), AUC-ROC for binary correction prediction, and likelihood ratio tests for nested model comparison. Historical out-of-sample performance is tracked and reported monthly.

**Bubble Risk Score:** Merges the Narrative, Technical, Fundamental, and Macro scores into a single bounded risk index scaled from 0 to 100. For example, an asset experiencing extreme media hype alongside weakening operational fundamentals and overextended technical indicators will trigger an elevated risk score.

```
Asset Example: NVIDIA
- Narrative Score: 95
- Technical Score: 82
- Fundamental Score: 61
───────────────────────────
Calculated Bubble Risk: 84 / 100
```

**Market Stress Score:** Compiles intermarket price relationships among bonds, global reserve currencies, safe-haven gold, industrial energy inputs, and broad equity indices to output an overall Global Risk-On / Risk-Off indicator.

---

### Layer 5: AI Processing Layer

Artificial intelligence is leveraged exclusively for specific contextual text-processing tasks where quantitative equations fall short. This layer operates in parallel with Layer 4, consuming its outputs to enhance interpretability.

**News Summarization:** Condenses large text sets to isolate the underlying themes driving asset sentiment.

**Entity Intelligence Engines:** Processes multi-source documentation to explain sudden metric shifts (e.g., determining exactly why a specific firm's NDI is expanding).

**Investment Co-Pilot Interactivity:** Powers a domain-specific natural language processor capable of cross-referencing NDI metrics, news flows, and financial scores to generate structured comparative breakdowns on demand.

---

### Layer 6: User Application Layer

The interface maps out these layers through four tactical entry points:

**Global Dashboard:** Surfaces broad market conditions, interest rates, commodities, and active risk regimes.

**Company Profiles:** Isolates individual stock metrics, providing a view of their Technical, Fundamental, Narrative, NDI, and Bubble Risk profiles.

**Sector Deep Dives:** Displays aggregate sector performance metrics, cross-referencing thematic sentiment against sector price momentum.

**AI Analyst Interface:** An embedded chat module designed to handle analytical prompts (e.g., "Which companies currently show the highest narrative divergence?").

---

## Technological Classification & Taxonomy

SignalIQ sits at the intersection of quantitative modeling and natural language processing. It is defined as an AI-Powered Market Intelligence Platform with Embedded Statistical Validation.

```
                  ┌──────────────────────────────────────────────┐
                  │                  SignalIQ                    │
                  └──────────────────────┬───────────────────────┘
                                         │
         ┌───────────────────────────────┼───────────────────────────────┐
         ▼                               ▼                               ▼
┌──────────────────────────────┐ ┌──────────────────────────────┐ ┌──────────────────────────────┐
│    Quantitative Finance      │ │  Natural Language Processing │ │   Predictive Intelligence    │
├──────────────────────────────┤ ├──────────────────────────────┤ ├──────────────────────────────┤
│ Calculates momentum, math    │ │ Determines sentiment drifts, │ │ Quantifies divergence states  │
│ indicators, volatility and   │ │ extracts topics, and computes│ │ and generates validated      │
│ absolute risk regimes.       │ │ source-weighted consensus.   │ │ risk metrics.                │
└──────────────────────────────┘ └──────────────────────────────┘ └──────────────────────────────┘
```

### Industry Taxonomy Positioning

**Primary Category:** Alternative Data Intelligence Platform. The platform converts unstructured news text into normalized, actionable signals that are systematically cross-referenced against price trends.

**Secondary Categories:** Risk Intelligence Platform, Sentiment Analysis System, and Cross-Asset Monitoring Platform.

### Core Architectural Delineations

| What SignalIQ IS | What SignalIQ IS NOT |
|------------------|----------------------|
| A Narrative-Driven Quantitative Intelligence System: A platform that joins normalized math formulas with text signals to isolate risk regimes | A Trading Terminal: It features no execution hooks, order routing tables, portfolio management suites, or broker integrations |
| A Comprehensive Risk Engine: An environment engineered to measure systemic market stress and asset-level structural exhaustion | A Pure Backtesting Engine or News Aggregator: It does not operate as a strategy playground or simple news feed; text is an input, not the output |

---

## Comprehensive Technical Summary Blueprint

```
Product Name: SignalIQ
Category: AI-Powered Market Intelligence Platform
Subcategory: Narrative-Driven Quantitative Intelligence System

Core Technological Components:
- NLP Sentiment Analysis Engine
- Technical Analysis Engine (momentum, RSI, volatility)
- Fundamental Analysis Engine (P/E, growth, margins)
- Statistical Validation Framework (KS test, AUC-ROC, walk-forward validation)
- Vector Database for Unstructured News Data
- AI Co-Pilot for Natural Language Queries

Primary Output:
- Narrative Divergence Index (NDI)
- Bubble Risk Score (0-100)
- Market Stress Score (Risk-On / Risk-Off)

Target User:
- Institutional investors
- Portfolio managers
- Risk analysts
- Quant researchers

Differentiator:
- Not a predictor. A measurer with statistical rigor
- Based on 90+ years of academic theory (Keynes, Dornbusch, Tetlock)
- Validated through walk-forward testing, likelihood ratios, and goodness-of-fit
```

---

**SignalIQ**

---
