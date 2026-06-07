import os
import sys

# Agregar el directorio actual al path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Ahora importar módulos locales
from asset_classifier import classifier
from llm_provider import provider

# Resto del código...
