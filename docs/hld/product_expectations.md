
---

# 🗂️ SignalIQ: Output Specification Document

## What the System Produces

SignalIQ extracts data as defined in the Operational Strategy (8 levels) and news from press sources (as defined in the Data Strategy). The system then generates three concrete outputs for each monitored asset, sector, and the global market.

---

## 📊 Output 1: Bubble Risk Probability Table

For each asset (company, index, commodity, currency pair, bond market), SignalIQ generates a table with the following columns:

| Column | Description | Format |
|--------|-------------|--------|
| Asset | Name of the monitored instrument | String |
| Asset Class | Equity / Index / Commodity / FX / Bond | String |
| NDI | Narrative Divergence Index value | Float (2 decimals) |
| NDI Percentile | Historical percentile vs 252-day lookback | Integer (0-100) |
| Bubble Risk Score | Composite score (0-100) | Integer |
| Bubble Risk Probability | Probability of a correction > 5% in next 10 days | Percentage (0-100%) |
| Regime | Color-coded regime from operational definitions | Text |
| Confidence | Based on article count and VIX status | High / Medium / Low / Crisis |

### 📋 Example Table

| Asset | Asset Class | NDI | NDI% | Risk Score | Risk Prob | Regime | Confidence |
|-------|-------------|-----|------|------------|-----------|--------|------------|
| NVIDIA | Equity | 2.34 | 96th | 87 | 64% | 🔴 Critical Divergence | High |
| Apple | Equity | 1.78 | 89th | 72 | 48% | 🟠 Divergence Warning | High |
| S&P 500 | Index | 0.92 | 72nd | 45 | 22% | 🟡 Narrative Exhaustion | High |
| Gold | Commodity | -1.23 | 18th | 18 | 8% | 🔵 Silent Accumulation | Medium |
| Crude Oil | Commodity | 0.34 | 58th | 22 | 12% | 🟢 Aligned | High |
| USD/JPY | FX | -0.89 | 28th | 15 | 6% | 🔵 Silent Accumulation | Medium |
| US 10Y Bond | Bond | 1.45 | 84th | 58 | 34% | 🟡 Narrative Exhaustion | Low |

### 🧮 Bubble Risk Probability Calculation

```
P(correction > 5% in 10 days) = logistic(β₀ + β₁ * NDI + β₂ * NDI_percentile + β₃ * volatility_regime)

Where:
- β coefficients are estimated from historical walk-forward validation
- Validation approach: expanding window with 252-day training, 21-day test, re-estimated quarterly
- Coefficients are asset-class specific (equity, commodity, FX, bond have separate calibrations)
- Logistic function maps output to 0-100%
- Baseline probability (NDI = 0) is approximately 8-12% depending on asset class
```

---

## 📈 Output 2: NDI Statistical Summary

For each monitored asset, SignalIQ generates a statistical summary box.

### 📋 Statistical Summary Fields

| Statistic | Description | Format |
|-----------|-------------|--------|
| Current NDI | Today's value | Float (2 decimals) |
| 5-day ΔNDI | Change over last 5 trading days | Float (2 decimals) |
| 20-day ΔNDI | Change over last 20 trading days | Float (2 decimals) |
| NDI Z-Score | (Current NDI - μ) / σ over 252-day lookback | Float (2 decimals) |
| NDI Percentile | Rank vs 252-day history | Integer (0-100) |
| Days since last >1.5 | Trading days since NDI last exceeded 1.5 | Integer |
| Max NDI (90 days) | Peak value in last 90 days | Float (2 decimals) |
| Min NDI (90 days) | Trough value in last 90 days | Float (2 decimals) |
| KS Test p-value | Goodness-of-fit to N(0,2) over last 252 days | Float (3 decimals) |
| Distribution Status | Normal / Heavy Tails / Non-normal | String |

### 📋 Example Statistical Summary

```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 NVIDIA CORPORATION (NVDA) | Equity
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📈 NDI STATISTICS:
  Current NDI:           2.34
  5-day ΔNDI:           +0.67 ▲
  20-day ΔNDI:          +1.82 ▲
  NDI Z-Score:          2.14σ
  NDI Percentile:       96th
  Days since last >1.5: 0 (today)

📌 EXTREMES (90 days):
  Max NDI:              2.89 (2026-05-15)
  Min NDI:              0.23 (2026-03-10)

📐 DISTRIBUTION FIT (252 days):
  KS Test p-value:      0.18
  Distribution Status:  Normal (cannot reject N(0,2))

⚠️ THRESHOLD STATUS:
  > 1.5 (Warning):      YES
  > 2.5 (Critical):     NO
  > 3.0 (Extreme):      NO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 📝 Output 3: Automated Economic-Financial Analysis (2 Paragraphs)

For each monitored asset or for a daily global summary, SignalIQ generates exactly two paragraphs of automated analysis.

### Paragraph 1: Narrative Context

Describes what the news is saying about the asset.

**Template:**

> *"Over the last [X] days, media narrative around [Asset] has been [predominantly positive / predominantly negative / mixed / neutral]. The highest-weight sources ([Tier 1 sources]) have emphasized [primary themes detected]. Narrative consensus across sources is [high / moderate / low], with sentiment intensity [increasing / stable / decreasing] compared to the previous 5-day window."*

**Example:**

> *"Over the last 5 days, media narrative around NVIDIA has been predominantly positive. The highest-weight sources (Reuters, CNBC, Bloomberg) have emphasized sustained demand for AI chips, better-than-expected quarterly results, and optimistic management guidance. Narrative consensus across sources is high, with sentiment intensity increasing compared to the previous 5-day window."*

---

### Paragraph 2: Divergence Analysis and Risk Implication

Describes the gap between narrative and price, and what it means.

**Template:**

> *"Despite [the prevailing narrative], price action shows [positive momentum / flat momentum / negative momentum] with an NDI accumulation of [X] points over the last [Y] days. The Narrative Divergence Index (NDI) currently stands at [value], representing the [Z]th percentile of its 252-day historical distribution. This configuration is classified as [Regime] and suggests that [narrative has outrun price action / price is moving without narrative support / narrative and price are aligned]. The estimated probability of a correction (>5% in 10 days) is [X]%. [Qualitative recommendation]. SignalIQ will continue monitoring the evolution of this divergence."*

**Example (Positive Divergence - NVIDIA):**

> *"Despite the extremely positive narrative, price action shows flat momentum over the last 5 days, with an NDI accumulation of +1.82 points over the last 20 days. The Narrative Divergence Index (NDI) currently stands at 2.34, representing the 96th percentile of its 252-day historical distribution. This configuration is classified as Critical Divergence 🔴 and suggests that narrative has significantly outrun price action. The estimated probability of a correction (>5% in 10 days) is 64%. Caution and position review are recommended. SignalIQ will continue monitoring the evolution of this divergence."*

**Example (Inverse Divergence - Gold):**

> *"Despite a predominantly neutral or slightly negative narrative, price action shows sustained positive momentum over the last 5 days. The Narrative Divergence Index (NDI) currently stands at -1.23, representing the 18th percentile of its historical distribution. This configuration is classified as Silent Accumulation 🔵 and suggests that price is moving without apparent narrative support, which historically has preceded sustained upward moves. The estimated probability of a correction is low (8%). Monitoring for trend confirmation is recommended."*

---

## 📁 Output Aggregation: Three Report Types

SignalIQ generates these outputs at three levels of aggregation.

### Report Type A: Global Market Summary 🌍

One table + one statistical summary + two-paragraph analysis for the global market (aggregating all assets).

**Frequency:** Daily

**Use case:** Macro overview for portfolio managers

---

### Report Type B: Sector Summary 🏭

One table per sector (technology, financials, energy, etc.) + statistical summary for the sector aggregate + two-paragraph analysis per sector.

**Frequency:** Daily

**Use case:** Sector rotation decisions

---

### Report Type C: Company/Asset Deep Dive 🔍

Individual table for the asset + full statistical summary + two-paragraph analysis specific to that asset.

**Frequency:** On demand or when NDI exceeds thresholds (1.5 or -1.5)

**Use case:** Position-level risk assessment

---

## 📋 Example: Complete Daily Output for S&P 500

### Table

| Asset | Asset Class | NDI | NDI% | Risk Score | Risk Prob | Regime | Confidence |
|-------|-------------|-----|------|------------|-----------|--------|------------|
| S&P 500 | Index | 0.92 | 72nd | 45 | 22% | 🟡 Narrative Exhaustion | High |

### Statistical Summary

```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 S&P 500 INDEX (SPX) | Index
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📈 NDI STATISTICS:
  Current NDI:           0.92
  5-day ΔNDI:           +0.31 ▲
  20-day ΔNDI:          -0.15 ▼
  NDI Z-Score:          0.65σ
  NDI Percentile:       72nd
  Days since last >1.5: 14

📌 EXTREMES (90 days):
  Max NDI:              1.67 (2026-05-18)
  Min NDI:              0.12 (2026-03-25)

📐 DISTRIBUTION FIT (252 days):
  KS Test p-value:      0.31
  Distribution Status:  Normal

⚠️ THRESHOLD STATUS:
  > 1.5 (Warning):      NO
  > 2.5 (Critical):     NO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Two-Paragraph Analysis

> *"Over the last 5 days, media narrative around the S&P 500 has been predominantly positive, though with decreasing intensity. The highest-weight sources (Reuters, CNBC, Bloomberg) have emphasized US consumer resilience, expectations of Federal Reserve rate cuts, and better-than-expected corporate results in the technology sector. Narrative consensus across sources is moderate, with growing dispersion as some media begin to highlight valuation risks and persistent inflationary pressures."*

> *"Despite the positive narrative, price action shows flat momentum over the last 5 days, with a slight NDI accumulation of +0.31 points over the last week. The Narrative Divergence Index (NDI) currently stands at 0.92, representing the 72nd percentile of its 252-day historical distribution. This configuration is classified as Narrative Exhaustion 🟡 and suggests that optimism persists but momentum is weakening. The estimated probability of a correction (>5% in 10 days) is 22%, slightly above the historical baseline. Monitoring is recommended without immediate action. SignalIQ will continue observing whether divergence intensifies in the coming days."*

---

## 📌 Summary: The Three Outputs

| Output | Format | Content | Use Case |
|--------|--------|---------|----------|
| 1 | Table | Asset, Asset Class, NDI, Risk Prob, Regime, Confidence | Quick scan, portfolio triage |
| 2 | Statistical Box | Z-score, percentiles, extremes, KS test, distribution | Deep dive, validation, audit |
| 3 | 2-Paragraph Analysis | Narrative context + divergence + implication | Investment committee, reports |

---

## 🏁 Output Tagline

> *"SignalIQ does not show data. It generates conclusions: bubble probability tables, NDI statistics, and automated economic-financial analysis in two paragraphs."*

---

**SignalIQ** 🔹

---
