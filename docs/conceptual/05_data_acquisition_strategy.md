
---

# SignalIQ Data Acquisition Strategy

## Objective

SignalIQ aims to build a balanced representation of financial reality by combining structured market data with unstructured narrative data.

The system is designed to observe not only what markets are doing, but also what influential information sources are saying about markets.

The objective is to reduce informational blind spots and avoid reliance on a single narrative source.

---

## 1. Structured Financial Data Sources

SignalIQ collects quantitative information from publicly available financial market data providers.

### Market Prices

Coverage includes:

- Individual equities
- Equity indices
- Commodities
- Currency pairs
- Government bonds
- ETFs

**Primary source:** Yahoo Finance (supplemented with exchange-provided data where available for critical assets)

**Limitation acknowledged:** Yahoo Finance provides reliable historical and end-of-day data but is not institutional grade for real-time or tick-level analysis. SignalIQ uses it for divergence detection, which operates on daily and multi-day intervals, not millisecond timing. For institutional deployment, data source upgradability is pre-budgeted.

**Purpose:**
- Price history
- Volume
- Volatility
- Momentum
- Relative performance

---

## 2. Macroeconomic Information

SignalIQ monitors key indicators affecting global capital allocation.

### Currencies

Major pairs only (liquidity threshold):

- USD/CNY
- USD/JPY
- EUR/USD
- GBP/USD

*USD/BOB excluded due to insufficient liquidity and global narrative relevance.*

### Sovereign Debt Markets

- United States Treasury Market
- United Kingdom Gilts
- Japanese Government Bonds
- Chinese Government Bonds
- Eurozone Sovereign Debt Markets

### Strategic Commodities

- Crude Oil
- Gold
- Copper
- Wheat
- Lithium

**Purpose:**
- Measure inflation pressure
- Monitor economic growth expectations
- Identify shifts in global capital flows
- Detect macroeconomic stress

---

## 3. Narrative Intelligence Sources

SignalIQ continuously analyzes financial and economic news from publicly accessible sources.

The goal is not to determine which source is correct.

The goal is to measure how narratives are distributed across the information ecosystem.

---

## 4. Media Diversification Framework

To reduce narrative concentration risk, SignalIQ monitors sources across the editorial spectrum. The categorization below is descriptive, not evaluative. SignalIQ does not assert political truth or balance. It asserts only that narrative concentration in any single quadrant creates blind spots.

**Left-leaning:** CNN, MSNBC, Vox

**Center / business-oriented:** Reuters, Associated Press, MarketWatch, Yahoo Finance, CNBC

**Right-leaning:** Fox Business, Wall Street Journal Opinion, New York Post Business

SignalIQ does not attempt to determine political truth. The system seeks exposure across perspectives to detect when a narrative becomes concentrated in one quadrant while price moves independently.

---

## 5. Financial News Sources

Priority is given to sources with strong influence on U.S. investors.

**Tier 1 Sources**
- Reuters
- Associated Press
- CNBC
- Bloomberg (publicly accessible content)
- Yahoo Finance

**Tier 2 Sources**
- MarketWatch
- Seeking Alpha
- The Motley Fool
- Barron's public articles

**Tier 3 Sources**
- Financial blogs
- Industry publications
- Company-specific commentary

---

## 6. Source Influence Weighting

Not all news sources have equal impact on market participants.

SignalIQ assigns an influence score based on:

- **Reach:** Estimated audience size
- **Financial Relevance:** Importance among investors and financial professionals
- **Historical Market Impact:** Frequency with which a source contributes to major market narratives
- **Citation Frequency:** How often the source is referenced by other media organizations

**Example weighting:**

| Source | Influence |
|--------|-----------|
| Reuters | Very High |
| CNBC | High |
| Bloomberg | High |
| Wall Street Journal | High |
| Yahoo Finance | Medium |
| MarketWatch | Medium |
| Blogs | Low |

The objective is to approximate narrative influence rather than article quantity.

---

## 7. Narrative Consensus Score

For each company, sector, or market theme, SignalIQ calculates:

- Positive sentiment
- Neutral sentiment
- Negative sentiment

across all monitored sources.

The system then measures:

- **Narrative Consensus:** Degree of agreement across sources
- **Narrative Dispersion:** Degree of disagreement across sources
- **Narrative Intensity:** Strength of overall sentiment

**Example application:** When Narrative Consensus is high (all sources agree "bullish") but Narrative Intensity is decelerating while price is flat or falling, SignalIQ flags potential Narrative Exhaustion.

*Full methodology for sentiment classification, threshold calibration, and backtested consensus values available under NDA.*

---

## 8. Company-Level Coverage

SignalIQ monitors:

- Company-specific news
- Earnings coverage
- Analyst commentary
- Sector developments
- Executive announcements
- Regulatory events

Coverage is focused on large-cap and systemically important U.S. companies.

---

## 9. Sector-Level Coverage

SignalIQ monitors narrative developments across:

- Technology
- Financial Services
- Energy
- Industrials
- Healthcare
- Consumer
- Semiconductors

The objective is to identify emerging narrative concentrations before they appear in broad market indices.

---

## 10. Information Philosophy

SignalIQ assumes that no individual source possesses complete information.

Market narratives emerge from the interaction of thousands of independent information signals.

The objective is not to predict the future from a single article.

The objective is to measure how collective narratives evolve, strengthen, weaken, and diverge from underlying market behavior.

---

**SignalIQ**

---

