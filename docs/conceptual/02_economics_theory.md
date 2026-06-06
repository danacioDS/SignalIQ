
---

# SignalIQ Background Theory

## The Three Scientific Pillars of the Narrative Divergence Index (NDI)

---

## 1. Animal Spirits

**Keynes (1936); Akerlof & Shiller (2009)**

### Core Idea

Economic decisions are not purely rational. They are driven by confidence, fear, enthusiasm, and collective narratives.

### Application in SignalIQ

Financial news is the observable manifestation of animal spirits. When news sentiment is extremely positive but prices are not rising, animal spirits are decoupling from rational price discovery.

### Foundational Quote

> *"Keynes argued that markets are driven by 'animal spirits' — spontaneous optimism. SignalIQ quantifies the gap between that optimism (news sentiment) and rational price discovery."*

### Behavioral Foundation

Daniel Kahneman and Amos Tversky demonstrated that humans do not process all available information. They use mental shortcuts called heuristics, which generate systematic biases:

- **Overconfidence:** Investors overestimate their ability to interpret news
- **Loss aversion:** Bad news has a disproportionate impact on perception
- **Representativeness bias:** A compelling narrative is overweighted relative to less striking but more objective evidence (prices)

Robert Shiller (1981) empirically demonstrated that stock prices are too volatile to be explained only by future dividends. That extra volatility comes from narratives and emotions.

### Application in SignalIQ

Investors overweight narrative information (easy-to-understand news, sticky stories) and underweight the price signal (which requires technical analysis). SignalIQ automatically corrects this bias by cross-referencing both sources.

---

## 2. Bounded Rationality and Heuristics

**Kahneman & Tversky (1979); Shiller (1981)**

### Core Idea

Investors do not process all available information. They use mental shortcuts (heuristics) that generate systematic biases: overconfidence, anchoring, representativeness, and loss aversion.

### Application in SignalIQ

Narrative-price divergence occurs because investors overweight narrative information (easy-to-understand news, sticky stories) and underweight the price signal (which requires technical analysis).

### Foundational Quote

> *"Kahneman and Tversky showed that humans overreact to salient narratives. SignalIQ detects when that overreaction stops being reflected in prices."*

### Key Biases

| Bias | Definition | Relevance to Divergence |
|------|-----------|------------------------|
| Overconfidence | Investors overestimate their ability to interpret information | Delays price correction after narrative peaks |
| Loss aversion | Bad news weighted more heavily than good news | Asymmetric narrative-price response |
| Representativeness | A compelling story overweights objective evidence | Narratives persist after price confirms them |

### Application in SignalIQ

SignalIQ automatically corrects this bias by cross-referencing both information streams.

---

## 3. Overshooting in Asset Markets

**Dornbusch (1976); De Long et al. (1990)**

### Core Idea

In markets with noise and slow feedback, prices overreact initially and then correct.

### Application in SignalIQ

When the Narrative Divergence Index (NDI) is high (very positive narrative, flat or falling prices), SignalIQ is detecting the peak of overshooting.

### Foundational Quote

> *"Dornbusch's overshooting model explains why asset prices initially overreact to narratives. SignalIQ measures when that overshooting has exhausted itself."*

### Conditions That Enable Overshooting

- Asymmetric information
- Delayed feedback loops
- Noise and uninformed traders

### Application in SignalIQ

High NDI values indicate the narrative overshoot peak. When narrative intensity remains elevated but price momentum fails to confirm, the overshoot has likely exhausted itself.

---

## 4. Why This Is Not Market Efficiency

The Efficient Market Hypothesis (Fama, 1970) holds that prices reflect all available information. SignalIQ does not contradict long-term efficiency.

### What Research Shows

- Markets are efficient over long horizons (years), but inefficient over short horizons (days or weeks)
- Anomalies exist systematically: momentum, medium-term reversal, excess volatility
- Narratives take time to be incorporated into prices because investors need time to process, believe, and act

### SignalIQ Positioning

SignalIQ operates in the short term (days to weeks), where temporary inefficiencies exist and are measurable. It does not challenge long-term market efficiency.

---

## 5. The SignalIQ Hypothesis

### Central Hypothesis

> *Over horizons of days to weeks, aggregate news sentiment and price momentum can systematically diverge. This divergence is a statistically significant predictor of impending corrections or consolidations, because it represents an exhaustion of animal spirits without price validation.*

### Simplified Version

> *When the story is very good but prices stop rising, the story is about to get tired.*

---

## 6. What SignalIQ Does Not Do

| Not this | Because |
|----------|---------|
| Predict the future | Does not say "the market will fall X% in Y days" |
| Guarantee market corrections | Measures divergence, not certainty |
| Work reliably during extreme systemic crises | In 2008 or COVID, everything collapses simultaneously — divergence disappears because narrative and prices align in panic |
| Replace human analysts | Provides a systematic second opinion |

### What SignalIQ Does Do

- Measures divergence: "Today, the narrative is at this level, prices are at this other level, and the gap between them is abnormal according to historical data"
- Quantifies narrative exhaustion
- Provides a systematic second opinion
- Highlights abnormal conditions as attention signals, not sentences

---

## 7. Narrative Divergence Index (NDI)

### Definition

The Narrative Divergence Index (NDI) measures the distance between aggregate media sentiment and price momentum, normalized by historical volatility.

### Formula

```
NDI(t) = [ S_news(t) - μ_s ] / σ_s - [ M_price(t) - μ_m ] / σ_m
```

### Where

| Variable | Definition |
|----------|------------|
| S_news(t) | Average news sentiment over window t (e.g., 5 days) |
| M_price(t) | Price momentum over window t (e.g., cumulative 5-day return) |
| μ_s, σ_s | Historical mean and standard deviation of sentiment |
| μ_m, σ_m | Historical mean and standard deviation of momentum |

### Interpretation

| NDI Value | Interpretation |
|-----------|----------------|
| NDI ≈ 0 | Narrative-price alignment |
| NDI > 1.5 | Significant divergence (narrative far ahead of price) |
| NDI < -1.5 | Inverse divergence (price rising without narrative support) |

---

## 8. Academic References That Support the NDI

| Paper | Key Finding | Application to NDI |
|-------|-------------|---------------------|
| Shiller (1981) - "Do Stock Prices Move Too Much?" | Prices are more volatile than dividends → excess reaction to narratives | NDI measures that excess |
| Barberis, Shleifer & Vishny (1998) | Model of investor sentiment with conservatism and representativeness bias | Divergence occurs when representativeness bias exhausts itself |
| Tetlock (2007) - "Giving Content to Investor Sentiment" | Media sentiment predicts short-term prices, but reverses | NDI detects the reversal point |
| Malkiel (2003) - "The Efficient Market Hypothesis and Its Critics" | Markets are not completely efficient in short horizons | Justifies why divergence can exist and be exploitable |

---

## 9. Full Academic References

1. Keynes, J. M. (1936). *The General Theory of Employment, Interest and Money*. Chapter 12.

2. Akerlof, G. A., & Shiller, R. J. (2009). *Animal Spirits: How Human Psychology Drives the Economy and Why It Matters for Global Capitalism*. Princeton University Press.

3. Kahneman, D., & Tversky, A. (1979). Prospect Theory: An Analysis of Decision under Risk. *Econometrica*, 47(2), 263-291.

4. Shiller, R. J. (1981). Do Stock Prices Move Too Much to Be Justified by Subsequent Changes in Dividends? *American Economic Review*, 71(3), 421-436.

5. Dornbusch, R. (1976). Expectations and Exchange Rate Dynamics. *Journal of Political Economy*, 84(6), 1161-1176.

6. De Long, J. B., Shleifer, A., Summers, L. H., & Waldmann, R. J. (1990). Noise Trader Risk in Financial Markets. *Journal of Political Economy*, 98(4), 703-738.

7. Fama, E. F. (1970). Efficient Capital Markets: A Review of Theory and Empirical Work. *Journal of Finance*, 25(2), 383-417.

8. Tetlock, P. C. (2007). Giving Content to Investor Sentiment: The Role of Media in the Stock Market. *Journal of Finance*, 62(3), 1139-1168.

9. Barberis, N., Shleifer, A., & Vishny, R. (1998). A Model of Investor Sentiment. *Journal of Financial Economics*, 49(3), 307-343.

10. Malkiel, B. G. (2003). The Efficient Market Hypothesis and Its Critics. *Journal of Economic Perspectives*, 17(1), 59-82.

---

## 10. Academic Summary Paragraph

*This system implements a quantitative measure of narrative divergence grounded in three established frameworks: (1) Keynesian animal spirits as a driver of sentiment cycles, (2) Kahneman and Tversky's bounded rationality to explain persistent mispricing, and (3) Dornbusch's overshooting model as the theoretical mechanism for price-sentiment decoupling. The resulting Narrative Divergence Index (NDI) extends Tetlock (2007) by explicitly modeling the divergence between news sentiment and price momentum, rather than predicting absolute returns.*

---

## 11. Commercial Defense Against Overfitting

### Market Question

*"How do you know this isn't just overfitting?"*

### Answer

Because SignalIQ is not predicting. It is measuring a divergence that has ninety years of academic backing.

Keynes talked about animal spirits. Shiller demonstrated that prices overreact to narratives. Tetlock quantified that media sentiment predicts reversals.

The system does not invent anything new. It brings together three established ideas into a simple indicator:

> *NDI = normalized sentiment − normalized momentum*

When narrative gets too far ahead of prices, historically that has been a signal of exhaustion — not a magic prediction.

---

## 12. Scientific Foundation Summary

| System Component | Scientific Foundation | Author / School |
|-----------------|----------------------|------------------|
| Measuring news sentiment | Animal spirits | Keynes, Akerlof & Shiller |
| Detecting narrative-price divergence | Bounded rationality, heuristics | Kahneman & Tversky |
| Alerting on narrative exhaustion | Overshooting | Dornbusch |
| Measuring distance, not prediction | Short-term inefficiency | Shiller, Tetlock, Malkiel |

---

**SignalIQ — Measuring the distance between stories and prices.**

---
