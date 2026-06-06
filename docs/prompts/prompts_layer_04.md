# SignalIQ Layer 4: Revised 5 Prompts for OpenCode (v2)

## Fixes Applied

| Issue | Fix |
|-------|-----|
| "Invalid" overloaded | Split into `InvalidInput`, `NoSignal`, `Watching`, `Active` |
| Price history indexing | Changed to `len(price_history) >= 6` and index `-6` |
| Missing enums | Added strict enum definitions at top of each module |
| Streak semantics | Clarified: streak counts ONLY consecutive days above threshold |
| Inverted-U confidence | Added explicit justification comment |
| Race condition | Note added about file locking for production (not MVP) |

---

## Prompt 1: Validity Gate + NDI Calculator

```
Build the first part of SignalIQ Layer 4 (Sublayer 4A: Measurement).

Create a Python module called `layer4_measurement.py` with:

ENUMS (define as strings at top of file):
  VALIDITY_STATE = ["VALID", "INVALID_INPUT", "INSUFFICIENT_PRICE_HISTORY"]

1. A function `validate_input(sentiment_zscore, momentum_zscore, price_history)` that:
   - Returns `("INVALID_INPUT", "sentiment is None")` if sentiment_zscore is None
   - Returns `("INVALID_INPUT", "momentum is None")` if momentum_zscore is None
   - Returns `("INSUFFICIENT_PRICE_HISTORY", f"need 6 prices, got {len(price_history)}")` if len(price_history) < 6
   - Returns `("VALID", None)` otherwise

2. A function `calculate_ndi(sentiment_zscore, momentum_zscore)` that:
   - Returns `None` if either input is None
   - Returns `sentiment_zscore - momentum_zscore` otherwise

3. A function `calculate_5d_return(price_history)` that:
   - Takes a list of closing prices with today as the last element (index -1)
   - Returns `None` if len(price_history) < 6
   - Returns `(price_history[-1] / price_history[-6]) - 1` otherwise
   - NOTE: price_history[-6] is the closing price from 5 trading days ago

4. A main `compute_measurements(sentiment_zscore, momentum_zscore, price_history)` function that:
   - First calls validate_input
   - If not VALID, returns `{"validity_state": state, "validity_reason": reason, "ndi": None, "return_5d": None}`
   - If VALID, returns `{"validity_state": "VALID", "validity_reason": None, "ndi": calculate_ndi(...), "return_5d": calculate_5d_return(...)}`

Add type hints and docstrings. Include example usage in `if __name__ == "__main__"`.
```

---

## Prompt 2: Persistence Tracker (Stateful)

```
Build the persistence tracker for SignalIQ Layer 4 (Sublayer 4B: Signal State).

Create a Python module called `layer4_persistence.py` with:

ENUMS (define as strings):
  SIGNAL_STATE = ["INACTIVE", "WATCHING", "ACTIVE"]
  REGIME = ["ALIGNED", "ACCUMULATION_DIVERGENCE", "OVERHEATING_DIVERGENCE", "INSUFFICIENT_DATA"]

1. A class `PersistenceTracker` that:
   - Stores state in a dictionary: `{ticker: {"streak": int, "last_ndi": float}}`
   - Loads from `persistence_state.json` on init (if file exists)
   - Saves to `persistence_state.json` on every update
   - NOTE: For MVP, no file locking. In production, add `fcntl` or use SQLite.

2. Method `update(ticker, ndi, threshold=1.5)` that:
   - If ndi is None: streak = 0
   - Else if abs(ndi) >= threshold: streak += 1
   - Else: streak = 0
   - Saves state after update
   - Returns the new streak

3. Method `get_signal_state(ticker, ndi)` that:
   - Calls update first
   - Returns "INACTIVE" if streak == 0
   - Returns "WATCHING" if streak == 1
   - Returns "ACTIVE" if streak >= 2

4. Method `get_regime(ndi, threshold=1.5)` that:
   - Returns "INSUFFICIENT_DATA" if ndi is None
   - Returns "ALIGNED" if abs(ndi) < threshold
   - Returns "ACCUMULATION_DIVERGENCE" if ndi <= -threshold
   - Returns "OVERHEATING_DIVERGENCE" if ndi >= threshold

CRITICAL BEHAVIOR NOTES:
- Streak counts ONLY consecutive days where |NDI| >= threshold
- A single day below threshold resets streak to 0
- This is intentional: persistence requires continuous threshold breach

Include example usage showing 5 days of updates for one ticker.
```

---

## Prompt 3: Confidence + Price Pressure

```
Build the confidence and price pressure calculators for SignalIQ Layer 4 (Sublayer 4B).

Create a Python module called `layer4_classification.py` with:

ENUMS:
  CONFIDENCE_LEVEL = ["LOW", "MEDIUM", "HIGH", "INSUFFICIENT_DATA"]
  PRICE_PRESSURE = ["SUPPORTING", "NEUTRAL", "PRESSURING"]
  RISK_LEVEL = ["NORMAL", "ELEVATED", "CRITICAL"]

1. A function `calculate_confidence(ndi)` that implements INVERTED U-SHAPE.
   
   RATIONALE: Extreme NDI values (|NDI| > 2.2) are often noise bursts or sentiment outliers.
   Mid-range NDI (0.8-2.2) represents stable, persistent divergence and is MORE reliable.
   This is intentional and empirically grounded in behavioral finance literature.
   
   Logic:
   - If ndi is None: return "INSUFFICIENT_DATA"
   - If abs(ndi) < 0.8: return "LOW"
   - If 0.8 <= abs(ndi) <= 2.2: return "HIGH"
   - If abs(ndi) > 2.2: return "MEDIUM"

2. A function `calculate_price_pressure(return_5d, flat_threshold=0.005)` that:
   - If return_5d is None: return "NEUTRAL"
   - If return_5d > flat_threshold: return "SUPPORTING"
   - If abs(return_5d) <= flat_threshold: return "NEUTRAL"
   - If return_5d < -flat_threshold: return "PRESSURING"

3. A function `get_risk_level(regime, price_pressure)` that implements ESCALATION RULE:
   - If regime != "OVERHEATING_DIVERGENCE": return "NORMAL"
   - If regime == "OVERHEATING_DIVERGENCE":
       if price_pressure == "NEUTRAL": return "ELEVATED"
       if price_pressure == "PRESSURING": return "CRITICAL"
       return "NORMAL"  # SUPPORTING or any other

4. A function `get_attention_text(risk_level, signal_state, regime)` that returns:
   - If signal_state == "INACTIVE" and regime == "INSUFFICIENT_DATA": 
        "Insufficient data for reliable signal."
   - If signal_state == "INACTIVE" and regime != "INSUFFICIENT_DATA":
        "No divergence signal detected."
   - If signal_state == "WATCHING": 
        "Watching for persistence (needs 2nd consecutive day)."
   - If risk_level == "NORMAL": 
        "No action required."
   - If risk_level == "ELEVATED": 
        "Narrative optimism with stalling price. Review position."
   - If risk_level == "CRITICAL": 
        "Narrative optimism despite falling prices. Elevated caution warranted."
   - Default: 
        "Signal detected. Monitor closely."

Add type hints and docstrings. Include example test cases for each function.
```

---

## Prompt 4: Main Orchestrator

```
Build the main orchestrator for SignalIQ Layer 4 that ties all components together.

Create a Python module called `layer4_orchestrator.py` that:

1. Imports from:
   - `layer4_measurement import compute_measurements`
   - `layer4_persistence import PersistenceTracker`
   - `layer4_classification import calculate_confidence, calculate_price_pressure, get_risk_level, get_attention_text`

2. Defines ENUMS (for reference):
   - OUTPUT_FIELDS = ["ticker", "date", "ndi", "regime", "signal_state", "confidence", "risk_level", "attention"]

3. Defines a function `process_asset(ticker, sentiment_zscore, momentum_zscore, price_history, persistence_tracker, date_string)` that:
   - Step 1: Call compute_measurements to get ndi, return_5d, validity_state
   - Step 2: If validity_state != "VALID", return dict with:
        ticker, date, ndi=None, regime="INSUFFICIENT_DATA", signal_state="INACTIVE", 
        confidence="INSUFFICIENT_DATA", risk_level="NORMAL", attention="Insufficient data."
   - Step 3: Get signal_state from persistence_tracker.get_signal_state(ticker, ndi)
   - Step 4: Get regime from persistence_tracker.get_regime(ndi)
   - Step 5: Calculate confidence from ndi
   - Step 6: Calculate price_pressure from return_5d
   - Step 7: Calculate risk_level from regime and price_pressure
   - Step 8: Calculate attention_text from risk_level, signal_state, regime
   - Step 9: Return dictionary with EXACTLY these 8 fields

4. Defines a function `process_batch(data_dict, persistence_tracker, date_string)` that:
   - Takes input: `{ticker: {"sentiment_zscore": float, "momentum_zscore": float, "price_history": list}}`
   - Loops through all tickers
   - Calls process_asset for each
   - Returns list of output dictionaries

5. The output dictionary MUST have EXACTLY these fields (no more, no less):
   ```python
   {
       "ticker": str,
       "date": str,  # YYYY-MM-DD format
       "ndi": float or None,
       "regime": str,  # From REGIME enum
       "signal_state": str,  # From SIGNAL_STATE enum
       "confidence": str,  # From CONFIDENCE_LEVEL enum
       "risk_level": str,  # From RISK_LEVEL enum
       "attention": str
   }
   ```

Include example usage with mock data for 3 assets over 5 days.
```

---

## Prompt 5: Integration & Testing Suite

```
Build the integration test suite for SignalIQ Layer 4.

Create a Python module called `test_layer4.py` with the following test cases:

TEST 1: Validity Gate
- Valid: sentiment=1.0, momentum=0.5, prices=[100]*6 → valid=True
- None sentiment → validity_state="INVALID_INPUT"
- 5 prices → validity_state="INSUFFICIENT_PRICE_HISTORY"

TEST 2: NDI Calculation
- sentiment=2.0, momentum=0.5 → ndi=1.5
- sentiment=None, momentum=0.5 → ndi=None

TEST 3: Persistence Streak (run sequentially with same tracker)
- Day 1: ndi=1.6 → streak=1, signal_state="WATCHING"
- Day 2: ndi=1.7 → streak=2, signal_state="ACTIVE"
- Day 3: ndi=0.5 → streak=0, signal_state="INACTIVE"
- Day 4: ndi=1.6 → streak=1, signal_state="WATCHING"

TEST 4: Regime Classification
- ndi=0.5 → "ALIGNED"
- ndi=-2.0 → "ACCUMULATION_DIVERGENCE"
- ndi=2.0 → "OVERHEATING_DIVERGENCE"
- ndi=None → "INSUFFICIENT_DATA"

TEST 5: Confidence (Inverted U - intentional)
- ndi=0.5 → "LOW"
- ndi=1.5 → "HIGH"
- ndi=2.5 → "MEDIUM"

TEST 6: Price Pressure
- return=0.01 → "SUPPORTING"
- return=0.002 → "NEUTRAL"
- return=-0.01 → "PRESSURING"

TEST 7: Risk Level Escalation
- Overheating + PRESSURING → "CRITICAL"
- Overheating + NEUTRAL → "ELEVATED"
- Overheating + SUPPORTING → "NORMAL"
- Accumulation + any → "NORMAL"

TEST 8: Full Integration (5 days of data for NVDA)
Simulate with persistence_tracker reused across days:
- Day1: sentiment=1.8, momentum=0.2, price_history=5 days ending with +1% return
  Expected: signal_state="WATCHING", regime="OVERHEATING_DIVERGENCE"
- Day2: sentiment=1.9, momentum=0.1, price_return=+0.3% (flat)
  Expected: signal_state="ACTIVE", risk_level="ELEVATED"
- Day3: sentiment=2.0, momentum=0.0, price_return=-0.8% (falling)
  Expected: signal_state="ACTIVE", risk_level="CRITICAL"
- Day4: sentiment=0.5, momentum=0.3, price_return=+0.5% (flat)
  Expected: signal_state="INACTIVE", regime="ALIGNED"
- Day5: sentiment=1.7, momentum=0.2, price_return=+0.1% (flat)
  Expected: signal_state="WATCHING" (streak restarted at 1)

TEST 9: JSON Output Format
- Verify all 8 fields present
- Verify no extra fields
- Verify JSON serializable using `import json; json.dumps(output)`

TEST 10: Edge Cases
- ndi exactly 1.5 → threshold met (>= includes equality)
- ndi exactly -1.5 → threshold met
- price_return exactly 0.005 → NEUTRAL (<= includes equality)
- Empty price_history → INSUFFICIENT_PRICE_HISTORY

Run all tests and print "ALL TESTS PASSED" if successful. If any test fails, print the failure clearly with expected vs actual.

Include a main block that runs all tests and handles persistence_state.json cleanup.
```

---

## Execution Order (Same)

| Prompt | Module | Depends On | Time Est. |
|--------|--------|------------|-----------|
| 1 | `layer4_measurement.py` | None | 10 min |
| 2 | `layer4_persistence.py` | None | 15 min |
| 3 | `layer4_classification.py` | None | 10 min |
| 4 | `layer4_orchestrator.py` | Prompts 1,2,3 | 15 min |
| 5 | `test_layer4.py` | Prompt 4 | 15 min |

**Total: ~65 minutes of OpenCode work**

---

## Expected Final File Structure

```
signaliq/
├── layer4/
│   ├── __init__.py
│   ├── layer4_measurement.py
│   ├── layer4_persistence.py
│   ├── layer4_classification.py
│   ├── layer4_orchestrator.py
│   ├── test_layer4.py
│   └── persistence_state.json (created at runtime)
```

---

## Success Criteria

After running Prompt 5, you should see:

```
ALL TESTS PASSED
```

If you see this, Layer 4 is ready.

---

## Known Limitations (Documented)

| Limitation | Impact | Fix Path |
|------------|--------|----------|
| No file locking on `persistence_state.json` | Concurrent runs could corrupt state | Post-MVP: add `fcntl` or SQLite |
| Price history assumes daily data | Won't work with intraday | Post-MVP: add date alignment |
| Thresholds (1.5, 0.005) frozen | May need asset-specific tuning | Post-MVP: make configurable per asset class |
| Inverted-U confidence unconventional | May confuse users | Document rationale prominently |

---

**SignalIQ** 🔹

*Five prompts. One hour. Enums everywhere. No ambiguity. Ready for OpenCode.*