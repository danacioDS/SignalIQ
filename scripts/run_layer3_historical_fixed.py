#!/usr/bin/env python3
"""Procesa datos históricos de Layer 3 y guarda señales (versión corregida)."""

import os
import sys
import psycopg2
import psycopg2.extras
from datetime import datetime, timedelta, date
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from layers.layer3_orchestrator import Layer3Orchestrator
from layers.layer3_momentum import MomentumProcessor
from layers.layer3_sentiment import SentimentProcessor
from layers.layer4_orchestrator import Layer4Orchestrator, process_asset
from layers.layer4_persistence import PersistenceTracker

DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    print("ERROR: DATABASE_URL no configurada")
    sys.exit(1)

def to_float(value):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(value)
    except (ValueError, TypeError):
        return None

def to_int(value):
    if value is None:
        return None
    if isinstance(value, int):
        return value
    try:
        return int(value)
    except (ValueError, TypeError):
        return None

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

print("🚀 Procesando datos históricos para Layer 3...")

# 1. Obtener tickers y precios
tickers = ['NVDA', 'AAPL', 'MSFT', 'TSLA']

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
    price_data[ticker] = [(row['price_date'], float(row['close'])) for row in rows]
    print(f"  {ticker}: {len(price_data[ticker])} precios")

# 2. Obtener noticias
print("📰 Cargando noticias históricas...")
cur.execute("""
    SELECT id, title, content, published_at, created_at
    FROM news_articles
    ORDER BY created_at ASC
    LIMIT 200
""")
news = cur.fetchall()
print(f"  {len(news)} noticias cargadas")

# 3. Procesar noticias en orden cronológico
print("🧠 Procesando noticias...")
orchestrator = Layer3Orchestrator()

# Agrupar noticias por fecha
news_by_date = defaultdict(list)
for item in news:
    headline = item.get('title', '') or item.get('content', '') or 'Market news'
    published_at = item.get('published_at', datetime.now())
    created_at = item.get('created_at', datetime.now())
    
    dt = published_at.date() if published_at else created_at.date()
    
    for ticker in tickers:
        news_by_date[dt].append({
            'ticker': ticker,
            'headline': f"{ticker} - {headline}",
            'published_at': published_at,
            'created_at': created_at,
            'url_param': ticker
        })

print(f"  {len(news_by_date)} días con noticias")

# 4. Procesar día por día en orden cronológico
print("📅 Procesando días...")
tracker = PersistenceTracker()
l4 = Layer4Orchestrator()

# Procesar precios primero (para momentum)
momentum = MomentumProcessor()
for ticker, prices in price_data.items():
    for dt, price in prices:
        momentum.add_price(ticker, dt, price)

# Procesar noticias y finalizar días en orden cronológico
for dt in sorted(news_by_date.keys()):
    # Procesar noticias del día
    for item in news_by_date[dt]:
        orchestrator.process_headline(
            item['headline'],
            item['published_at'],
            item['created_at'],
            item['url_param']
        )
    
    # Finalizar el día
    try:
        result = orchestrator.finalize_day(dt, tickers)
        
        # Generar señales para cada ticker
        for ticker, data in result.items():
            if ticker == "__UNRESOLVED__":
                continue
            
            for date_str, values in data.items():
                sentiment_zscore = values.get('sentiment_zscore')
                momentum_zscore = values.get('momentum_zscore')
                
                prices_hist = [p[1] for p in price_data.get(ticker, [])]
                if not prices_hist:
                    prices_hist = [100.0, 101.0, 102.0, 103.0, 104.0, 105.0]
                
                signal = process_asset(
                    ticker,
                    sentiment_zscore,
                    momentum_zscore,
                    prices_hist,
                    tracker,
                    date_str
                )
                
                # Convertir valores a tipos correctos
                ndi = to_float(signal.get('ndi'))
                confidence = to_float(signal.get('confidence'))
                price_modifier = to_float(signal.get('price_modifier'))
                persistence_days = to_int(signal.get('persistence_days'))
                
                regime = signal.get('regime')
                signal_state = signal.get('signal_state')
                risk_level = signal.get('risk_level')
                attention = signal.get('attention')
                
                # Reemplazar valores no válidos
                if regime in ("INSUFFICIENT_DATA", "insufficient_data"):
                    regime = None
                if signal_state in ("INSUFFICIENT_DATA", "insufficient_data"):
                    signal_state = None
                if risk_level in ("INSUFFICIENT_DATA", "insufficient_data"):
                    risk_level = None
                if attention in ("INSUFFICIENT_DATA", "insufficient_data"):
                    attention = "Insufficient data for reliable signal."
                
                # Insertar en la base de datos
                try:
                    cur.execute("""
                        INSERT INTO layer4.signals 
                        (ticker, signal_date, ndi, regime, signal_state, confidence, 
                         price_modifier, persistence_days, risk_level, attention)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (ticker, signal_date) DO UPDATE SET
                            ndi = EXCLUDED.ndi,
                            regime = EXCLUDED.regime,
                            signal_state = EXCLUDED.signal_state,
                            confidence = EXCLUDED.confidence,
                            price_modifier = EXCLUDED.price_modifier,
                            persistence_days = EXCLUDED.persistence_days,
                            risk_level = EXCLUDED.risk_level,
                            attention = EXCLUDED.attention
                    """, (
                        ticker,
                        date_str,
                        ndi,
                        regime,
                        signal_state,
                        confidence,
                        price_modifier,
                        persistence_days,
                        risk_level,
                        attention
                    ))
                except Exception as e:
                    print(f"  ERROR INSERT: {e}")
                    conn.rollback()
                    continue
        
        conn.commit()
        print(f"  {dt}: OK")
    except Exception as e:
        print(f"  {dt}: ERROR - {e}")
        conn.rollback()
        continue

# 5. Mostrar resumen
try:
    cur.execute("SELECT ticker, COUNT(*) FROM layer4.signals GROUP BY ticker ORDER BY ticker")
    stats = cur.fetchall()
    print(f"\n📊 Resumen de señales:")
    for row in stats:
        print(f"  {row['ticker']}: {row['count']} señales")

    cur.execute("SELECT ticker, ndi, regime, signal_state, confidence FROM layer4.signals ORDER BY signal_date DESC LIMIT 5")
    signals = cur.fetchall()
    print(f"\n📈 Últimas señales:")
    for s in signals:
        ndi_str = f"{s['ndi']:.3f}" if s['ndi'] is not None else "N/A"
        print(f"  {s['ticker']}: NDI={ndi_str} | {s['regime']} | {s['signal_state']} | Conf={s['confidence']}")
except Exception as e:
    print(f"Error en resumen: {e}")

cur.close()
conn.close()
print("🎉 Pipeline histórico completado")
