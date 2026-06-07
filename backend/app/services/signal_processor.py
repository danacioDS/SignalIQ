"""Procesa noticias y genera SignalIQ Scores"""
import os
import re
import psycopg2
from psycopg2.extras import Json
from app.scoring.signal_score import SignalIQScore
from app.classification.event_classifier import EventClassifier

class SignalProcessor:
    def __init__(self):
        self.database_url = os.environ.get('DATABASE_URL')
        self.scorer = SignalIQScore()
        self.classifier = EventClassifier()
        self.score_config_id = self.get_active_config_id()
    
    def get_active_config_id(self):
        with psycopg2.connect(self.database_url) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM score_configs WHERE is_active = true LIMIT 1")
                result = cur.fetchone()
                return result[0] if result else 1
    
    def detect_tickers(self, text: str) -> list:
        """Detección simple de tickers (mayúsculas de 2-4 letras)"""
        pattern = r'\b([A-Z]{2,4})\b'
        tickers = re.findall(pattern, text)
        common_words = {'THE', 'AND', 'FOR', 'WITH', 'FROM', 'THIS', 'THAT', 'WHAT', 'HAVE', 'WILL'}
        return list(set([t for t in tickers if t not in common_words]))[:5]
    
    def process_unprocessed_news(self):
        """Procesa noticias que aún no tienen señales"""
        
        with psycopg2.connect(self.database_url) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT na.id, na.title, na.content, na.source
                    FROM news_articles na
                    LEFT JOIN signal_predictions sp ON na.id = sp.news_article_id
                    WHERE sp.id IS NULL
                    ORDER BY na.created_at DESC
                    LIMIT 50
                """)
                
                unprocessed = cur.fetchall()
                
                for news_id, title, content, source in unprocessed:
                    text = title + " " + (content or "")
                    detected_tickers = self.detect_tickers(text)
                    
                    for ticker in detected_tickers:
                        score_result = self.scorer.calculate({
                            'title': title,
                            'content': content or '',
                            'ticker': ticker,
                            'source': source,
                            'sentiment': 'neutral'
                        })
                        
                        cur.execute("""
                            INSERT INTO signal_predictions (
                                news_article_id, score_config_id, ticker, score, confidence,
                                signal, strength, sentiment_score, relevance_score,
                                source_quality_score, event_type_score, event_type,
                                event_confidence, explanation, created_at
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                        """, (
                            news_id, self.score_config_id, ticker, score_result['score'],
                            score_result.get('event_confidence', 0.5), score_result['signal'],
                            score_result['strength'], score_result['components']['sentiment'],
                            score_result['components']['relevance'], score_result['components']['source_quality'],
                            score_result['components']['event_type'], score_result['event_type'],
                            score_result['event_confidence'], score_result['explanation']
                        ))
                        
                        print(f"✅ {ticker}: Score {score_result['score']} - {score_result['signal']}")
                    
                    conn.commit()
    
    def run_full_pipeline(self):
        print("🔄 Iniciando pipeline de procesamiento...")
        
        from app.services.rss_ingestor import RSSIngestor
        ingestor = RSSIngestor()
        new_articles = ingestor.fetch_and_save(limit=20)
        
        if new_articles > 0:
            print(f"\n📊 Procesando {new_articles} noticias...")
            self.process_unprocessed_news()
        
        print("✅ Pipeline completado")

if __name__ == "__main__":
    processor = SignalProcessor()
    processor.run_full_pipeline()
