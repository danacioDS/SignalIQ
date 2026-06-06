
---

# SignalIQ Operational Strategy

## Objective

SignalIQ monitors the global financial system across multiple levels of market information to identify divergences between narratives, fundamentals, and market behavior.

Rather than focusing on a single asset class, the platform evaluates how capital flows through currencies, fixed income, commodities, equity indices, and individual companies.

The objective is to detect situations where market narratives become disconnected from underlying market reality.

The output of all eight levels feeds into the Narrative Divergence Index (NDI). See Commercial Pitch for NDI construction and interpretation.

---

## Level 1: Global Monetary Environment

**Purpose:** Establish the direction and strength of global capital flows.

The U.S. dollar is the primary reserve currency. Its movements influence all other asset classes. SignalIQ continuously evaluates the relative strength of the U.S. dollar against major global currencies.

### Monitored Currency Pairs

| Currency | Rationale |
|----------|-----------|
| CNY | Primary U.S. trade and strategic competitor |
| JPY | Major reserve currency, carry trade benchmark |
| EUR | Largest non-U.S. developed market bloc |
| GBP | Liquid proxy for European ex-Eurozone sentiment |


### What This Level Provides

- Direction of dollar strength or weakness
- Implied capital flow pressure on emerging and developed markets
- Early signal for commodity price trends (dollar inverse correlation)
- Context for central bank policy divergence

**Output to NDI:** Baseline risk adjustment factor applied to all asset-level divergence scores.

---

## Level 2: Sovereign Bond Markets

**Purpose:** Measure the market's forward view on inflation, growth, and systemic risk.

Government bond markets are the foundation of global capital allocation. They reflect institutional expectations more accurately than any other asset class.

### Monitored Markets

| Market | Benchmark | What It Signals |
|--------|-----------|------------------|
| United States | 2Y / 10Y Treasury | Global risk-free rate, recession probability (yield curve) |
| United Kingdom | 10Y Gilt | Fiscal credibility, Brexit impact |
| Japan | 10Y JGB | BOJ intervention, deflationary pressures |
| China | 10Y CGB | Slowing growth, property sector stress |
| Eurozone | 10Y Bund (Germany) | Regional divergence (periphery spreads) |

### Key Indicators Derived

- Yield curve slope (2s10s) for recession probability
- Real yields (nominal minus inflation breakevens)
- Term premium (investor demand for duration risk)
- Cross-border spread differentials (capital flight detection)

**Output to NDI:** Macro risk regime (risk-on / risk-off) that weights all lower-level divergence signals.

---

## Level 3: Strategic Commodities

**Purpose:** Detect real-economy inflation pressure, supply shocks, and geopolitical stress.

Commodities are often the first asset class to move on macroeconomic shifts before equities react.

### Monitored Commodities

| Commodity | Category | What It Signals |
|-----------|----------|------------------|
| Crude Oil | Energy | Global demand, supply shocks, inflation |
| Gold | Precious metal | Real yields, safe-haven demand, dollar hedging |
| Copper | Industrial metal | Manufacturing activity, global growth (Dr. Copper) |
| Wheat | Agriculture | Food inflation, geopolitical supply risk |
| Lithium | Manufacturing input | Energy transition demand, EV supply chain stress |

### What This Level Provides

- Inflation leading indicator (six months ahead of CPI)
- Industrial demand signal (copper)
- Risk-off confirmation (gold rising with yields)
- Geopolitical shock detection (price spikes without fundamental change)

**Output to NDI:** Inflation pressure score and geopolitical risk overlay.

---

## Level 4: Global Equity Indices

**Purpose:** Measure aggregate investor sentiment and regional risk appetite.

Equity indices reflect the market's collective judgment on future corporate earnings and economic growth.

### Monitored Indices

| Index | Region | What It Signals |
|-------|--------|------------------|
| Nasdaq 100 | US | Technology sentiment, growth expectations |
| S&P 500 | US | Broad US market, sector rotation |
| Nikkei 225 | Japan | Yen correlation, global trade exposure |
| FTSE 100 | UK | Commodity/energy exposure, Brexit residual |
| STOXX 600 | Europe | Eurozone growth, political risk |
| Shanghai Composite | China | Policy intervention, property crisis |

### What This Level Provides

- Regional divergence (US vs. rest of world)
- Factor rotation (growth vs. value)
- Breadth and participation (advance/decline lines)
- Correlation shifts (risk-on/risk-off confirmation)

**Output to NDI:** Regional sentiment baseline and divergence calibration for Level 5 sector analysis.

---

## Level 5: Sector Intelligence

**Purpose:** Identify narrative concentrations and divergences before they appear in broad indices.

Sector-level analysis is the core of SignalIQ's divergence detection. Each sector contains a representative basket of leading publicly traded companies. See Data Acquisition Strategy, Section 8, for selection methodology.

### Monitored Sectors and Representative Companies

| Sector | Representative Companies |
|--------|--------------------------|
| Technology | Microsoft, Apple, Alphabet, Meta, Amazon |
| Financial Services | JPMorgan Chase, Bank of America, Goldman Sachs, Morgan Stanley, Berkshire Hathaway |
| Energy | Exxon Mobil, Chevron, ConocoPhillips, Schlumberger, Occidental Petroleum |
| Healthcare | Johnson & Johnson, UnitedHealth Group, Pfizer, Merck, Eli Lilly |
| Consumer | Walmart, Costco, Procter & Gamble, Coca-Cola, Tesla |
| Industrials | Caterpillar, General Electric, Honeywell, Union Pacific, Boeing |
| Semiconductors | NVIDIA, AMD, Intel, Broadcom, Qualcomm |

*NVIDIA appears only in Semiconductors to prevent double-counting in divergence aggregation.*

### What This Level Provides

- Sector-level divergence (narrative vs. price)
- Rotation detection (capital moving between sectors)
- Leadership changes (which sectors are driving indices)
- Concentration risk (one sector dominating narrative)

**Output to NDI:** Asset-level divergence scores aggregated into sector risk surfaces.

---

## Level 6: Narrative Intelligence

**Purpose:** Quantify collective market sentiment and identify changes in narrative intensity.

This level implements the data acquisition framework described in Data Acquisition Strategy, Sections 3-7. SignalIQ continuously evaluates financial news and market narratives without asserting which sources are correct.

### Narrative Sources by Tier

| Tier | Sources | Influence Weight |
|------|---------|------------------|
| 1 | Reuters, Associated Press, CNBC, Bloomberg (public), Yahoo Finance | Very High / High |
| 2 | MarketWatch, Seeking Alpha, Motley Fool, Barron's public | Medium |
| 3 | Financial blogs, industry pubs, company commentary | Low |

### Narrative Metrics Calculated

- **Narrative Intensity:** Volume and velocity of coverage
- **Narrative Consensus:** Degree of agreement across sources
- **Narrative Dispersion:** Degree of disagreement
- **Sentiment Balance:** Positive / neutral / negative ratio

### What This Level Provides

- Early warning when narrative intensity decouples from price
- Detection of consensus bubbles (everyone agrees, price stops moving)
- Identification of narrative concentration in one editorial quadrant
- Quantification of hype vs. fundamentals

**Output to NDI:** Narrative Intensity score (Pillar 1 of the NDI). See Commercial Pitch.

---

## Level 7: Technical and Fundamental Assessment

**Purpose:** Provide the price and fundamental context against which narrative intensity is compared.

For every monitored company and sector, SignalIQ performs two complementary evaluations. These form Pillar 2 of the NDI (Price Action).

### Technical Assessment

| Metric | What It Measures |
|--------|------------------|
| Price momentum | Direction and strength of trend |
| Relative strength | Performance vs. sector and market |
| Volatility | Risk-adjusted movement |
| Trend persistence | Sustainability of price direction |
| Volume behavior | Confirmation or divergence of price moves |

### Fundamental Assessment

| Metric | What It Measures |
|--------|------------------|
| Revenue growth | Top-line expansion |
| Earnings growth | Bottom-line performance |
| Profitability margins | Operational efficiency |
| Valuation multiples | Price relative to fundamentals (P/E, P/S, EV/EBITDA) |
| Balance sheet quality | Leverage, liquidity, solvency |

### What This Level Provides

- Confirmation when price supports narrative
- Warning when price diverges from narrative
- Context for whether valuation justifies optimism
- Detection of deteriorating fundamentals with rising prices (bubble fuel)

**Output to NDI:** Price Action score (Pillar 2) and fundamental health overlay.

---

## Level 8: Bubble Risk Detection

**Purpose:** Synthesize all seven lower levels into a single judgment on narrative-health-price alignment.

This is the final output of the operational strategy. It feeds directly into the NDI's Divergence Score (Pillar 3) and the four-regime classification.

### Conditions That Trigger Elevated Divergence

SignalIQ flags an asset or sector for bubble risk review when the following occur simultaneously:

- Narrative intensity is high and rising (Level 6)
- Narrative consensus is strong across all source tiers (Level 6)
- Price momentum is flat or declining (Level 7 technical)
- Valuation multiples are stretched relative to history (Level 7 fundamental)
- Fundamentals (revenue, earnings) no longer support the narrative (Level 7 fundamental)

### What This Level Does Not Do

The system does not predict market crashes. It does not issue sell signals. It does not assert that elevated divergence will resolve through price decline rather than narrative correction.

### What This Level Provides

- Systematic identification of assets where risk surface has changed
- Prioritization of which divergences warrant investment committee review
- Historical context (how previous similar divergences resolved)
- Audit trail of which conditions triggered the alert

**Output to NDI:** Divergence Score (Pillar 3) and Regime Classification (Aligned / Exhaustion / Warning / Critical). See Commercial Pitch for interpretation.

---

## Summary: How the Levels Work Together

| Level | Domain | Primary Output | Feeds Into |
|-------|--------|----------------|------------|
| 1 | Currency | Risk adjustment factor | NDI baseline |
| 2 | Bonds | Macro risk regime | NDI weighting |
| 3 | Commodities | Inflation & geopolitics | NDI overlay |
| 4 | Indices | Regional sentiment | Level 5 calibration |
| 5 | Sectors | Asset-level divergence | NDI Pillar 2 |
| 6 | Narratives | Narrative Intensity | NDI Pillar 1 |
| 7 | Tech/Fund | Price Action | NDI Pillar 2 |
| 8 | Synthesis | Divergence Score & Regime | NDI Pillar 3 |

---

**SignalIQ**

---
