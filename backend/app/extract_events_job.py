"""
ExtractEventsJob - Extrae eventos de noticias guardadas
"""

import os
import sys
import psycopg2
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.event_extractor import EventExtractor

DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    print("❌ ERROR: DATABASE_URL no configurada")
    sys.exit(1)

print("📊 EXTRAYENDO EVENTOS...")
print(f"🕐 {datetime.now().isoformat()}")

try:
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    # Obtener noticias sin procesar
    cur.execute("""
        SELECT id, title, content
        FROM news_articles
        WHERE id NOT IN (SELECT DISTINCT article_id FROM news_events)
        ORDER BY created_at DESC
        LIMIT 50
    """)
    articles = cur.fetchall()
    print(f"✅ {len(articles)} noticias sin procesar")

    extractor = EventExtractor()
    inserted = 0
    skipped = 0

    for article_id, title, content in articles:
        article = {'title': title, 'content': content}
        events = extractor.extract_from_article(article)

        if not events:
            skipped += 1
            continue

        for event in events:
            cur.execute("""
                INSERT INTO news_events
                (article_id, ticker, event_type, label, confidence)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                article_id,
                None,  # ticker se asignará más tarde
                event['event_type'],
                event['label'],
                event['confidence'],
            ))
            inserted += 1

    conn.commit()
    print(f"✅ {inserted} eventos insertados, {skipped} noticias sin eventos")

    cur.close()
    conn.close()
    print("🎉 Extracción completada")

except Exception as e:
    print(f"❌ Error en la extracción: {e}")
    sys.exit(1)
