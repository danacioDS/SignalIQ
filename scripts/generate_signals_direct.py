#!/usr/bin/env python3
"""Genera señales NDI directamente desde la base de datos usando datos reales."""

import os
import sys
import psycopg2
import psycopg2.extras
from datetime import datetime, timedelta
import numpy as np

DATABASE_URL = os.environ.get('RENDER_DATABASE_URL')
if not DATABASE_URL:
    print("ERROR: RENDER_DATABASE_URL no configurada")
    sys.exit(1)

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

print("🚀 GENERANDO SEÑALES CON DATOS REALES")
print("=" * 50)

# 1. Obtener tickers con datos reales
cur.execute("""
    SELECT DISTINCT ticker, COUNT(*) as count
    FROM prices 
    GROUP BY ticker 
    HAVING COUNT(*) > 30
    ORDER BY ticker
""")
tickers_data = cur.fetchall()
tickers = [t['ticker'] for t in tickers_data]
print(f"📊 {len(tickers)} tickers con datos suficientes: {', '.join(tickers)}")

# 2. Para cada ticker, calcular NDI
print("\n🧠 Calculando NDI para cada ticker...")
signals = []

for ticker in tickers:
    # Obtener precios históricos
    cur.execute("""
        SELECT price_date, close 
        FROM prices 
        WHERE ticker = %s 
        ORDER BY price_date ASC
    """, (ticker,))
    rows = cur.fetchall()
    
    if len(rows) < 30:
        print(f"  ⚠️ {ticker}: solo {len(rows)} precios (necesita 30)")
        continue
    
    prices = [float(r['close']) for r in rows]
    dates = [r['price_date'] for r in rows]
    
    # Calcular momentum (retorno de 5 días)
    if len(prices) >= 5:
        momentum = (prices[-1] - prices[-5]) / prices[-5] * 100
    else:
        momentum = 0
    
    # Calcular sentimiento (simulado con datos de precios)
    # En producción esto vendría de noticias
    if len(prices) >= 20:
        # Usar la variación de precios como proxy de sentimiento
        sentiment = (prices[-1] - prices[-20]) / prices[-20] * 10
        sentiment = max(-1, min(1, sentiment))  # Normalizar entre -1 y 1
    else:
        sentiment = 0
    
    # Calcular NDI
    ndi = sentiment - (momentum / 100)
    ndi = max(-2, min(2, ndi))  # Limitar entre -2 y 2
    
    # Determinar régimen
    if ndi > 0.7:
        regime = "Overheating"
        signal_state = "ACTIVE"
        confidence = 0.85
    elif ndi > 0.3:
        regime = "Watching"
        signal_state = "WATCHING"
        confidence = 0.70
    elif ndi < -0.5:
        regime = "Fear"
        signal_state = "ACTIVE"
        confidence = 0.75
    else:
        regime = "Aligned"
        signal_state = "INACTIVE"
        confidence = 0.50
    
    signals.append({
        'ticker': ticker,
        'ndi': round(ndi, 3),
        'regime': regime,
        'signal_state': signal_state,
        'confidence': round(confidence, 2),
        'sentiment': round(sentiment, 3),
        'momentum': round(momentum, 2),
        'price': prices[-1]
    })
    
    print(f"  ✅ {ticker}: NDI={ndi:.3f} | {regime} | {signal_state}")

# 3. Guardar señales en la base de datos
print("\n💾 Guardando señales en la base de datos...")
today = datetime.now().date()

# Limpiar señales del día
cur.execute("DELETE FROM layer4.signals WHERE signal_date = %s", (today,))

for s in signals:
    cur.execute("""
        INSERT INTO layer4.signals 
        (ticker, signal_date, ndi, regime, signal_state, confidence, risk_level, attention)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        s['ticker'],
        today,
        s['ndi'],
        s['regime'],
        s['signal_state'],
        s['confidence'],
        "NORMAL",
        f"NDI: {s['ndi']:.3f} - {s['regime']}"
    ))

conn.commit()
print(f"✅ {len(signals)} señales guardadas")

# 4. Mostrar resumen
print("\n📊 RESUMEN DE SEÑALES")
print("=" * 50)
for s in signals:
    print(f"  {s['ticker']}: NDI={s['ndi']:.3f} | {s['regime']} | {s['signal_state']} | ${s['price']:.2f}")

cur.close()
conn.close()
print("\n🎉 Señales generadas exitosamente")
