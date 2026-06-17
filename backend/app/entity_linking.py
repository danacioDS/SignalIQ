"""
EntityLinking - Detecta tickers en textos de noticias
"""

from typing import List, Dict, Any

class EntityLinker:
    def __init__(self):
        self.ticker_map = {
            'nvidia': 'NVDA',
            'apple': 'AAPL',
            'microsoft': 'MSFT',
            'tesla': 'TSLA',
            'google': 'GOOGL',
            'alphabet': 'GOOGL',
            'meta': 'META',
            'facebook': 'META',
            'amd': 'AMD',
            'amazon': 'AMZN',
            'jpmorgan': 'JPM',
            'coca-cola': 'KO',
            'coke': 'KO',
        }

    def extract_tickers(self, text: str) -> List[str]:
        """Extrae tickers de un texto."""
        if not text:
            return []

        text_lower = text.lower()
        found = set()

        for company, ticker in self.ticker_map.items():
            if company in text_lower:
                found.add(ticker)

        return list(found)

    def extract_from_article(self, article: Dict[str, Any]) -> List[str]:
        """Extrae tickers de un artículo de noticias."""
        text = f"{article.get('title', '')} {article.get('description', '')} {article.get('content', '')}"
        return self.extract_tickers(text)
