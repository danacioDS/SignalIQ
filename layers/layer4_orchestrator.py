"""Layer 4: Orchestrator - FORZADO A GEMINI REAL"""

import os
import sys
from typing import Dict, Any, Optional, List
from datetime import datetime

# FORZAR Gemini ANTES de cualquier import
os.environ['PRIMARY_LLM'] = 'gemini'
os.environ['FALLBACK_LLM'] = 'mock'
os.environ['GEMINI_API_KEY'] = 'GEMINI_API_KEY_REDACTED'

from signaliq.core.llm import llm_router

class Layer4Orchestrator:
    def __init__(self):
        self.analyses: List[Dict[str, Any]] = []
        self.total_processed = 0
        self.cache_enabled = True
        self._cache: Dict[str, Dict[str, Any]] = {}
        print("🚀 SignalIQ Layer4 Orchestrator initialized (FORZADO GEMINI)")
    
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
