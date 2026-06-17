"""
EventExtractor - Extrae eventos de noticias
"""

import re
from typing import List, Dict, Any

class EventExtractor:
    def __init__(self):
        self.event_patterns = {
            'earnings_beat': r'(beat|exceed|surpass).*(earnings|estimates|expectations)',
            'earnings_miss': r'(miss|fall short|below).*(earnings|estimates|expectations)',
            'upgrade': r'(upgraded|raised|increase).*(price target|rating|outlook|guidance)',
            'downgrade': r'(downgraded|lowered|decrease).*(price target|rating|outlook)',
            'product_launch': r'(launch|announced|released|unveiled).*(product|device|software|service)',
            'acquisition': r'(acquired|merger|buyout|deal).*(company|division|asset)',
            'regulatory': r'(approved|denied|investigation|fine|settlement)',
            'macro': r'(Fed|rate hike|inflation|CPI|employment|jobs)',
            'partnership': r'(partner|collaboration|alliance).*(with|and)',
            'expansion': r'(expand|growth|new market|open).*(plant|factory|office|market)',
        }

        self.event_labels = {
            'earnings_beat': 'Earnings Beat',
            'earnings_miss': 'Earnings Miss',
            'upgrade': 'Analyst Upgrade',
            'downgrade': 'Analyst Downgrade',
            'product_launch': 'Product Launch',
            'acquisition': 'Merger or Acquisition',
            'regulatory': 'Regulatory Development',
            'macro': 'Macroeconomic Event',
            'partnership': 'Strategic Partnership',
            'expansion': 'Business Expansion',
        }

    def extract_events(self, text: str) -> List[Dict[str, Any]]:
        """Extrae eventos de un texto."""
        if not text:
            return []

        text_lower = text.lower()
        events = []

        for pattern_key, pattern in self.event_patterns.items():
            if re.search(pattern, text_lower):
                events.append({
                    'event_type': pattern_key,
                    'label': self.event_labels.get(pattern_key, 'Event'),
                    'confidence': 0.85,
                })

        return events[:3]  # Máximo 3 eventos

    def extract_from_article(self, article: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extrae eventos de un artículo de noticias."""
        text = f"{article.get('title', '')} {article.get('content', '')}"
        return self.extract_events(text)
