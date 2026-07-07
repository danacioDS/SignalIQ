"""
Pipeline de noticias - Múltiples fuentes RSS
"""
import feedparser
import sys
import requests
import json

# Agregar layers al path
sys.path.append('/home/daniel/repo_lab/SignalIQ')
from layers.layer3_sentiment import polarity

# Fuentes RSS alternativas (más confiables)
RSS_FEEDS = [
    'https://news.google.com/rss/search?q=NVDA+when:1d&hl=en-US&gl=US&ceid=US:en',
    'https://news.google.com/rss/search?q=NVIDIA+stock+when:1d&hl=en-US&gl=US&ceid=US:en',
    'https://finance.yahoo.com/rss/headline?s=NVDA',
    'https://feeds.finance.yahoo.com/rss/2.0/headline?s=NVDA',
    'https://www.marketwatch.com/rss/topstories',
]

def fetch_news(ticker, max_items=20):
    """Obtiene noticias relacionadas con un ticker desde múltiples fuentes"""
    headlines = []
    seen = set()
    
    for feed_url in RSS_FEEDS:
        try:
            # Reemplazar NVDA en la URL con el ticker buscado
            url = feed_url.replace('NVDA', ticker)
            feed = feedparser.parse(url)
            
            for entry in feed.entries[:10]:
                title = entry.title
                # Verificar que el título contenga el ticker
                if ticker.lower() in title.lower() and title not in seen:
                    headlines.append(title)
                    seen.add(title)
        except Exception as e:
            print(f"⚠️ Error con {feed_url}: {e}")
    
    return headlines[:max_items]

def process_news_for_ticker(ticker):
    """Procesa noticias y calcula sentimiento"""
    headlines = fetch_news(ticker)
    
    if not headlines:
        return {'sentiment': 0, 'count': 0, 'headlines': [], 'scores': []}
    
    sentiment_scores = []
    for headline in headlines:
        try:
            score = polarity(headline)
            sentiment_scores.append(score)
        except Exception as e:
            print(f"⚠️ Error procesando: {headline[:50]}... {e}")
            sentiment_scores.append(0)
    
    return {
        'sentiment': sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0,
        'count': len(headlines),
        'headlines': headlines,
        'scores': sentiment_scores
    }

if __name__ == '__main__':
    ticker = sys.argv[1] if len(sys.argv) > 1 else 'NVDA'
    print(f"🔍 Buscando noticias para {ticker}...")
    result = process_news_for_ticker(ticker)
    print(f"\n📰 Noticias para {ticker}: {result['count']}")
    print(f"📊 Sentimiento promedio: {result['sentiment']:.3f}")
    for i, (h, s) in enumerate(zip(result['headlines'], result['scores'])):
        print(f"  {i+1}. {h[:100]}... (sentiment: {s:.3f})")
