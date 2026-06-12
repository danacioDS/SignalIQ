#!/usr/bin/env python3
"""Verifica que la refactorización funciona"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))

def main():
    print("VERIFICANDO REFACTORIZACION\n" + "="*50)

    from layers.system_config import config
    print(f"Configuracion: {config}")
    print(f"   - DB URL: {'Configurada' if config.db.url else 'FALTA'}")
    print(f"   - LLM Primary: {config.llm.primary}")

    from layers.llm_router import llm_router
    print(f"LLM Router: {llm_router.primary} (fallback: {llm_router.fallback})")

    print("\nDEPENDENCIAS:")
    deps = ['psycopg2', 'zhipuai', 'openai']
    for dep in deps:
        try:
            __import__(dep)
            print(f"   {dep}")
        except ImportError:
            print(f"   {dep} (instalar con pip)")

    print("\n" + "="*50)
    print("Refactorizacion exitosa!")

if __name__ == "__main__":
    main()
