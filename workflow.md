## SignalIQ Development Methodology — Complete Workflow

Your methodology flows from **why** (conceptual) → **what** (design) → **how** (implementation) in six distinct phases.

---

## Phase 0: Conceptual Foundation

**Purpose:** Establish the investment thesis, economic rationale, and strategic positioning before any design or code.

**Documents (already complete):**

| # | Document | Question It Answers |
|---|----------|---------------------|
| 01 | Commercial Pitch | Why does this product need to exist? Who pays for it? |
| 02 | Economics Theory | What behavioral economics principles justify the approach? (Keynes, Minsky, Tetlock) |
| 03 | Statistics Theory | How do we measure divergence? Why z-scores? What validation tests? |
| 04 | Commercial Strategy | How does this compete? What's the moat? |
| 05 | Data Acquisition | What data sources? Why these sources? |
| 06 | Operational Strategy | How does this scale to multiple asset classes? |

**Gate condition:** Conceptual docs reviewed and approved by stakeholders.

**Output:** Confidence that the product idea is sound before spending engineering time.

---

## Phase 1: High-Level Design (HLD)

**Purpose:** Translate conceptual foundation into system architecture. Define layers, data flows, and component boundaries without implementation details.

**Documents:**
- `docs/hld/SignalIQ_mvp_plan.md` — 6-layer architecture, data flow diagrams, technology choices
- `docs/hld/product_engineering.md` — Feature scope, MVP boundaries, post-MVP roadmap
- `docs/hld/product_expectations.md` — Output specifications, validation criteria, success metrics

**Key decisions made here:**
- 6-layer architecture (Collection → Storage → Intelligence → Signal → AI → UI)
- NDI as the core metric
- PostgreSQL for structured data, vector DB for embeddings (post-MVP)
- Walk-forward validation framework

**Gate condition:** HLD reviewed, dependencies identified, resource estimates approved.

**Output:** System block diagram with clear layer boundaries.

---

## Phase 2: Low-Level Design (LLD)

**Purpose:** Detailed technical specifications for each layer. Function signatures, API contracts, database schemas, error handling rules.

**Documents (one per layer):**
- `docs/lld/SignalIQ_layer_01.md` — Data ingestion: Yahoo API, RSS parsing, retry logic, lock files
- `docs/lld/SignalIQ_layer_02.md` — PostgreSQL: 10 tables, 13 functions, triggers, roles
- `docs/lld/SignalIQ_layer_03.md` — NLP: Entity resolution, sentiment lexicon, rolling z-scores
- `docs/lld/SignalIQ_layer_04.md` — Signal: NDI calculation, persistence, regimes, confidence
- `docs/lld/SignalIQ_layer_05.md` — AI: Summarization, entity intelligence, co-pilot prompts
- `docs/lld/SignalIQ_layer_06.md` — UI: Dashboards, asset views, chat interface

**Each LLD includes:**
- Function signatures with parameter types and return types
- Expected behavior for happy path and all error conditions
- Data schemas (JSON, SQL DDL, or both)
- Test criteria (what must be tested)
- Dependencies on other layers

**Gate condition:** LLD reviewed for completeness, no ambiguities, all edge cases covered.

**Output:** A document that an independent engineer could implement from without asking questions.

---

## Phase 3: Production Specification

**Purpose:** A single, frozen master document that unifies HLD and LLD into an executable specification. This is the "contract" between design and implementation.

**Document:** `docs/hld/SignalIQ_mvp_uni_exec.md`

**What it contains:**
- Executive summary (one page)
- Complete architecture diagram
- Layer-by-layer specifications (synthesized from HLD + LLD)
- Data flow descriptions
- Validation criteria (statistical tests, acceptance criteria)
- Success metrics

**Why this exists:** The unified spec prevents HLD/LLD drift. When HLD and LLD conflict, the unified spec is truth.

**Gate condition:** Unified spec frozen. No changes without formal change request.

**Output:** A single document that drives all implementation prompts.

---

## Phase 4: Prompt Generation

**Purpose:** Convert the unified spec into executable prompts for each module. Each prompt is self-contained and testable.

**Documents:** `docs/prompts/prompts_layer_XX.md`

**Prompt structure (from your Layer 4 prompts):**

| Section | Content |
|---------|---------|
| Overview | What this module does, why it exists |
| Input specification | Function signatures, expected data shapes |
| Output specification | Return values, side effects |
| Error handling | Table of error types → actions |
| Retry logic | If applicable |
| CLI | Command-line interface if applicable |
| Test criteria | What must be tested |
| Example | Input/output example |

**Gate condition:** Prompts reviewed for clarity, no ambiguities, testable.

**Output:** A set of prompts that a coding agent (human or LLM) can execute in order.

---

## Phase 5: Implementation

**Purpose:** Execute prompts to produce code, tests, and deployment artifacts.

**Process for each layer:**
1. Execute Prompt 1 → module 1 → test → commit
2. Execute Prompt 2 → module 2 → test → commit
3. ...continue through all prompts for the layer
4. Run full layer test suite
5. Verify no regressions in existing layers
6. Tag release (e.g., `v0.2-with-layer1`)

**Order of implementation (from your actual build):**
- Layer 4 first (signal generation) — proves the math works
- Layer 3 second (NLP) — provides inputs to Layer 4
- Layer 2 third (database) — stores outputs from L3/L4
- Layer 1 fourth (ingestion) — feeds data into L2
- Layer 5 fifth (AI) — enhances L4 outputs
- Layer 6 sixth (UI) — presents everything

**Gate condition:** All tests pass, no regressions, synthetic demo works.

**Output:** Working code, passing tests, deployment artifacts.

---

## Phase 6: Validation

**Purpose:** Verify that the implemented system meets the success criteria defined in conceptual and HLD phases.

**Validation activities:**
- Walk-forward validation (252-day training, 21-day testing)
- KS test for NDI ~ N(0,2)
- AUC-ROC for correction prediction
- Regime monotonicity tests (Jonckheere-Terpstra)
- Divergence vs baseline (Mann-Whitney U)

**Gate condition:** All validation criteria met or explicitly waived for MVP.

**Output:** Validation report, confidence to deploy.

---

## Complete Workflow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PHASE 0: CONCEPTUAL                               │
│  01_pitch → 02_economics → 03_statistics → 04_strategy → 05_data → 06_ops  │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PHASE 1: HIGH-LEVEL DESIGN                        │
│         mvp_plan.md ← product_engineering.md ← product_expectations.md      │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PHASE 2: LOW-LEVEL DESIGN                         │
│     layer_01.md ← layer_02.md ← layer_03.md ← layer_04.md ← layer_05.md    │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        PHASE 3: PRODUCTION SPECIFICATION                     │
│                    SignalIQ_mvp_uni_exec.md (FROZEN)                        │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PHASE 4: PROMPT GENERATION                        │
│              prompts_layer_01.md → prompts_layer_02.md → ...               │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PHASE 5: IMPLEMENTATION                           │
│     L4 → L3 → L2 → L1 → L5 → L6 (each with test → commit → tag)           │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PHASE 6: VALIDATION                               │
│     Walk-forward → KS test → AUC-ROC → JT test → MWU test → Report         │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Your Current Status

| Phase | Status |
|-------|--------|
| Phase 0: Conceptual | ✅ Complete (6 docs) |
| Phase 1: HLD | ✅ Complete (but may need updates based on L3/L4 learnings) |
| Phase 2: LLD | ✅ Complete for L2, L3, L4; ⚠️ L1 needs review |
| Phase 3: Unified Spec | ✅ Complete (but has discrepancies with L4 code) |
| Phase 4: Prompts | ✅ Complete for L2, L3, L4; ❌ L1 prompts not yet generated |
| Phase 5: Implementation | ✅ L2, L3, L4 done; ❌ L1 not started; ❌ L5, L6 not started |
| Phase 6: Validation | ❌ Not started (needs data from L1+L2 first) |

---

## What You Should Do Now

1. **Review HLD for Layer 1** — does it still match what you learned from building L3/L4?
2. **Review LLD for Layer 1** — identify gaps, update based on L3/L4 patterns
3. **Update unified spec** — resolve the 3-regime vs 5-regime discrepancy
4. **Generate Layer 1 prompts** — following the same structure as your L4 prompts
5. **Implement Layer 1** from prompts
6. **Test** → **Commit** → **Tag**

Then repeat for Layer 5 and Layer 6.

---

Does this match your actual methodology?