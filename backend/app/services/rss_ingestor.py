"""RSS Ingestor - Solo Reuters y MarketWatch"""
import hashlib
import feedparser
import os
import psycopg2
from psycopg2.extras import Json
from datetime import datetime
from typing import Dict, Optional

class RSSIngestor:
    def __init__(self):
        self.database_url = os.environ.get('DATABASE_URL')
        self.sources = {
            'reuters': 'http://feeds.reuters.com/reuters/businessNews',
            'marketwatch': 'https://www.marketwatch.com/rss/topstories'
        }
    
    def get_db_connection(self):
        return psycopg2.connect(self.database_url)
    
    def news_exists(self, content_hash: str) -> bool:
        with self.get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM news_articles WHERE content_hash = %s", (content_hash,))
                return cur.fetchone() is not None
    
    def save_news(self, news_item: Dict) -> int:
        with self.get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO news_articles (title, content, source, url, content_hash, published_at, raw_data)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (content_hash) DO NOTHING
                    RETURNING id
                """, (
                    news_item['title'],
                    news_item['content'],
                    news_item['source'],
                    news_item['url'],
                    news_item['content_hash'],
                    news_item['published_at'],
                    Json(news_item['raw_data'])
                ))
                result = cur.fetchone()
                return result[0] if result else None
    
    def fetch_and_save(self, limit: int = 20):
        articles_processed = 0
        
        for source_name, feed_url in self.sources.items():
            try:
                print(f"📰 Procesando {source_name}...")
                feed = feedparser.parse(feed_url)
                
                for entry in feed.entries[:limit]:
                    content_hash = hashlib.sha256(
                        f"{entry.title}{entry.description}".encode()
                    ).hexdigest()
                    
                    if self.news_exists(content_hash):
                        continue
                    
                    published_at = None
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        published_at = datetime(*entry.published_parsed[:6])
                    
                    news_item = {
                        'title': entry.title,
                        'content': entry.description,
                        'source': source_name,
                        'url': entry.link,
                        'content_hash': content_hash,
                        'published_at': published_at,
                        'raw_data': entry
                    }
                    
                    news_id = self.save_news(news_item)
                    if news_id:
                        articles_processed += 1
                        print(f"   ✅ Guardada: {entry.title[:50]}...")
                
            except Exception as e:
                print(f"   ❌ Error con {source_name}: {e}")
        
        print(f"\n📊 Total noticias nuevas: {articles_processed}")
        return articles_processed

if __name__ == "__main__":
    ingestor = RSSIngestor()
    ingestor.fetch_and_save(limit=10)
