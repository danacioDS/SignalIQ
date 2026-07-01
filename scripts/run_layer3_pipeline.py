#!/usr/bin/env python3
"""Ejecuta el pipeline completo de Layer 3 y guarda señales en la base de datos."""

import os
import sys
import psycopg2
import psycopg2.extras
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from layers.layer3_orchestrator import Layer3Orchestrator
from layers.layer4_orchestrator import Layer4Orchestrator
from layers.layer4_persistence import PersistenceTracker

DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    print("ERROR: DATABASE_URL no configurada")
    sys.exit(1)

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

print("🚀 Iniciando pipeline de Layer 3...")

# 1. Obtener noticias
print("📰 Obteniendo noticias...")
cur.execute("""
    SELECT id, title, content, source, url, published_at, created_at
    FROM public.news_articles
    ORDER BY created_at DESC
    LIMIT 100
""")
news = cur.fetchall()
print(f"✅ {len(news)} noticias obtenidas")

if len(news) == 0:
    print("⚠️ No hay noticias. Creando datos de prueba...")
    sys.exit(0)

# 2. Procesar con Layer 3
print("🧠 Procesando sentimiento y momentum...")
orchestrator = Layer3Orchestrator()

tickers = ['NVDA', 'AAPL', 'MSFT', 'TSLA', 'GOOGL', 'META', 'AMD', 'AMZN', 'JPM', 'KO']

for item in news:
    headline = item.get('title', '') or item.get('content', '') or 'Market news'
    published_at = item.get('published_at', datetime.now())
    created_at = item.get('created_at', datetime.now())
    
    for ticker in tickers:
        try:
            orchestrator.process_headline(
                f"{ticker} - {headline}",
                published_at,
                created_at,
                ticker
            )
        except Exception as e:
            print(f"⚠️ Error procesando {ticker}: {e}")

today = datetime.now().date()
result = orchestrator.finalize_day(today)

print(f"✅ Procesados {len(result)} tickers")

# 3. Obtener precios reales de la base de datos
print("📊 Obteniendo precios reales...")
price_history_dict = {}
for ticker in tickers:
    cur.execute("""
        SELECT close FROM prices 
        WHERE ticker = %s 
        ORDER BY price_date DESC 
        LIMIT 30
    """, (ticker,))
    rows = cur.fetchall()
    if rows:
        price_history_dict[ticker] = [float(row['close']) for row in rows]
    else:
        price_history_dict[ticker] = [100.0, 101.0, 102.0, 103.0, 104.0, 105.0]
    print(f"  {ticker}: {len(price_history_dict[ticker])} precios")

# 4. Generar señales con Layer 4
print("📊 Generando señales...")
l4 = Layer4Orchestrator()
tracker = PersistenceTracker()

for ticker, data in result.items():
    if ticker == "__UNRESOLVED__":
        continue
    
    for date_str, values in data.items():
        sentiment_zscore = values.get('sentiment_zscore')
        momentum_zscore = values.get('momentum_zscore')
        
        # Usar precios reales
        price_history = price_history_dict.get(ticker, [100.0, 101.0, 102.0, 103.0, 104.0, 105.0])
        
        from layers.layer4_orchestrator import process_asset
        
        signal = process_asset(
            ticker, 
            sentiment_zscore, 
            momentum_zscore, 
            price_history, 
            tracker, 
            date_str
        )
        
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
        
        ndi = to_float(signal.get('ndi'))
        confidence = to_float(signal.get('confidence'))
        price_modifier = to_float(signal.get('price_modifier'))
        persistence_days = to_int(signal.get('persistence_days'))
        
        regime = signal.get('regime')
        signal_state = signal.get('signal_state')
        risk_level = signal.get('risk_level')
        attention = signal.get('attention')
        
        if regime == "INSUFFICIENT_DATA" or regime == "insufficient_data":
            regime = None
        if signal_state == "INSUFFICIENT_DATA" or signal_state == "insufficient_data":
            signal_state = None
        if risk_level == "INSUFFICIENT_DATA" or risk_level == "insufficient_data":
            risk_level = None
        
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

conn.commit()
print("✅ Señales guardadas en la base de datos")

# 5. Mostrar resumen
cur.execute("SELECT COUNT(*) FROM layer4.signals WHERE signal_date = CURRENT_DATE")
count = cur.fetchone()['count']
print(f"📊 Total señales del día: {count}")

cur.execute("SELECT ticker, ndi, regime, signal_state FROM layer4.signals WHERE signal_date = CURRENT_DATE ORDER BY ticker")
signals = cur.fetchall()
for s in signals:
    ndi_str = f"{s['ndi']:.3f}" if s['ndi'] is not None else "N/A"
    print(f"  {s['ticker']}: NDI={ndi_str} | {s['regime']} | {s['signal_state']}")

cur.close()
conn.close()
print("🎉 Pipeline completado")
