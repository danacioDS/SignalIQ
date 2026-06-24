#!/bin/bash
echo "🚀 Iniciando SignalIQ Backend..."

# Activar entorno virtual
source /home/daniel/repo_lab/SignalIQ/venv/bin/activate

# Cargar variables de entorno (solo líneas sin comentarios y con valor)
export $(grep -v '^#' .env | grep -v '^$' | xargs)

# Crear directorio de logs
mkdir -p logs

# Ir al directorio backend y ejecutar
cd /home/daniel/repo_lab/SignalIQ/backend
python app/main.py &

echo "✅ Backend iniciado en http://localhost:10000"
echo "📊 Logs: tail -f ../logs/app.log"
