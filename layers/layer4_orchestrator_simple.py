import sys
import os
from typing import Dict, Any, Optional, List
from datetime import datetime

sys.path.insert(0, '/home/danacio/repo_lab/SignalIQ')
from signaliq.core.llm_simple import simple_llm

class Layer4Orchestrator:
    def __init__(self):
        self.analyses = []
        print("🚀 Orchestrator con SimpleLLM (Gemini directo)")
    
    def process_signal(self, ticker: str, ndi_score: float, 
                      news_summary: str, context: Optional[str] = None,
                      force_refresh: bool = False) -> Dict[str, Any]:
        
        print(f"🤖 Analizando {ticker} con Gemini REAL...")
        
        # Usar el LLM simple
        llm_analysis = simple_llm.analyze_signal(ticker, ndi_score, news_summary, context)
        
        # Extraer recomendación
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
            "confidence_score": 0.90 if ndi_score > 0.7 else 0.75,
            "timestamp": datetime.now().isoformat(),
            "from_cache": False
        }
        
        self.analyses.append(result)
        return result
    
    def batch_process(self, signals: List[Dict], show_progress: bool = True) -> List[Dict]:
        return [self.process_signal(s['ticker'], s['ndi'], s.get('news', '')) for s in signals]
    
    def get_summary(self, top_n: int = 5) -> str:
        return f"Total analyses: {len(self.analyses)}"
    
    def get_performance_stats(self) -> Dict:
        return {"total_processed": len(self.analyses), "llm_status": "ACTIVE (Gemini)"}

orchestrator = Layer4Orchestrator()
