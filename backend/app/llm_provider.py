"""Proveedor unificado de LLM con fallback automático"""

import os
from groq import Groq
import google.generativeai as genai

class LLMProvider:
    """Proveedor con Groq principal y Gemini fallback"""
    
    def __init__(self):
        # Configurar Groq
        self.groq_client = Groq(api_key=os.environ.get('GROQ_API_KEY', ''))
        
        # Configurar Gemini (fallback)
        self.gemini_keys = [
            'GEMINI_API_KEY_REDACTED',
            'GEMINI_API_KEY_REDACTED',
            'GEMINI_API_KEY_REDACTED',
        ]
        self.gemini_index = 0
        
    def _call_groq(self, prompt):
        """Llama a Groq (principal)"""
        response = self.groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.7,
            max_tokens=800,
        )
        return response.choices[0].message.content
    
    def _call_gemini(self, prompt):
        """Llama a Gemini (fallback)"""
        genai.configure(api_key=self.gemini_keys[self.gemini_index])
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(prompt)
        return response.text
    
    def analyze(self, prompt):
        """Intenta Groq, si falla usa Gemini"""
        try:
            return self._call_groq(prompt)
        except Exception as e:
            print(f"⚠️ Groq falló: {e}, usando Gemini...")
            return self._call_gemini(prompt)

provider = LLMProvider()
