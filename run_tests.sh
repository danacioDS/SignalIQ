#!/bin/bash
# Script para ejecutar todos los tests automáticamente

echo "🚀 Iniciando API para tests..."
cd backend
python -m app.main &
API_PID=$!

echo "⏳ Esperando a que la API arranque..."
sleep 5

echo "🧪 Ejecutando tests..."
cd ..
pytest tests/ -v --tb=short --cov=backend/app --cov-report=term

echo "🧹 Deteniendo API..."
kill $API_PID

echo "✅ Tests completados!"
