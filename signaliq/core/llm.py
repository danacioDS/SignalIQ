"""LLM Router for signal analysis - Supports Gemini, GLM, Groq and MOCK"""

import os
from typing import Optional
from dotenv import load_dotenv

# Cargar .env al inicio
load_dotenv()

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
        self.primary = os.getenv("PRIMARY_LLM", "mock")
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
                except:
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
