"""
NewsFetcher - Obtiene noticias reales desde NewsAPI
"""

import os
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any

class NewsFetcher:
    def __init__(self):
        self.api_key = os.environ.get('NEWS_API_KEY')
        self.base_url = "https://newsapi.org/v2"

    def fetch_news(self, query: str = None, days_back: int = 1) -> List[Dict[str, Any]]:
        """Obtiene noticias reales desde NewsAPI."""
        if not self.api_key:
            print("⚠️ NEWS_API_KEY no configurada. Usando datos de ejemplo.")
            return self._get_sample_news()

        query = query or "stocks OR markets OR earnings"
        from_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")

        params = {
            "q": query,
            "from": from_date,
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": 20,
            "apiKey": self.api_key,
        }

        try:
            response = requests.get(f"{self.base_url}/everything", params=params, timeout=10)
            data = response.json()

            if data.get("status") != "ok":
                print(f"⚠️ NewsAPI error: {data.get('message', 'Unknown error')}")
                return []

            articles = []
            for a in data.get("articles", []):
                title = a.get("title", "")
                description = a.get("description", "")
                content = a.get("content", "")

                # Limpiar contenido
                if content and "..." in content:
                    content = content.split("[")[0] if "[" in content else content

                # Si no hay content, usar description
                if not content and description:
                    content = description

                articles.append({
                    "title": title,
                    "description": description or "",
                    "content": content or "",
                    "source": a.get("source", {}).get("name", "Unknown"),
                    "url": a.get("url", ""),
                    "published_at": a.get("publishedAt", datetime.now().isoformat()),
                })

            return articles

        except Exception as e:
            print(f"⚠️ Error fetching news: {e}")
            return self._get_sample_news()

    def _get_sample_news(self) -> List[Dict[str, Any]]:
        """Datos de ejemplo cuando la API no está disponible."""
        return [
            {
                "title": "NVIDIA beats earnings expectations as AI demand surges",
                "description": "NVIDIA reported Q1 earnings that exceeded analyst estimates",
                "content": "The company's revenue grew 25% year-over-year driven by AI demand.",
                "source": "Example News",
                "url": "https://example.com/nvidia-earnings",
                "published_at": datetime.now().isoformat(),
            },
            {
                "title": "Apple announces new product lineup",
                "description": "Apple unveiled new products including updated iPads and MacBooks",
                "content": "The new lineup features enhanced AI capabilities.",
                "source": "Example News",
                "url": "https://example.com/apple-products",
                "published_at": datetime.now().isoformat(),
            },
        ]
