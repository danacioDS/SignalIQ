"""Pipeline de noticias con caché de 15 minutos"""
import feedparser
import re
from textblob import TextBlob
from datetime import datetime, timedelta

RSS_FEEDS = [
    'https://news.google.com/rss/search?q={ticker}+stock+when:1d&hl=en-US&gl=US&ceid=US:en',
    'https://news.google.com/rss/search?q={ticker}+earnings+when:1d&hl=en-US&gl=US&ceid=US:en',
    'https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}',
    'https://www.marketwatch.com/rss/topstories',
]

_news_cache = {}
_NEWS_CACHE_TTL = 900  # 15 minutos

def polarity(text):
    try:
        return TextBlob(text).sentiment.polarity
    except:
        return 0.0

def fetch_news(ticker, max_items=20):
    headlines = []
    seen = set()
    
    for feed_url in RSS_FEEDS:
        try:
            url = feed_url.format(ticker=ticker)
            feed = feedparser.parse(url)
            for entry in feed.entries[:10]:
                title = entry.title
                if (ticker.lower() in title.lower() or 
                    any(word in title.lower() for word in ['stock', 'share', 'earnings', 'profit'])):
                    if title not in seen:
                        headlines.append(title)
                        seen.add(title)
        except:
            continue
    
    if not headlines:
        try:
            alt_url = f'https://news.google.com/rss/search?q={ticker}+technology+when:1d&hl=en-US&gl=US&ceid=US:en'
            feed = feedparser.parse(alt_url)
            for entry in feed.entries[:5]:
                title = entry.title
                if ticker.lower() in title.lower() and title not in seen:
                    headlines.append(title)
                    seen.add(title)
        except:
            pass
    
    return headlines[:max_items]

def process_news_for_ticker(ticker):
    """Procesa noticias con caché de 15 minutos"""
    if ticker in _news_cache:
        data, timestamp = _news_cache[ticker]
        if (datetime.now() - timestamp).total_seconds() < _NEWS_CACHE_TTL:
            return data
    
    headlines = fetch_news(ticker)
    
    if not headlines:
        result = {'sentiment': 0.0, 'count': 0, 'headlines': [f"No hay noticias recientes para {ticker}"], 'scores': [0.0]}
    else:
        sentiment_scores = []
        for headline in headlines:
            try:
                sentiment_scores.append(polarity(headline))
            except:
                sentiment_scores.append(0.0)
        
        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0.0
        result = {
            'sentiment': avg_sentiment,
            'count': len(headlines),
            'headlines': headlines[:10],
            'scores': sentiment_scores[:10]
        }
    
    _news_cache[ticker] = (result, datetime.now())
    return result

if __name__ == '__main__':
    import sys
    ticker = sys.argv[1] if len(sys.argv) > 1 else 'NVDA'
    result = process_news_for_ticker(ticker)
    print(f"📰 {ticker}: {result['count']} noticias, sentimiento: {result['sentiment']:.3f}")
