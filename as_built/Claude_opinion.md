The repo is already cloned. Let me read only what I haven't fully covered yet.Now I have read every document in the repo. Here is the updated review, focused on what the previous two passes missed.

---

## SignalIQ — fourth pass review

This pass covers the documents not yet read: the unified spec (`SignalIQ_mvp_uni_exec.md`), the full product engineering doc, the output specification, the Layer 3 HLD contract, the Layer 4 dev transcript, and the git log.

---

### What the previous reviews missed

**The product has three outputs, not one.** The `product_expectations.md` defines:

1. A **bubble risk probability table** per asset, including a logistic regression model: `P(correction > 5% in 10 days) = logistic(β₀ + β₁·NDI + β₂·NDI_percentile + β₃·volatility_regime)`, with asset-class-specific β coefficients estimated from walk-forward validation.
2. A **statistical summary box** per asset including 5-day and 20-day ΔNDI, NDI z-score, NDI percentile, 90-day extremes, KS goodness-of-fit test p-value against N(0,2), and a distribution status flag.
3. A **two-paragraph automated analysis** with a narrative context paragraph and a divergence analysis paragraph, generated from structured templates.

The current Layer 4 code produces none of these. It produces a `risk_level` string and an `attention` sentence. The gap between the specified output and the implemented output is large — the β coefficients don't exist, the NDI percentile computation (252-day lookback) isn't implemented, the KS test isn't implemented, and the two-paragraph generation is not wired up. The Anthropic Claude API is listed in the tech stack explicitly for report generation (Layer 5), which is entirely unbuilt.

**The full vision is substantially bigger than the MVP core.** The `product_engineering.md` reveals a post-MVP feature set that includes: a Bubble Risk Score (0–100 composite of Narrative, Technical, Fundamental, and Macro scores), a Market Stress Score (global risk-on/risk-off indicator from intermarket relationships), a Fundamental Analysis Engine (P/E, EPS growth, ROE, free cash flow), a Technical Analysis Engine (RSI, MACD, EMAs), a Vector Database for semantic embeddings, and an AI Co-Pilot chat interface. None of this is in scope for MVP and none of it has any code, but it's important context — the current codebase implements roughly Layer 3 sentiment + momentum and Layer 4 NDI classification, which is one pillar of a much larger intended product.

**The Layer 4 dev transcript reveals the engineering process.** `transcript_layer_04.md` is a full record of a code review and three rounds of remediation. It documents exactly which issues were found and fixed: the `save()` visibility bug (was writing to disk on every asset update), the hardcoded state file path, the LLD/architecture doc mismatch, unsorted batch output, and missing `price_modifier` and `persistence_days` fields in the output schema. The transcript also records things deliberately left unchanged, with explicit rationale. This is useful project management context: the current code is not at a first-draft quality level — it has gone through structured review and hardening.

**The git log tells the development story.** Twenty commits, all with the generic message "commit" except three: `Create Layer_03_arch.md`, `Create SignalIQ_layer_03.md`, and `Update README.md` / `Update SignalIQ_mvp_uni_exec.md`. This is consistent with LLM-assisted development where the author is iterating fast and not writing descriptive commit messages. It makes the git history useless for understanding what changed between commits.

---

### Discrepancy between the unified spec and the code

The `SignalIQ_mvp_uni_exec.md` (the "frozen" master spec) defines five regimes based on both NDI and price direction:

| NDI | Price | Regime |
|---|---|---|
| < -1.5 | Rising or Flat | Silent Accumulation |
| -1.5 to 1.5 | Any | Aligned |
| > 1.5 | Rising or Flat > -0.5% | Narrative Exhaustion |
| > 1.5 | Flat 0 to -0.5% | Divergence Warning |
| > 1.5 | Falling < -0.5% | Severe Divergence |

The actual Layer 4 code implements only **three regimes** (ALIGNED, ACCUMULATION_DIVERGENCE, OVERHEATING_DIVERGENCE) based on NDI alone, with price used only to escalate risk level within OVERHEATING_DIVERGENCE. The five-regime taxonomy from the unified spec is not implemented in the code. The HLD spec and the implementation are out of sync on this specific point. This isn't necessarily wrong — the architecture docs explicitly say Layer 4 evolved through multiple revisions — but the unified spec is marked "FROZEN" and "ready for implementation," suggesting this gap is unintentional.

---

### What the validation framework requires vs. what exists

The validation spec requires:
- 252-day NDI history per asset to compute percentiles
- β coefficients for the logistic correction probability model (estimated from walk-forward validation)
- KS test against N(0,2) distribution per asset
- Jonckheere-Terpstra test for regime monotonicity
- Mann-Whitney U test for divergence vs baseline

None of this exists. The current persistence tracker stores only streak count and last NDI value — it has no NDI history. Building the validation framework requires first building a historical NDI store, which requires first running the pipeline on real data, which requires Layers 1 and 2.

The validation spec is well-designed but it's describing a post-MVP deliverable. The current code can't be validated against these criteria yet because the data infrastructure doesn't exist.

---

### Scorecard: spec vs. reality

| Component | Specified | Implemented |
|---|---|---|
| Layer 1 ingestion | Full spec, frozen | None |
| Layer 2 PostgreSQL schema | Full spec, SQL written | None |
| Layer 3 sentiment (Loughran-McDonald) | Yes | Yes |
| Layer 3 momentum (daily returns) | Yes | Yes |
| Layer 3 entity resolution | Yes | Yes (aliases empty) |
| Layer 3 → Layer 4 pipeline orchestrator | Yes, 4.5hr estimate | None |
| Layer 4 NDI + 3-regime classification | Partially (spec has 5 regimes) | Yes |
| Layer 4 persistence streak filter | Yes | Yes |
| NDI percentile (252-day history) | Yes | None |
| Logistic correction probability model | Yes | None |
| KS goodness-of-fit test | Yes | None |
| Layer 5 AI report generation | Listed in tech stack | None |
| Layer 6 UI/dashboard | Described | None |
| Two-paragraph automated analysis | Full template | None |
| Bubble Risk Score (0–100) | Full spec | None |
| Validation framework (KS, Mann-Whitney, JT) | Full spec | None |

---

### The honest summary

Three reviews in, the picture is now stable. The repo contains:

- Roughly 30–35% of the MVP as specified in the frozen unified spec
- 100% of the documentation for the MVP
- ~10% of the post-MVP product vision

The implemented code is genuinely well-engineered within its scope — the review-and-remediation cycle documented in the Layer 4 transcript produced clean, tested code. The documentation is unusually thorough and internally consistent (with the one five-regime vs three-regime discrepancy noted above).

The critical path to a working MVP is: populate the two data files (`entity_aliases.json` and the Loughran-McDonald CSV), build the `SignalPipelineOrchestrator`, build Layer 1, stand up Layer 2 in PostgreSQL, and wire up Claude API calls for the two-paragraph report generation. The first of those is 10 minutes of typing; the rest is probably 2–3 focused weeks of work.