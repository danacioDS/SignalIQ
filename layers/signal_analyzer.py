"""Integración del LLM Router con layer4"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from signaliq.core.llm import llm_router

def analyze_signal_with_llm(ticker: str, ndi: float, news_summary: str = None):
    """Función para usar en layer4_orchestrator"""
    
    if not news_summary:
        news_summary = f"Noticias recientes para {ticker}"
    
    analysis = llm_router.analyze_signal(
        ticker=ticker,
        ndi=ndi,
        news_summary=news_summary
    )
    
    return {
        "ticker": ticker,
        "ndi": ndi,
        "llm_analysis": analysis,
        "recommendation": extract_recommendation(analysis)
    }

def extract_recommendation(analysis: str) -> str:
    """Extrae recomendación del análisis"""
    if "CONSIDERAR VENTA" in analysis:
        return "SELL"
    elif "MONITOREAR" in analysis:
        return "WATCH"
    else:
        return "HOLD"

# Ejemplo de uso
if __name__ == "__main__":
    result = analyze_signal_with_llm("AAPL", 0.82)
    print(result["llm_analysis"])
