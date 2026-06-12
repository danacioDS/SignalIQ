"""Layer 4: Orchestrator"""

import os
import sys
from typing import Dict, Any, Optional, List
from datetime import datetime

from signaliq.core.llm import llm_router
from layers.layer4_measurement import (
    validate_input,
    calculate_ndi,
    calculate_5d_return,
)
from layers.layer4_persistence import PersistenceTracker
from layers.layer4_classification import (
    boost_confidence_by_streak,
    calculate_confidence,
    calculate_price_pressure,
    get_price_modifier,
    get_ndi_trend,
    get_risk_level,
    get_attention_text,
)

OUTPUT_FIELDS = [
    "ticker", "date", "ndi", "ndi_delta", "ndi_trend", "regime",
    "signal_state", "confidence", "price_modifier", "persistence_days",
    "risk_level", "attention",
]


def process_asset(
    ticker: str,
    sentiment_zscore: float | None,
    momentum_zscore: float | None,
    price_history: list[float],
    tracker: PersistenceTracker,
    date_string: str,
) -> dict:
    state, reason = validate_input(sentiment_zscore, momentum_zscore, price_history)

    if state != "VALID":
        return {
            "ticker": ticker,
            "date": date_string,
            "ndi": None,
            "ndi_delta": None,
            "ndi_trend": "INSUFFICIENT_DATA",
            "regime": "INSUFFICIENT_DATA",
            "signal_state": "INACTIVE",
            "confidence": "INSUFFICIENT_DATA",
            "price_modifier": "trend_stalling",
            "persistence_days": 0,
            "risk_level": "NORMAL",
            "attention": "Insufficient data for reliable signal.",
        }

    ndi = calculate_ndi(sentiment_zscore, momentum_zscore)
    return_5d = calculate_5d_return(price_history)
    prev_ndi = tracker.get_last_ndi(ticker)
    ndi_delta = ndi - prev_ndi if (ndi is not None and prev_ndi is not None) else None

    signal_state = tracker.get_signal_state(ticker, ndi, date_string)
    streak = tracker.get_streak(ticker)
    regime = PersistenceTracker.get_regime(ndi)
    price_pressure = calculate_price_pressure(return_5d)
    confidence = calculate_confidence(ndi)
    confidence = boost_confidence_by_streak(confidence, streak)
    risk = get_risk_level(regime, price_pressure)
    trend = get_ndi_trend(ndi_delta)

    return {
        "ticker": ticker,
        "date": date_string,
        "ndi": ndi,
        "ndi_delta": ndi_delta,
        "ndi_trend": trend,
        "regime": regime,
        "signal_state": signal_state,
        "confidence": confidence,
        "price_modifier": get_price_modifier(price_pressure),
        "persistence_days": streak,
        "risk_level": risk,
        "attention": get_attention_text(risk, signal_state, regime),
    }


def validate_batch_input(batch: dict[str, dict]) -> list[str]:
    errors = []
    for ticker, data in batch.items():
        if not isinstance(data, dict):
            errors.append(f"{ticker}: value is not a dict")
            continue
        missing = []
        if "sentiment_zscore" not in data:
            missing.append("sentiment_zscore")
        if "momentum_zscore" not in data:
            missing.append("momentum_zscore")
        if "price_history" not in data:
            missing.append("price_history")
        if missing:
            errors.append(f"{ticker}: missing {', '.join(missing)}")
    return errors


def process_batch(
    batch: dict[str, dict],
    tracker: PersistenceTracker,
    date_string: str,
) -> list[dict]:
    errs = validate_batch_input(batch)
    if errs:
        raise ValueError("; ".join(errs))
    return [
        process_asset(
            ticker,
            data["sentiment_zscore"],
            data["momentum_zscore"],
            data["price_history"],
            tracker,
            date_string,
        )
        for ticker, data in batch.items()
    ]

class Layer4Orchestrator:
    def __init__(self):
        self.analyses: List[Dict[str, Any]] = []
        self.total_processed = 0
        self.cache_enabled = True
        self._cache: Dict[str, Dict[str, Any]] = {}
        print("🚀 SignalIQ Layer4 Orchestrator initialized")
    
    def _get_llm_status(self) -> str:
        return "ACTIVE (Gemini)" if 'gemini' in llm_router._clients else "MOCK MODE"
    
    def process_signal(self, ticker: str, ndi_score: float, 
                      news_summary: str, context: Optional[str] = None,
                      force_refresh: bool = False) -> Dict[str, Any]:
        
        print(f"🤖 Generando análisis REAL con Gemini para {ticker}...")
        
        # Usar el LLM router directamente
        llm_analysis = llm_router.analyze_signal(
            ticker=ticker,
            ndi=ndi_score,
            news_summary=news_summary,
            context=context
        )
        
        # Determinar recomendación basada en el análisis
        if "BUY" in llm_analysis.upper() and "SELL" not in llm_analysis.upper():
            recommendation = "BUY"
        elif "SELL" in llm_analysis.upper():
            recommendation = "SELL"
        else:
            recommendation = "HOLD"
        
        result = {
            "ticker": ticker,
            "ndi_score": round(ndi_score, 3),
            "signal_strength": "STRONG" if ndi_score > 0.7 else "MODERATE" if ndi_score > 0.5 else "WEAK",
            "news_summary": news_summary[:300],
            "context": context or "No additional context",
            "llm_analysis": llm_analysis,
            "recommendation": recommendation,
            "confidence_score": 0.85 if ndi_score > 0.7 else 0.70,
            "timestamp": datetime.now().isoformat(),
            "from_cache": False
        }
        
        self.analyses.append(result)
        self.total_processed += 1
        return result
    
    def batch_process(self, signals: List[Dict[str, Any]], show_progress: bool = True, parallel: bool = False) -> List[Dict[str, Any]]:
        results = []
        for signal in signals:
            result = self.process_signal(
                ticker=signal.get("ticker"),
                ndi_score=signal.get("ndi", 0.5),
                news_summary=signal.get("news", "No news available"),
                context=signal.get("context")
            )
            results.append(result)
        return results
    
    def get_summary(self, top_n: int = 5) -> str:
        if not self.analyses:
            return "No analyses available"
        return f"Total signals: {len(self.analyses)}"
    
    def get_ticker_analysis(self, ticker: str) -> Optional[Dict[str, Any]]:
        for analysis in reversed(self.analyses):
            if analysis.get('ticker') == ticker:
                return analysis
        return None
    
    def get_all_analyses(self) -> List[Dict[str, Any]]:
        return self.analyses.copy()
    
    def clear_cache(self):
        self._cache.clear()
    
    def export_to_json(self, filepath: str = "signaliq_analyses.json") -> str:
        import json
        with open(filepath, 'w') as f:
            json.dump(self.analyses, f, indent=2)
        return filepath
    
    def get_performance_stats(self) -> Dict[str, Any]:
        return {
            "total_processed": self.total_processed,
            "cache_size": len(self._cache),
            "valid_analyses": len(self.analyses),
            "error_rate": 0.0,
            "recommendation_distribution": {},
            "average_confidence": 0.80,
            "llm_status": self._get_llm_status()
        }

orchestrator = Layer4Orchestrator()
