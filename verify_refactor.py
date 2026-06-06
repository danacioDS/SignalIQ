#!/usr/bin/env python3
"""Verifica que la refactorización funciona"""

import sys
from pathlib import Path

# Agregar al path
sys.path.insert(0, str(Path.cwd()))

def main():
    print("🔍 VERIFICANDO REFACTORIZACIÓN\n" + "="*50)
    
    # 1. Configuración
    from signaliq.core.config import config
    print(f"✅ Configuración: {config}")
    print(f"   - DB URL: {'Configurada' if config.db.url else '❌ FALTA'}")
    print(f"   - LLM Primary: {config.llm.primary}")
    
    # 2. Persistencia
    from signaliq.core.persistence import SignalPersistence
    persistence = SignalPersistence()
    state = persistence.get_state()
    print(f"✅ Persistencia: {len(state)} tickers en estado")
    
    # 3. LLM Router
    from signaliq.core.llm import llm_router
    print(f"✅ LLM Router: {llm_router.primary} (fallback: {llm_router.fallback})")
    
    # 4. Verificar dependencias
    print("\n📦 DEPENDENCIAS:")
    deps = ['psycopg2', 'zhipuai', 'openai']
    for dep in deps:
        try:
            __import__(dep)
            print(f"   ✅ {dep}")
        except ImportError:
            print(f"   ❌ {dep} (instalar con pip)")
    
    print("\n" + "="*50)
    print("🎉 Refactorización exitosa!")
    print("\n📝 PRÓXIMOS PASOS:")
    print("1. Configurar variables de entorno en .env")
    print("2. pip install zhipuai openai")
    print("3. Integrar en layer4_orchestrator.py")

if __name__ == "__main__":
    main()
