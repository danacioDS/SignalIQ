"""
StoreIntelJob - Orquestador: eventos → narrative → intel_signals
"""

import os
import sys
import psycopg2
import psycopg2.extras
from datetime import datetime
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.narrative_builder import NarrativeBuilder

DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    print("❌ ERROR: DATABASE_URL no configurada")
    sys.exit(1)

print("📊 GENERANDO NARRATIVE E INTELIGENCIA...")
print(f"🕐 {datetime.now().isoformat()}")

try:
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # 1. Obtener tickers con eventos sin procesar
    cur.execute("""
        SELECT DISTINCT ne.ticker, ne.article_id, ne.label, ne.event_type
        FROM news_events ne
        WHERE ne.ticker IS NOT NULL
        AND ne.ticker NOT IN (
            SELECT DISTINCT ticker FROM intel_signals
        )
        ORDER BY ne.ticker
    """)
    events_data = cur.fetchall()

    if not events_data:
        print("⚠️ No hay eventos nuevos para procesar")
        sys.exit(0)

    print(f"✅ {len(events_data)} eventos sin procesar")

    # 2. Agrupar eventos por ticker
    events_by_ticker = {}
    for e in events_data:
        ticker = e.get('ticker')
        if ticker:
            if ticker not in events_by_ticker:
                events_by_ticker[ticker] = []
            events_by_ticker[ticker].append({
                'label': e.get('label'),
                'event_type': e.get('event_type'),
                'article_id': e.get('article_id')
            })

    print(f"📊 {len(events_by_ticker)} tickers con eventos")

    # 3. Generar narrative e insertar en intel_signals
    narrative_builder = NarrativeBuilder()
    inserted = 0

    for ticker, events in events_by_ticker.items():
        # Obtener NDI para este ticker
        cur.execute("""
            SELECT ndi
            FROM layer4.signals
            WHERE ticker = %s
            ORDER BY signal_date DESC
            LIMIT 1
        """, (ticker,))
        signal = cur.fetchone()

        ndi = float(signal['ndi']) if signal and signal['ndi'] else 0.0

        # Generar narrative
        event_labels = [e['label'] for e in events if e['label']]
        narrative = narrative_builder.generate(event_labels, narrative_builder._get_sector(ticker), ndi)

        # Guardar en intel_signals
        cur.execute("""
            INSERT INTO intel_signals
            (ticker, signal_timestamp, ndi, events, narrative, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            ticker,
            datetime.now(),
            ndi,
            json.dumps(events),
            json.dumps(narrative),
            datetime.now()
        ))

        inserted += 1
        print(f"  ✅ {ticker}: {len(events)} eventos → {len(narrative)} narrativas")

    conn.commit()
    print(f"✅ {inserted} señales de inteligencia guardadas")

    # 4. Mostrar resumen
    cur.execute("SELECT COUNT(*) FROM intel_signals")
    total = cur.fetchone()['count']
    print(f"📊 Total en intel_signals: {total}")

    cur.close()
    conn.close()
    print("🎉 StoreIntelJob completado")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
