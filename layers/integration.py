"""SignalIQ Pipeline Integration — connects Layer 1→2→3→4.

Provides a single entry point that wires together:
  - FundamentalEngine (Layer 3)
  - Layer4Orchestrator (Layer 4 – NDI, Bubble Risk)
  - PersistenceTracker (Layer 4 – state management)
"""

from typing import Any, Optional

from layers.fundamental.fundamental_engine import FundamentalEngine
from layers.layer4_orchestrator import Layer4Orchestrator
from layers.layer4_persistence import PersistenceTracker


def run_pipeline(
    ticker: str,
    narrative_score: float,
    technical_score: float,
    article_count: int,
    fundamental_data: Optional[dict] = None,
    config: Optional[dict] = None,
    orchestrator: Optional[Layer4Orchestrator] = None,
) -> dict:
    """Run the full Layer 3→4 pipeline for a single asset.

    Parameters
    ----------
    ticker:
        Asset symbol (e.g. ``NVDA``).
    narrative_score:
        Narrative / sentiment score from Layer 3 (0–100).
    technical_score:
        Momentum / technical score from Layer 3 (0–100).
    article_count:
        Number of articles processed for the period.
    fundamental_data:
        Raw fundamental metrics dict (see ``FundamentalEngine``).
        If ``None``, the pipeline still runs but without fundamental adjustment.
    config:
        Optional config dict forwarded to ``Layer4Orchestrator``.
    orchestrator:
        Reusable orchestrator instance. If ``None``, a fresh one is created.

    Returns
    -------
    dict
        Full Layer 4 output with NDI, bubble risk, confidence, regime, etc.
    """
    l4 = orchestrator or Layer4Orchestrator(config or {})

    signal = l4.process_signal(
        ticker=ticker,
        narrative_score=narrative_score,
        technical_score=technical_score,
        article_count=article_count,
        fundamental_data=fundamental_data,
    )

    return signal


def run_batch_pipeline(
    assets: list[dict],
    config: Optional[dict] = None,
) -> list[dict]:
    """Run the Layer 3→4 pipeline for multiple assets.

    Parameters
    ----------
    assets:
        List of dicts, each with keys:
        ``ticker``, ``narrative_score``, ``technical_score``,
        ``article_count``, and optionally ``fundamental_data``.
    config:
        Optional config dict.

    Returns
    -------
    list[dict]
        One output dict per asset.
    """
    l4 = Layer4Orchestrator(config or {})
    results = []
    for asset in assets:
        result = run_pipeline(
            ticker=asset["ticker"],
            narrative_score=asset["narrative_score"],
            technical_score=asset["technical_score"],
            article_count=asset["article_count"],
            fundamental_data=asset.get("fundamental_data"),
            orchestrator=l4,
        )
        results.append(result)
    return results
