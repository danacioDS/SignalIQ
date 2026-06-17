"""
NarrativeBuilder - Genera narrativa de mercado desde eventos
"""

from typing import List, Dict, Any

class NarrativeBuilder:
    def __init__(self):
        self.sector_narratives = {
            'Technology': 'Tech sector driving AI-led innovation narrative',
            'Automotive': 'Automotive sector navigating transition to electric',
            'Financial': 'Financial sector adapting to changing rate environment',
            'Consumer': 'Consumer sector showing resilience in spending',
            'Energy': 'Energy sector benefiting from commodity price dynamics',
            'Healthcare': 'Healthcare sector innovating with AI and gene therapies',
            'Semiconductors': 'Semiconductor cycle showing signs of bottoming',
        }

    def generate(self, events: List[str], sector: str, ndi: float) -> List[str]:
        """Genera narrativa de mercado desde eventos."""
        narratives = []

        # Narrativa basada en eventos
        if events:
            if any('Earnings Beat' in e for e in events):
                narratives.append('Earnings season driving price discovery')
            if any('Analyst Upgrade' in e for e in events):
                narratives.append('Analyst sentiment turning increasingly positive')
            if any('Analyst Downgrade' in e for e in events):
                narratives.append('Caution emerging from analyst community')
            if any('Product Launch' in e for e in events):
                narratives.append('Product innovation cycle gaining momentum')
            if any('Macroeconomic Event' in e for e in events):
                narratives.append('Macroeconomic factors influencing market direction')
            if any('Strategic Partnership' in e for e in events):
                narratives.append('Strategic partnerships reshaping competitive landscape')
            if any('Business Expansion' in e for e in events):
                narratives.append('Business expansion indicating growth phase')

        # Narrativa basada en sector
        if sector in self.sector_narratives:
            narratives.append(self.sector_narratives[sector])

        # Narrativa basada en NDI
        if ndi > 0.7:
            narratives.append('Narrative momentum significantly ahead of price action')
        elif ndi < -0.5:
            narratives.append('Price action disconnecting from fundamental narrative')
        else:
            narratives.append('Narrative and price action remain aligned')

        # Si no hay narrativas, agregar una por defecto
        if not narratives:
            narratives.append('Market sentiment remains stable with no clear narrative')

        return narratives[:3]  # Máximo 3 narrativas

    def generate_from_events(self, events_data: List[Dict[str, Any]], ticker: str, ndi: float) -> List[str]:
        """Genera narrativa desde eventos estructurados."""
        sector = self._get_sector(ticker)
        event_labels = [e.get('label', '') for e in events_data if e.get('label')]
        return self.generate(event_labels, sector, ndi)

    def _get_sector(self, ticker: str) -> str:
        sector_map = {
            'NVDA': 'Technology', 'AAPL': 'Technology', 'MSFT': 'Technology',
            'GOOGL': 'Technology', 'META': 'Technology', 'AMD': 'Technology',
            'AMZN': 'Technology', 'TSLA': 'Automotive', 'JPM': 'Financial',
            'KO': 'Consumer'
        }
        return sector_map.get(ticker, 'Other')
