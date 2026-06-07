"""LLM Provider - Simple version"""

import os
import google.generativeai as genai

class LLMProvider:
    def __init__(self):
        self.model = None
        api_key = os.environ.get('GEMINI_API_KEY')
        
        if not api_key:
            print("❌ GEMINI_API_KEY not found in environment")
            return
        
        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash')
            # Test connection
            self.model.generate_content("OK", generation_config={'max_output_tokens': 1})
            print("✅ Gemini API initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize Gemini: {e}")
            self.model = None
    
    def generate(self, prompt: str) -> str:
        if not self.model:
            return "MOCK: No API key configured"
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error: {str(e)}"

provider = LLMProvider()
