"""Sublayer 4A: Measurement — validity gate, NDI, and 5-day return."""

from config.thresholds import MIN_PRICE_HISTORY_DAYS

VALIDITY_STATE = ["VALID", "INVALID_INPUT", "INSUFFICIENT_PRICE_HISTORY"]


def validate_input(sentiment_zscore, momentum_zscore, price_history):
    """Check that all inputs are present and sufficient for measurement.

    Returns
    -------
    tuple[str, str | None]
        (state, reason) where state is one of VALIDITY_STATE and reason
        is a human-readable description when state is not VALID.
    """
    if sentiment_zscore is None:
        return ("INVALID_INPUT", "sentiment is None")
    if momentum_zscore is None:
        return ("INVALID_INPUT", "momentum is None")
    if price_history is None:
        return ("INVALID_INPUT", "price_history is None")
    if len(price_history) < MIN_PRICE_HISTORY_DAYS:
        return (
            "INSUFFICIENT_PRICE_HISTORY",
            f"need {MIN_PRICE_HISTORY_DAYS} prices, got {len(price_history)}",
        )
    return ("VALID", None)


def calculate_narrative_divergence_index(sentiment_zscore, momentum_zscore):
    """Net Divergence Index = sentiment_zscore - momentum_zscore.

    Returns None when either input is None.
    """
    if sentiment_zscore is None or momentum_zscore is None:
        return None
    return sentiment_zscore - momentum_zscore

# Backwards compatibility alias
calculate_ndi = calculate_narrative_divergence_index


def calculate_5d_return(price_history):
    """5-day trailing return from the closing-price list.

    ``price_history[-1]`` is today's close; ``price_history[-6]`` is the
    close from 5 trading days ago.  Returns None when fewer than 6 prices
    are available.
    """
    if len(price_history) < 6:
        return None
    return (price_history[-1] / price_history[-6]) - 1


def compute_measurements(sentiment_zscore, momentum_zscore, price_history):
    """Run the full Sublayer 4A measurement pipeline.

    Parameters
    ----------
    sentiment_zscore : float or None
    momentum_zscore : float or None
    price_history : list[float]
        Closing prices with today as the last element.

    Returns
    -------
    dict
        Keys: validity_state, validity_reason, ndi, return_5d.
    """
    state, reason = validate_input(sentiment_zscore, momentum_zscore, price_history)

    if state != "VALID":
        return {
            "validity_state": state,
            "validity_reason": reason,
            "ndi": None,
            "return_5d": None,
        }

    return {
        "validity_state": "VALID",
        "validity_reason": None,
        "ndi": calculate_ndi(sentiment_zscore, momentum_zscore),
        "return_5d": calculate_5d_return(price_history),
    }

