#!/usr/bin/env python3
"""
Métricas de rendimiento para el NDI.
"""
import json
import numpy as np
from datetime import datetime

# Cargar resultados
with open('backtest_results.json', 'r') as f:
    data = json.load(f)

results = data.get('results', [])
if not results:
    print("No hay resultados para analizar")
    exit()

# Extraer valores
ndi_values = [r['ndi'] for r in results]
sentiment_values = [r['sentiment'] for r in results]
momentum_values = [r['momentum'] for r in results]
prices = [r['price'] for r in results]

# Calcular métricas
print("=== MÉTRICAS DEL NDI ===\n")

print(f"Fecha: {data.get('timestamp', 'N/A')}")
print(f"Tickers analizados: {len(results)}")
print()

# Distribución
print("📊 Distribución:")
print(f"  NDI medio: {np.mean(ndi_values):.4f}")
print(f"  NDI desvío: {np.std(ndi_values):.4f}")
print(f"  NDI mínimo: {np.min(ndi_values):.4f}")
print(f"  NDI máximo: {np.max(ndi_values):.4f}")
print(f"  Rango NDI: {np.max(ndi_values) - np.min(ndi_values):.4f}")
print()

# Correlaciones
print("📈 Correlaciones:")
print(f"  Sentiment-NDI: {np.corrcoef(sentiment_values, ndi_values)[0,1]:.4f}")
print(f"  Momentum-NDI: {np.corrcoef(momentum_values, ndi_values)[0,1]:.4f}")
print(f"  Price-NDI: {np.corrcoef(prices, ndi_values)[0,1]:.4f}")
print()

# Regímenes
regime_counts = {}
for r in results:
    regime = r.get('regime', 'UNKNOWN')
    regime_counts[regime] = regime_counts.get(regime, 0) + 1

print("🏷️ Regímenes:")
for regime, count in regime_counts.items():
    pct = (count / len(results)) * 100
    print(f"  {regime}: {count} ({pct:.1f}%)")
print()

# Métricas de señal
print("🎯 Métricas de señal:")
print(f"  Señales totales: {len(results)}")
print(f"  Señales WATCHING: {regime_counts.get('WATCHING', 0)}")
print(f"  Señales NEUTRAL: {regime_counts.get('NEUTRAL', 0)}")
print(f"  Señales ALIGNED: {regime_counts.get('ALIGNED', 0)}")
print(f"  Señales OVERHEATING: {regime_counts.get('OVERHEATING', 0)}")
print(f"  Señales CAPITULATION: {regime_counts.get('CAPITULATION', 0)}")

# Métricas de calidad
print("\n📋 Métricas de calidad:")
print(f"  Confianza media: {np.mean([r.get('confidence', 0) for r in results]):.1f}")
print(f"  Confianza mínima: {np.min([r.get('confidence', 0) for r in results]):.1f}")
print(f"  Confianza máxima: {np.max([r.get('confidence', 0) for r in results]):.1f}")
print(f"  Precio medio: ${np.mean(prices):.2f}")

print("\n✅ Análisis completado")
