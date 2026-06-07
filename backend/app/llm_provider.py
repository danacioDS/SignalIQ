"""LLM Provider - Gestión de proveedores de IA"""

import os
import sys
import google.generativeai as genai

class LLMProvider:
    """Proveedor de LLM con múltiples backends"""
    
    def __init__(self):
        print("🔧 Inicializando LLMProvider...")
        print(f"📋 Variables de entorno encontradas:")
        for key in os.environ.keys():
            if 'GEMINI' in key or 'LLM' in key:
                print(f"   - {key}=[{'*' * min(len(os.environ.get(key, '')), 10)}]")
        
        self.api_keys = self._load_api_keys()
        print(f"🔑 Keys cargadas: {len(self.api_keys)}")
        
        self.current_key_index = 0
        self.model = None
        self._init_model()
    
    def _load_api_keys(self) -> list:
        """Cargar API keys desde variables de entorno"""
        keys = []
        
        # Buscar GEMINI_API_KEY_1, _2, _3
        for i in range(1, 4):
            key = os.environ.get(f'GEMINI_API_KEY_{i}')
            if key:
                keys.append(key)
                print(f"✅ Cargada GEMINI_API_KEY_{i}: {key[:15]}...")
            else:
                print(f"❌ No encontrada GEMINI_API_KEY_{i}")
        
        # Fallback a GEMINI_API_KEY única
        if not keys and os.environ.get('GEMINI_API_KEY'):
            keys = [os.environ.get('GEMINI_API_KEY')]
            print(f"✅ Fallback a GEMINI_API_KEY")
        
        if not keys:
            print("⚠️ No se encontraron API keys!")
        
        return keys
    
    def _init_model(self):
        """Inicializar modelo Gemini con la primera key disponible"""
        for i, key in enumerate(self.api_keys):
            try:
                print(f"🔄 Intentando inicializar con key {i+1}...")
                genai.configure(api_key=key)
                test_model = genai.GenerativeModel('gemini-2.0-flash')
                # Test rápido
                response = test_model.generate_content("OK", generation_config={'max_output_tokens': 1})
                self.model = test_model
                self.current_key_index = i
                print(f"✅ LLM inicializado correctamente con key {i+1}")
                return True
            except Exception as e:
                print(f"❌ Error con key {i+1}: {str(e)[:100]}")
                continue
        
        print("⚠️ No hay API keys válidas, usando modo MOCK")
        self.model = None
        return False
    
    def generate(self, prompt: str) -> str:
        """Generar respuesta usando el LLM"""
        if not self.model:
            return self._mock_response(prompt)
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"❌ Error en generate: {str(e)[:100]}")
            return self._mock_response(prompt)
    
    def _mock_response(self, prompt: str) -> str:
        """Respuesta mock cuando no hay LLM disponible"""
        return """
ANALYSIS SUMMARY:
- Market sentiment: NEUTRAL
- Technical indicators: MIXED
- Recommendation: HOLD

Note: This is a mock response. Configure GEMINI_API_KEY_1, _2, _3 in environment variables.
"""

# Instancia global
print("🚀 Creando instancia global de LLMProvider...")
provider = LLMProvider()
print(f"📊 Estado final: {'REAL' if provider.model else 'MOCK'}")
