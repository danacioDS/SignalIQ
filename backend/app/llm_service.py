import os
from groq import Groq

class LLMService:
    def __init__(self):
        self.api_key = os.environ.get('GROQ_API_KEY')
        if not self.api_key:
            print("⚠️ GROQ_API_KEY no configurada. Usando modo mock.")
            self.client = None
        else:
            self.client = Groq(api_key=self.api_key)
        
        self.primary_model = "qwen/qwen3-32b"
        self.fallback_model = "llama-3.3-70b-versatile"
    
    def analyze_ticker(self, ticker: str, ndi: float, sentiment: float = None, momentum: float = None) -> str:
        # Determinar régimen
        if ndi > 0.7:
            regime = "Overheating Divergence"
            regime_desc = "bearish - narrative ahead of price"
        elif ndi > 0.3:
            regime = "Accumulation Divergence"
            regime_desc = "watching - mild divergence"
        else:
            regime = "Aligned"
            regime_desc = "neutral - narrative and price in sync"
        
        # Construir prompt (evitando errores de formato)
        sentiment_str = f"{sentiment:.2f}" if sentiment is not None else "N/A"
        momentum_str = f"{momentum:.2f}" if momentum is not None else "N/A"
        
        prompt = f"""You are a professional financial analyst. Analyze this signal:

Ticker: {ticker}
NDI: {ndi:.3f}
Regime: {regime} - {regime_desc}
Sentiment Z-Score: {sentiment_str}
Momentum Z-Score: {momentum_str}

Write a concise 2-3 sentence analysis in English that:
1. Explains what this NDI means for {ticker}
2. Gives a clear recommendation (BUY/HOLD/REDUCE)
3. Mentions risk level

Keep it professional and actionable."""
        
        # Si no hay API key, usar mock
        if not self.client:
            return self._mock_analysis(ticker, ndi)
        
        # Intento 1: Qwen3-32B
        try:
            response = self.client.chat.completions.create(
                model=self.primary_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
                max_tokens=200
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"⚠️ Error con Qwen: {e}")
            
            # Intento 2: Llama 3.3 70B
            try:
                response = self.client.chat.completions.create(
                    model=self.fallback_model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.5,
                    max_tokens=200
                )
                return response.choices[0].message.content
            except Exception as e:
                print(f"⚠️ Error con Llama: {e}")
                return self._mock_analysis(ticker, ndi)
    
    def _mock_analysis(self, ticker: str, ndi: float) -> str:
        if ndi > 0.7:
            return f"{ticker} shows strong overheating divergence (NDI: +{ndi:.3f}). Market narrative has outpaced price action. Recommendation: Reduce exposure. Risk: High."
        elif ndi > 0.3:
            return f"{ticker} exhibits accumulation divergence (NDI: +{ndi:.3f}). Mild disconnect between sentiment and price. Recommendation: Hold with caution. Risk: Moderate."
        else:
            return f"{ticker} is in aligned regime (NDI: +{ndi:.3f}). Narrative and price action synchronized. Recommendation: Hold. Risk: Low."

# Instancia global
llm_service = LLMService()
