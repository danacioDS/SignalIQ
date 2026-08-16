"""LLM Router for signal analysis - Supports Gemini, GLM, Groq and MOCK"""

import os
from typing import Optional
from dotenv import load_dotenv
import hashlib
from datetime import datetime

# Load .env only if not already loaded (not in test environment)
if os.environ.get('ENVIRONMENT') != 'test':
    load_dotenv()
# ============================================================
# CACHÉ DE LLM
# ============================================================
_llm_cache = {}
_LLM_CACHE_TTL = 600  # 10 minutos


class LLMRouter:
    """Intelligent router between multiple LLMs"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize clients based on configuration"""
        self.primary = os.getenv("PRIMARY_LLM", "groq")
        self.fallback = os.getenv("FALLBACK_LLM", "mock")
        self._clients = {}
        
        print(f"🔧 LLM Config: PRIMARY={self.primary}, FALLBACK={self.fallback}")
        
        if self.primary == "mock":
            print("🔄 MOCK mode activated")
            return
        
        # Initialize Gemini
        gemini_key = os.getenv("GEMINI_API_KEY")
        print(f"🔑 GEMINI_API_KEY: {'✓ Encontrada' if gemini_key else '✗ No encontrada'}")
        
        if gemini_key:  # Eliminada la condición 'tu_api_key'
            try:
                import google.generativeai as genai
                genai.configure(api_key=gemini_key)
                self._clients["gemini"] = genai
                print("✅ Gemini client initialized")
            except Exception as e:
                print(f"⚠️ Gemini init error: {e}")
        else:
            print("⚠️ GEMINI_API_KEY not found in environment")
        
        # Initialize GLM
        glm_key = os.getenv("GLM_API_KEY")
        if glm_key and "tu_api_key" not in glm_key:
            try:
                from zhipuai import ZhipuAI
                self._clients["glm"] = ZhipuAI(api_key=glm_key)
                print("✅ GLM client initialized")
            except Exception as e:
                print(f"⚠️ GLM init error: {e}")
        
        # Initialize Groq
        groq_key = os.getenv("GROQ_API_KEY")
        if groq_key and "tu_api_key" not in groq_key:
            try:
                from groq import Groq
                self._clients["groq"] = Groq(api_key=groq_key)
                print("✅ Groq client initialized")
            except Exception as e:
                print(f"⚠️ Groq init error: {e}")
    
    def analyze_signal(self, ticker: str, ndi: float, news_summary: str, context: Optional[str] = None) -> str:
        """Analyze a financial signal"""
        prompt = self._build_prompt(ticker, ndi, news_summary, context)
        
        if self.primary == "mock":
            return self._mock_response(ticker, ndi, news_summary)
        
        if self.primary in self._clients:
            try:
                result = self._call_llm(self.primary, prompt)
                if result and len(result.strip()) > 0:
                    return result
            except Exception as e:
                print(f"⚠️ {self.primary} failed: {e}")
        
        return self._fallback(prompt, ticker, ndi, news_summary)
    
    def _call_llm(self, provider: str, prompt: str) -> str:
        """Call specific LLM based on provider"""
        client = self._clients.get(provider)
        
        if provider == "gemini":
            # Probar con diferentes modelos de Gemini
            modelos = ['gemini-2.5-flash', 'gemini-1.5-flash', 'gemini-pro']
            for modelo in modelos:
                try:
                    model = client.GenerativeModel(modelo)
                    response = model.generate_content(prompt)
                    if response and response.text:
                        return response.text.strip()
                except Exception:
                    continue
            return ""
        
        elif provider == "glm":
            response = client.chat.completions.create(
                model="glm-4.7-flash",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=800
            )
            return response.choices[0].message.content.strip()
        
        elif provider == "groq":
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=800
            )
            return response.choices[0].message.content.strip()
        
        return ""
    
    def _fallback(self, prompt: str, ticker: str, ndi: float, news_summary: str) -> str:
        """Use configured fallback"""
        if self.fallback in self._clients:
            try:
                result = self._call_llm(self.fallback, prompt)
                if result and len(result.strip()) > 0:
                    return result
            except Exception as e:
                print(f"⚠️ Fallback {self.fallback} also failed: {e}")
        
        return self._mock_response(ticker, ndi, news_summary)
    
    def _build_prompt(self, ticker, ndi, news_summary, context):
        """Build prompt in English"""
        return f"""You are an expert financial analyst. Analyze this signal:

TICKER: {ticker}
NDI SCORE: {ndi} (0-1 scale, where >0.7 indicates strong signal)
NEWS: {news_summary}
CONTEXT: {context or 'No additional context'}

Generate an executive summary of 2-3 paragraphs including:
1. NDI interpretation
2. Market sentiment
3. Recommendation (BUY/SELL/HOLD)
4. Key risks

Format: Clear, professional English."""
    
    def _mock_response(self, ticker: str, ndi: float, news_summary: str) -> str:
        if ndi > 0.7:
            signal = "🔴 STRONG SIGNAL"
            recommendation = "CONSIDER SELL"
        elif ndi > 0.5:
            signal = "🟡 MODERATE SIGNAL"
            recommendation = "MONITOR"
        else:
            signal = "🟢 WEAK SIGNAL"
            recommendation = "HOLD"
        
        return f"""
╔══════════════════════════════════════════════════════════════╗
║                   SIGNALIQ FINANCIAL ANALYSIS                ║
║                         {ticker}                                  ║
╚══════════════════════════════════════════════════════════════╝

📊 **NDI Score:** {ndi} - {signal}

📈 **Interpretation:**
The Narrative Divergence Index indicates {
'high' if ndi > 0.7 else 'moderate' if ndi > 0.5 else 'low'
} divergence between price action and recent news.

📰 **News Context:**
{news_summary[:200]}...

💡 **Recommendation:** {recommendation}

⚠️ **Key Risks:**
• Market volatility
• Interest rate changes
• Competition in sector

---
📌 *Analysis generated by SignalIQ IA*
"""

# Global instance
llm_router = LLMRouter()


# ============================================================
# MARKET INTELLIGENCE ANALYSIS CON CACHÉ
# ============================================================
def analyze_market_intelligence(
    ticker: str,
    sentiment: float,
    momentum: float,
    ndi: float,
    regime: str,
    news: list
) -> dict:
    """Generate structured market intelligence using the existing LLM router."""

    cache_key = hashlib.md5(
        f"{ticker}_{ndi:.3f}_{sentiment:.3f}_{momentum:.3f}_{regime}_{len(news)}".encode()
    ).hexdigest()

    # Cache
    if cache_key in _llm_cache:
        data, timestamp = _llm_cache[cache_key]
        if (datetime.now() - timestamp).total_seconds() < _LLM_CACHE_TTL:
            print(f"🧠 LLM cache HIT: {ticker}")
            return data

    news_summary = (
        "\n".join([f"- {n[:150]}..." for n in news[:3]])
        if news
        else "- No recent news"
    )

    prompt = f"""Respond with exactly 5 concise lines for market intelligence.

Ticker: {ticker}
Sentiment: {sentiment:.3f}
Momentum: {momentum:.3f}
NDI: {ndi:.3f}
Regime: {regime}

Recent news:
{news_summary}

Use exactly this format:
Sentiment: <assessment>
Momentum: <assessment>
NDI/Regime: <assessment>
Market Interpretation: <assessment>
Risk/Outlook: <assessment>

Do not add numbering or extra lines.
"""

    result_text = ""

    # Use the existing router and its configured primary/fallback providers.
    try:
        print(f"🤖 Primary LLM: {llm_router.primary}")
        result_text = llm_router._call_llm(llm_router.primary, prompt) or ""
    except Exception as e:
        print(f"⚠️ Primary LLM failed: {e}")

    if not result_text:
        try:
            print(f"🔄 Fallback LLM: {llm_router.fallback}")
            result_text = llm_router._call_llm(llm_router.fallback, prompt) or ""
        except Exception as e:
            print(f"⚠️ Fallback LLM failed: {e}")

    # Deterministic fallback: API must still return valid intelligence
    if not result_text:
        sentiment_label = (
            "Positive" if sentiment > 0.05
            else "Negative" if sentiment < -0.05
            else "Neutral"
        )

        momentum_label = (
            "Strong" if momentum > 0.05
            else "Weak" if momentum < -0.05
            else "Stable"
        )

        result = {
            "sentiment": f"{sentiment_label} ({sentiment:.3f})",
            "momentum": f"{momentum_label} ({momentum:.3f})",
            "regime": f"{regime} (NDI: {ndi:.3f})",
            "interpretation": (
                f"{regime} market regime with "
                f"{sentiment_label.lower()} sentiment and "
                f"{momentum_label.lower()} momentum."
            ),
            "risk_outlook": (
                "Monitor divergence between sentiment, momentum "
                "and price action."
            )
        }

        _llm_cache[cache_key] = (result, datetime.now())
        return result

    # Convert the 5-line LLM response into the API's structured schema.
    lines = [
        line.strip()
        for line in result_text.strip().splitlines()
        if line.strip()
    ]

    result = {
        "sentiment": lines[0] if len(lines) > 0 else f"Sentiment: {sentiment:.3f}",
        "momentum": lines[1] if len(lines) > 1 else f"Momentum: {momentum:.3f}",
        "regime": lines[2] if len(lines) > 2 else f"NDI/Regime: {regime} ({ndi:.3f})",
        "interpretation": lines[3] if len(lines) > 3 else f"Market Interpretation: {regime} market",
        "risk_outlook": lines[4] if len(lines) > 4 else "Risk/Outlook: moderate risk"
    }

    _llm_cache[cache_key] = (result, datetime.now())

    return result
