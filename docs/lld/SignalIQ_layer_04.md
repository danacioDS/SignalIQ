# SignalIQ Layer 4: Low-Level Design

> **⚠️ SUPERSEDED — This document predates the Architecture specification.**
> See [`Architecture/Layer_04_arch.md`](../Architecture/Layer_04_arch.md) for the
> current, authoritative design. Key differences include inverted-U confidence
> (not monotonic), separated `signal_state` vs `regime`, and a 10-field output
> schema. This LLD is preserved for historical reference only.

## The Core (Unchanged)

> **NDI = sentiment_zscore − momentum_zscore → deterministic regime classification → readable risk signal**

Everything below preserves this core while simplifying execution.

---

## The Three Regimes (Not Five)

| Condition | Regime | Meaning |
|-----------|--------|---------|
| `|NDI| < 1.5` | **Aligned** | Narrative and price in sync |
| `NDI ≤ -1.5` | **Accumulation Divergence** | Price moving without narrative support |
| `NDI ≥ +1.5` | **Overheating Divergence** | Narrative ahead of price reality |

**Why three:** Divergence is the product. Direction matters. Degree matters. H2 ("Narrative Momentum") is not divergence — removed.

---

## Price as Modifier, Not Driver

Price does **not** determine regime. Price **modulates** risk severity.

| Price Direction (5-day) | Modifier | Applies To |
|------------------------|----------|------------|
| Rising (>0.5%) | `trend_supporting` | Any regime |
| Flat (±0.5%) | `trend_stalling` | Overheating Divergence only |
| Falling (<-0.5%) | `trend_collapsing` | Overheating Divergence only |

**Accumulation Divergence** (NDI ≤ -1.5) ignores price direction for regime classification. Price may inform position sizing, not signal.

---

## Confidence: One Rule, Based on |NDI|

| |NDI| | Confidence |
|-----|------------|
| `< 1.0` | Low |
| `1.0 - 2.0` | Medium |
| `≥ 2.0` | High |

**No multi-axis complexity.** Confidence = magnitude.

---

## Persistence Filter (Critical Addition)

Single-day spikes are noise. Require persistence.

| Duration | Action |
|----------|--------|
| 1 day above threshold | Mark as "watch" — no regime triggered |
| 2 consecutive days | Trigger regime |
| 3+ consecutive days | Strengthen confidence (add one level) |

**Example:** NDI = 1.8 for one day → "watching" (no signal). Second day → "Overheating Divergence" with Medium confidence. Third day → High confidence.

**Why this matters:** Reduces false positives. Aligns with how narratives actually persist.

---

## Output Schema (Single, Clean)

```json
{
  "ticker": "NVDA",
  "date": "2026-06-02",
  "ndi": 1.82,
  "regime": "Overheating Divergence",
  "confidence": "Medium",
  "persistence_days": 2,
  "price_modifier": "trend_stalling",
  "risk_flag": "ELEVATED",
  "attention": "Narrative optimism with stalling price. Review position."
}
```

**Field definitions:**

| Field | Source | Values |
|-------|--------|--------|
| `ndi` | Calculated | Float or null |
| `regime` | NDI threshold | Aligned / Accumulation Divergence / Overheating Divergence |
| `confidence` | \|NDI\| | Low / Medium / High |
| `persistence_days` | Consecutive days above threshold | Integer (0 = watching, 1+ = triggered) |
| `price_modifier` | 5-day return | trend_supporting / trend_stalling / trend_collapsing / null |
| `risk_flag` | regime + modifier | NORMAL / ELEVATED / CRITICAL |
| `attention` | Mapped | One-sentence guidance |

---

## Risk Flag Logic (Simple)

| Regime | Modifier | Risk Flag |
|--------|----------|-----------|
| Aligned | any | NORMAL |
| Accumulation Divergence | any | NORMAL |
| Overheating Divergence | trend_supporting | NORMAL |
| Overheating Divergence | trend_stalling | ELEVATED |
| Overheating Divergence | trend_collapsing | CRITICAL |

**Why this matters:** The risk flag is the action signal. Regime is the diagnosis. Do not confuse them.

---

## Decision Flow (Reduced Branches)

```
1. Is NDI null? → Yes → "Insufficient Data" (gray, no action)

2. persistence_days < 2 → "Watching" (no regime, log only)

3. |NDI| < 1.5 → "Aligned" (confidence based on |NDI|)

4. NDI ≤ -1.5 → "Accumulation Divergence" (ignore price)

5. NDI ≥ +1.5 → "Overheating Divergence" (apply price modifier)
```

**Total branches: 5.** Not 12+.

---

## What Is Removed (Core-Preserving)

| Removed | Why |
|---------|-----|
| H2 "Narrative Momentum" | Not divergence |
| Divergence Warning (Orange) | Merged into Overheating + modifier |
| H0-H4 hypothesis bands | Too academic for MVP |
| "State-space model" framing | Product, not research paper |
| Confidence from boundary distance | Too complex; magnitude suffices |
| Asymmetric regime treatment | Accumulation and Overheating now symmetric |

---

## What Is Added (Essential)

| Added | Why |
|-------|-----|
| Persistence filter (2 days) | Reduces false positives |
| Risk flag (NORMAL/ELEVATED/CRITICAL) | Actionable summary |
| Watching state | Logs spikes without triggering |
| Symmetric regime logic | Accumulation and Overheating treated equally |

---

## One-Page Reference (Print This)

```
CORE: NDI = sentiment_zscore - momentum_zscore

REGIMES (based on NDI only):
  |NDI| < 1.5     → Aligned
  NDI ≤ -1.5     → Accumulation Divergence
  NDI ≥ +1.5     → Overheating Divergence

PRICE MODIFIER (Overheating Divergence only):
  rising (>0.5%)   → trend_supporting (NORMAL risk)
  flat (±0.5%)     → trend_stalling (ELEVATED risk)
  falling (<-0.5%) → trend_collapsing (CRITICAL risk)

CONFIDENCE (based on |NDI| only):
  < 1.0   → Low
  1.0-2.0 → Medium
  ≥ 2.0   → High

PERSISTENCE (critical filter):
  Day 1 above threshold → "watching" (no signal)
  Day 2 consecutive    → trigger regime
  Day 3+ consecutive   → confidence +1 level

OUTPUT:
  regime, confidence, persistence_days, price_modifier, risk_flag, attention

SIGNALIQ DOES NOT PREDICT PRICE.
It measures divergence between narrative and price.
```

---

## Implementation Checklist (30 Minutes)

- [ ] Calculate NDI per asset per day
- [ ] Calculate 5-day return per asset
- [ ] Track consecutive days above threshold (stateful)
- [ ] Apply regime logic (5 branches)
- [ ] Assign confidence from |NDI|
- [ ] Assign price modifier from 5-day return
- [ ] Assign risk flag from regime + modifier
- [ ] Generate attention text from risk flag
- [ ] Output JSON with schema above

---

## Layer 4 Status: READY FOR IMPLEMENTATION

> Deterministic. Three regimes. Price as modifier. Confidence from magnitude. Persistence filter. No ML. No state-space framing. No academic overhead. Core intact.

---

**SignalIQ** 🔹

*NDI is measured. Regimes are thresholds. Confidence is magnitude. Risk flags are actions. Persistence prevents noise.*
