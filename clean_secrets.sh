#!/bin/bash
# Script para eliminar TODOS los secrets hardcodeados

echo "🔐 Limpiando secrets de SignalIQ..."

# 1. Limpiar backend/app/main.py
sed -i '/API_KEYS = \[/,/^\]/c\# API Keys now loaded from environment variables\nAPI_KEYS = []  # Will be populated from env' backend/app/main.py

# 2. Limpiar backend/app/llm_provider.py  
sed -i '/GEMINI_API_KEYS = \[/,/^\]/c\# API Keys now loaded from environment variables\nGEMINI_API_KEYS = []  # Will be populated from env' backend/app/llm_provider.py

# 3. Limpiar docker-compose.yml
sed -i '/GEMINI_API_KEY_[0-9]/d' docker-compose.yml

# 4. Limpiar layers/layer4_orchestrator.py
sed -i '/os.environ\["GEMINI_API_KEY"\] =/d' layers/layer4_orchestrator.py

# 5. Verificar que no quedan secrets
echo ""
echo "🔍 Verificando secrets remanentes..."
grep -r "AQ\.Ab8RN6" --include="*.py" --include="*.yml" --include="*.yaml" --include="*.env" . 2>/dev/null || echo "✅ No secrets found!"

echo ""
echo "📝 Recuerda:"
echo "1. Agregar nuevas API keys a .env"
echo "2. NO committear .env"
echo "3. Hacer git push --force after filter-repo"
