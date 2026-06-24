#!/bin/bash
echo "🚀 SignalIQ Backend - Modo REAL"

# Matar procesos existentes
echo "🔄 Limpiando procesos antiguos..."
pkill -f "python.*app.main" || true
sleep 2

# Activar entorno virtual
source /home/daniel/repo_lab/SignalIQ/venv/bin/activate

# Cargar variables de entorno
set -a
source /home/daniel/repo_lab/SignalIQ/.env
set +a

# Forzar modo REAL
export USE_MOCK=false
export MOCK_MODE=false

# Mostrar configuración
echo "========================================="
echo "✅ Modo: REAL (conectado a DB)"
echo "✅ PRIMARY_LLM: $PRIMARY_LLM"
echo "✅ FALLBACK_LLM: $FALLBACK_LLM"
echo "✅ DATABASE: ${DATABASE_URL:0:30}..."
echo "✅ GROQ: ${GROQ_API_KEY:0:15}..."
echo "========================================="
echo ""

# Ir al backend y ejecutar
cd /home/daniel/repo_lab/SignalIQ/backend
python -m app.main
