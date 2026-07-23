"""
Pipeline de noticias - Simple e independiente
"""
import feedparser
import re
from textblob import TextBlob

# Fuentes RSS (sin depender de otros módulos)
RSS_FEEDS = [
    'https://news.google.com/rss/search?q={ticker}+stock+when:1d&hl=en-US&gl=US&ceid=US:en',
    'https://news.google.com/rss/search?q={ticker}+earnings+when:1d&hl=en-US&gl=US&ceid=US:en',
    'https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}',
    'https://www.marketwatch.com/rss/topstories',
]

def polarity(text):
    """Análisis de sentimiento simple usando TextBlob"""
    try:
        blob = TextBlob(text)
        return blob.sentiment.polarity
    except:
        return 0.0

def fetch_news(ticker, max_items=20):
    """Obtiene noticias relacionadas con un ticker desde múltiples fuentes"""
    headlines = []
    seen = set()
    
    for feed_url in RSS_FEEDS:
        try:
            # Reemplazar {ticker} con el ticker buscado
            url = feed_url.format(ticker=ticker)
            feed = feedparser.parse(url)
            
            for entry in feed.entries[:10]:
                title = entry.title
                # Verificar que el título contenga el ticker o palabras clave
                if (ticker.lower() in title.lower() or 
                    any(word in title.lower() for word in ['stock', 'share', 'earnings', 'profit'])):
                    if title not in seen:
                        headlines.append(title)
                        seen.add(title)
        except Exception as e:
            print(f"⚠️ Error con feed: {e}")
            continue
    
    # Si no hay noticias, buscar con términos alternativos
    if not headlines:
        try:
            alt_feeds = [
                f'https://news.google.com/rss/search?q={ticker}+technology+when:1d&hl=en-US&gl=US&ceid=US:en',
            ]
            for feed_url in alt_feeds:
                url = feed_url.format(ticker=ticker)
                feed = feedparser.parse(url)
                for entry in feed.entries[:5]:
                    title = entry.title
                    if ticker.lower() in title.lower() and title not in seen:
                        headlines.append(title)
                        seen.add(title)
        except:
            pass
    
    return headlines[:max_items]

def process_news_for_ticker(ticker):
    """Procesa noticias y calcula sentimiento"""
    headlines = fetch_news(ticker)
    
    if not headlines:
        return {
            'sentiment': 0.0,
            'count': 0,
            'headlines': [f"No hay noticias recientes para {ticker}"],
            'scores': [0.0]
        }
    
    sentiment_scores = []
    for headline in headlines:
        try:
            score = polarity(headline)
            sentiment_scores.append(score)
        except Exception as e:
            print(f"⚠️ Error procesando: {headline[:50]}... {e}")
            sentiment_scores.append(0.0)
    
    avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0.0
    
    return {
        'sentiment': avg_sentiment,
        'count': len(headlines),
        'headlines': headlines[:10],
        'scores': sentiment_scores[:10]
    }

if __name__ == '__main__':
    import sys
    ticker = sys.argv[1] if len(sys.argv) > 1 else 'NVDA'
    print(f"🔍 Buscando noticias para {ticker}...")
    result = process_news_for_ticker(ticker)
    print(f"\n📰 Noticias para {ticker}: {result['count']}")
    print(f"📊 Sentimiento promedio: {result['sentiment']:.3f}")
    for i, (h, s) in enumerate(zip(result['headlines'], result['scores'])):
        print(f"  {i+1}. {h[:100]}... (sentiment: {s:.3f})")
