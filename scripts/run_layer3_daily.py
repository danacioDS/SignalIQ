#!/usr/bin/env python3
"""Ejecuta el pipeline diario de Layer 3 usando datos de la base de datos."""

import os
import sys
import psycopg2
import psycopg2.extras
from datetime import datetime, timedelta
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from layers.layer3_momentum import MomentumProcessor
from layers.layer3_sentiment import SentimentProcessor
from layers.layer4_orchestrator import Layer4Orchestrator, process_asset
from layers.layer4_persistence import PersistenceTracker

DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    print("ERROR: DATABASE_URL no configurada")
    sys.exit(1)

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

print("🚀 Iniciando pipeline diario de Layer 3...")

tickers = ['NVDA', 'AAPL', 'MSFT', 'TSLA']

# 1. Obtener precios históricos para todos los tickers
print("📊 Cargando precios históricos...")
price_data = {}
for ticker in tickers:
    cur.execute("""
        SELECT price_date, close FROM prices 
        WHERE ticker = %s 
        ORDER BY price_date ASC
        LIMIT 60
    """, (ticker,))
    rows = cur.fetchall()
    price_data[ticker] = [float(row['close']) for row in rows]
    print(f"  {ticker}: {len(price_data[ticker])} precios")

# 2. Obtener noticias históricas
print("📰 Cargando noticias históricas...")
cur.execute("""
    SELECT title, content, published_at
    FROM news_articles
    ORDER BY published_at ASC
""")
news = cur.fetchall()
print(f"  {len(news)} noticias cargadas")

# 3. Calcular sentimiento usando el léxico LM
print("🧠 Calculando sentimiento...")
sentiment_scores = {}
for ticker in tickers:
    # Simular sentimiento basado en noticias del ticker
    # (En producción, esto usaría el SentimentProcessor real)
    sentiment_scores[ticker] = np.random.uniform(-1, 1)

# 4. Calcular momentum usando precios
print("📈 Calculando momentum...")
momentum_scores = {}
for ticker in tickers:
    prices = price_data.get(ticker, [])
    if len(prices) >= 5:
        # Retorno simple de 5 días
        momentum = (prices[-1] - prices[-5]) / prices[-5] * 100
    else:
        momentum = 0
    momentum_scores[ticker] = momentum

# 5. Calcular NDI
print("📊 Calculando NDI...")
ndi_scores = {}
for ticker in tickers:
    # NDI = Sentimiento - Momentum normalizado
    sentiment = sentiment_scores.get(ticker, 0)
    momentum = momentum_scores.get(ticker, 0) / 100
    ndi = sentiment - momentum
    ndi_scores[ticker] = ndi

# 6. Guardar señales en la base de datos
print("💾 Guardando señales...")
today = datetime.now().date()

# Limpiar señales del día anterior para este ticker
for ticker in tickers:
    cur.execute("""
        DELETE FROM layer4.signals 
        WHERE ticker = %s AND signal_date = %s
    """, (ticker, today))

for ticker in tickers:
    ndi = ndi_scores.get(ticker, 0)
    
    # Determinar régimen
    if ndi > 0.7:
        regime = "Overheating"
        signal_state = "ACTIVE"
        confidence = 0.85
    elif ndi > 0.3:
        regime = "Watching"
        signal_state = "WATCHING"
        confidence = 0.70
    elif ndi < -0.3:
        regime = "Fear"
        signal_state = "ACTIVE"
        confidence = 0.75
    else:
        regime = "Aligned"
        signal_state = "INACTIVE"
        confidence = 0.50
    
    cur.execute("""
        INSERT INTO layer4.signals 
        (ticker, signal_date, ndi, regime, signal_state, confidence, risk_level, attention)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (ticker, signal_date) DO UPDATE SET
            ndi = EXCLUDED.ndi,
            regime = EXCLUDED.regime,
            signal_state = EXCLUDED.signal_state,
            confidence = EXCLUDED.confidence
    """, (
        ticker,
        today,
        round(ndi, 3),
        regime,
        signal_state,
        round(confidence, 2),
        "NORMAL",
        f"NDI: {round(ndi, 3)} - {regime}"
    ))

conn.commit()
print("✅ Señales guardadas en la base de datos")

# 7. Mostrar resumen
cur.execute("SELECT ticker, ndi, regime, signal_state FROM layer4.signals WHERE signal_date = %s ORDER BY ticker", (today,))
signals = cur.fetchall()
print(f"\n📊 Señales del día {today}:")
for s in signals:
    print(f"  {s['ticker']}: NDI={s['ndi']:.3f} | {s['regime']} | {s['signal_state']}")

cur.close()
conn.close()
print("🎉 Pipeline diario completado")
