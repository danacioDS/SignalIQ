import os
import requests
from groq import Groq

class LLMService:
    def __init__(self):
        self.groq_api_key = os.environ.get('GROQ_API_KEY')
        self.groq_client = Groq(api_key=self.groq_api_key) if self.groq_api_key else None
        
    def analyze_ticker(self, ticker: str, ndi: float, sentiment: float = None, momentum: float = None):
        """Genera análisis financiero para un ticker usando Groq"""
        
        # Determinar régimen basado en NDI
        if ndi > 0.7:
            regime = "Overheating Divergence"
            regime_desc = "bearish signal, narrative running ahead of price"
        elif ndi > 0.3:
            regime = "Accumulation Divergence"
            regime_desc = "watching signal, mild divergence"
        else:
            regime = "Aligned"
            regime_desc = "neutral, narrative and price in sync"
        
        prompt = f"""
You are a professional financial analyst. Analyze this signal:

Ticker: {ticker}
NDI (Narrative Divergence Index): {ndi:.3f}
Regime: {regime} - {regime_desc}
Sentiment Z-Score: {sentiment:.2f if sentiment else 'N/A'}
Momentum Z-Score: {momentum:.2f if momentum else 'N/A'}

Write a concise 2-3 sentence analysis in English that:
1. Explains what this NDI means for {ticker}
2. Gives a clear recommendation (BUY/HOLD/REDUCE)
3. Mentions risk level

Keep it professional and actionable. Maximum 100 words.
"""
        
        try:
            if self.groq_client:
                response = self.groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.5,
                    max_tokens=200
                )
                return response.choices[0].message.content
            else:
                return self._mock_analysis(ticker, ndi, regime)
        except Exception as e:
            print(f"Error calling Groq: {e}")
            return self._mock_analysis(ticker, ndi, regime)
    
    def _mock_analysis(self, ticker: str, ndi: float, regime: str):
        """Fallback analysis when LLM is unavailable"""
        if ndi > 0.7:
            return f"{ticker} shows strong overheating divergence. Narrative has significantly outpaced price action. Consider reducing exposure and monitoring sentiment closely."
        elif ndi > 0.3:
            return f"{ticker} exhibits accumulation divergence. Mild disconnect between sentiment and price. Maintain position with caution."
        else:
            return f"{ticker} is in aligned regime. Narrative and price action are synchronized. No immediate action required."

# Instancia global
llm_service = LLMService()
