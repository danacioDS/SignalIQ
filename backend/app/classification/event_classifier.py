"""
Clasificador de eventos - Base para todo el scoring
"""
from typing import Dict, List

class EventClassifier:
    EVENT_TYPES = {
        'earnings': {
            'keywords': ['earnings', 'quarterly results', 'financial results', 'profit report', 'q1', 'q2', 'q3', 'q4'],
            'weight': 100
        },
        'guidance': {
            'keywords': ['guidance', 'outlook', 'forecast', 'expects', 'projects', 'estimates'],
            'weight': 95
        },
        'merger_acquisition': {
            'keywords': ['acquisition', 'merger', 'acquires', 'to buy', 'takeover', 'deal'],
            'weight': 90
        },
        'analyst_upgrade': {
            'keywords': ['upgrade', 'overweight', 'buy rating', 'price target raised'],
            'weight': 85
        },
        'analyst_downgrade': {
            'keywords': ['downgrade', 'underweight', 'sell rating', 'price target cut'],
            'weight': 85
        },
        'product_launch': {
            'keywords': ['launch', 'releases', 'introduces', 'unveils', 'new product'],
            'weight': 75
        },
        'regulatory': {
            'keywords': ['sec', 'regulatory', 'investigation', 'fines', 'compliance'],
            'weight': 80
        },
        'lawsuit': {
            'keywords': ['lawsuit', 'sues', 'litigation', 'settlement', 'legal'],
            'weight': 75
        },
        'executive_change': {
            'keywords': ['ceo', 'cfo', 'appoints', 'resigns', 'steps down', 'hires', 'executive'],
            'weight': 65
        }
    }
    
    def classify(self, title: str, content: str) -> Dict:
        """Clasifica el evento principal de la noticia"""
        text = f"{title} {content}".lower()
        
        scores = {}
        for event_type, info in self.EVENT_TYPES.items():
            matches = sum(1 for kw in info['keywords'] if kw in text)
            if matches > 0:
                scores[event_type] = {
                    'matches': matches,
                    'weight': info['weight']
                }
        
        if not scores:
            return {
                'event_type': 'general_news',
                'confidence': 0.5,
                'weight': 30
            }
        
        best_event = max(scores.items(), key=lambda x: x[1]['matches'])
        
        return {
            'event_type': best_event[0],
            'confidence': min(0.5 + (best_event[1]['matches'] * 0.1), 0.95),
            'weight': best_event[1]['weight']
        }
