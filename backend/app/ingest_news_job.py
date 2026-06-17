"""
IngestNewsJob - Orquestador de ingesta de noticias
Se ejecuta cada 15 minutos como background job
"""

import os
import sys
import psycopg2
import hashlib
from datetime import datetime

# Agregar directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.news_fetcher import NewsFetcher
from app.entity_linking import EntityLinker

DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    print("❌ ERROR: DATABASE_URL no configurada")
    sys.exit(1)

print("📰 INGESTANDO NOTICIAS...")
print(f"🕐 {datetime.now().isoformat()}")

try:
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    fetcher = NewsFetcher()
    articles = fetcher.fetch_news()

    if not articles:
        print("⚠️ No se obtuvieron noticias")
        sys.exit(0)

    print(f"✅ {len(articles)} noticias obtenidas")

    linker = EntityLinker()
    inserted = 0
    skipped = 0

    for article in articles:
        title = article.get('title', '')
        if not title:
            continue

        # Extraer tickers
        tickers = linker.extract_from_article(article)
        
        # Generar content_hash (para deduplicación)
        content = article.get('content', '') or article.get('description', '')
        content_hash = hashlib.sha256(content.encode()).hexdigest() if content else None

        try:
            cur.execute("""
                INSERT INTO news_articles
                (title, content, source, url, content_hash, published_at, raw_data)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (url) DO NOTHING
            """, (
                title,
                content or article.get('description', ''),
                article.get('source', 'Unknown'),
                article.get('url', ''),
                content_hash,
                article.get('published_at'),
                '{}',  # raw_data vacío por ahora
            ))
            if cur.rowcount > 0:
                inserted += 1
                # Si insertamos, guardamos los tickers en una tabla separada o en una columna
                # Por ahora, los tickers se guardarán en la tabla news_events más adelante
            else:
                skipped += 1
        except Exception as e:
            print(f"⚠️ Error insertando noticia: {e}")
            skipped += 1

    conn.commit()
    print(f"✅ {inserted} noticias insertadas, {skipped} omitidas")

    cur.close()
    conn.close()
    print("🎉 Ingesta completada")

except Exception as e:
    print(f"❌ Error en la ingesta: {e}")
    sys.exit(1)
