"""Sublayer 4B: Classification — confidence, price pressure, risk, and attention."""

CONFIDENCE_LEVEL = ["LOW", "MEDIUM", "HIGH", "INSUFFICIENT_DATA"]
PRICE_PRESSURE = ["SUPPORTING", "NEUTRAL", "PRESSURING"]
RISK_LEVEL = ["NORMAL", "ELEVATED", "CRITICAL"]
PRICE_MODIFIER = ["trend_supporting", "trend_stalling", "trend_collapsing"]
NDI_TREND = ["ACCELERATING", "DECELERATING", "STABLE", "INSUFFICIENT_DATA"]


def calculate_confidence(ndi: float | None) -> str:
    """Inverted U-shape confidence.

    Rationale
    ---------
    Extreme NDI values (|NDI| > 2.2) are often noise bursts or sentiment
    outliers.  Mid-range NDI (0.8–2.2) represents stable, persistent
    divergence and is **more** reliable.  This is intentional and
    empirically grounded in behavioural finance literature.
    """
    if ndi is None:
        return "INSUFFICIENT_DATA"
    if abs(ndi) > 2.2:
        return "MEDIUM"
    if abs(ndi) >= 0.8:
        return "HIGH"
    return "LOW"


def boost_confidence_by_streak(confidence: str, streak: int) -> str:
    """Boost confidence by one level when streak >= 3 days.

    Mapping
    -------
    * ``LOW`` → ``MEDIUM``
    * ``MEDIUM`` → ``HIGH``
    * ``HIGH`` → ``HIGH`` (ceiling)
    * ``INSUFFICIENT_DATA`` → ``INSUFFICIENT_DATA``
    """
    if streak < 3 or confidence == "HIGH" or confidence == "INSUFFICIENT_DATA":
        return confidence
    if confidence == "LOW":
        return "MEDIUM"
    if confidence == "MEDIUM":
        return "HIGH"
    return confidence


def calculate_price_pressure(return_5d: float | None, flat_threshold: float = 0.005) -> str:
    """Classify 5-day return into a pressure score."""
    if return_5d is None:
        return "NEUTRAL"
    if return_5d > flat_threshold:
        return "SUPPORTING"
    if return_5d < -flat_threshold:
        return "PRESSURING"
    return "NEUTRAL"


def get_price_modifier(price_pressure: str) -> str:
    """Map internal price-pressure labels to user-facing modifier strings."""
    mapping = {
        "SUPPORTING": "trend_supporting",
        "NEUTRAL": "trend_stalling",
        "PRESSURING": "trend_collapsing",
    }
    return mapping.get(price_pressure, "trend_stalling")


def get_ndi_trend(ndi_delta: float | None, threshold: float = 0.3) -> str:
    """Classify NDI velocity into a trend direction.

    Parameters
    ----------
    ndi_delta
        Today's NDI minus yesterday's NDI.
    threshold
        Minimum absolute delta to be considered meaningful (default 0.3).
    """
    if ndi_delta is None:
        return "INSUFFICIENT_DATA"
    if ndi_delta > threshold:
        return "ACCELERATING"
    if ndi_delta < -threshold:
        return "DECELERATING"
    return "STABLE"


def get_risk_level(regime: str, price_pressure: str) -> str:
    """Escalation rule — risk is a function of regime *modulated by* price.

    Only ``OVERHEATING_DIVERGENCE`` can produce non-NORMAL risk.
    """
    if regime != "OVERHEATING_DIVERGENCE":
        return "NORMAL"
    if price_pressure == "NEUTRAL":
        return "ELEVATED"
    if price_pressure == "PRESSURING":
        return "CRITICAL"
    return "NORMAL"


def get_attention_text(risk_level: str, signal_state: str, regime: str) -> str:
    """Map risk-level / signal-state / regime to a one-line attention text."""
    if signal_state == "INACTIVE" and regime == "INSUFFICIENT_DATA":
        return "Insufficient data for reliable signal."
    if signal_state == "INACTIVE":
        return "No divergence signal detected."
    if signal_state == "WATCHING":
        return "Watching for persistence (needs 2nd consecutive day)."
    if risk_level == "NORMAL":
        return "No action required."
    if risk_level == "ELEVATED":
        return "Narrative optimism with stalling price. Review position."
    if risk_level == "CRITICAL":
        return "Narrative optimism despite falling prices. Elevated caution warranted."
    return "Signal detected. Monitor closely."
