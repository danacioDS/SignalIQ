"""
SignalIQ Score - Simple, medible, versionado
"""
from typing import Dict
from datetime import datetime
from app.classification.event_classifier import EventClassifier

class SignalIQScore:
    VERSION = "v1.0"
    
    def __init__(self, event_classifier=None):
        self.event_classifier = event_classifier or EventClassifier()
        
        self.weights = {
            'sentiment': 0.35,
            'relevance': 0.25,
            'source_quality': 0.20,
            'event_type': 0.20
        }
        
        self.source_scores = {
            'bloomberg': 100, 'reuters': 100,
            'wsj': 95, 'financial_times': 95,
            'cnbc': 80, 'yahoo_finance': 70,
            'seeking_alpha': 60, 'benzinga': 55,
            'default': 40
        }
        
        self.sentiment_map = {
            'very_bullish': 90, 'bullish': 75,
            'neutral': 50,
            'bearish': 25, 'very_bearish': 10
        }
    
    def calculate(self, news_item: Dict) -> Dict:
        """Calcula score y guarda TODO para backtesting"""
        
        event = self.event_classifier.classify(
            news_item.get('title', ''),
            news_item.get('content', '')
        )
        
        components = {
            'sentiment': self._sentiment_score(news_item),
            'relevance': self._relevance_score(news_item),
            'source_quality': self._source_score(news_item),
            'event_type': event['weight']
        }
        
        total_score = sum(
            components[k] * self.weights[k] 
            for k in components
        )
        
        sentiment_direction = self._get_sentiment_direction(news_item)
        sentiment_score = components['sentiment']
        
        if total_score >= 70 and sentiment_score > 60:
            signal = 'BULLISH'
            strength = 'STRONG'
        elif total_score >= 70 and sentiment_score < 40:
            signal = 'BEARISH'
            strength = 'STRONG'
        elif total_score >= 50:
            signal = 'NEUTRAL'
            strength = 'MODERATE'
        else:
            signal = 'NEUTRAL'
            strength = 'WEAK'
        
        explanation = self._explain(components, event, news_item)
        
        return {
            'version': self.VERSION,
            'score': round(total_score, 1),
            'signal': signal,
            'strength': strength,
            'components': components,
            'event_type': event['event_type'],
            'event_confidence': event['confidence'],
            'explanation': explanation,
            'timestamp': datetime.now().isoformat()
        }
    
    def _sentiment_score(self, news_item: Dict) -> float:
        sentiment = news_item.get('sentiment', 'neutral')
        return self.sentiment_map.get(sentiment, 50)
    
    def _relevance_score(self, news_item: Dict) -> float:
        content = news_item.get('content', '').lower()
        ticker = news_item.get('ticker', '').lower()
        
        score = 0
        if ticker and ticker in content:
            score += 30
        
        high_impact_words = ['earnings', 'revenue', 'profit', 'growth', 'decline']
        for word in high_impact_words:
            if word in content:
                score += 15
        
        return min(score, 100)
    
    def _source_score(self, news_item: Dict) -> float:
        source = news_item.get('source', 'default').lower()
        for known_source in self.source_scores:
            if known_source in source:
                return self.source_scores[known_source]
        return self.source_scores['default']
    
    def _get_sentiment_direction(self, news_item: Dict) -> str:
        return news_item.get('sentiment', 'neutral')
    
    def _explain(self, components: Dict, event: Dict, news_item: Dict) -> str:
        reasons = []
        
        if event['weight'] >= 80:
            reasons.append(f"• {event['event_type'].replace('_', ' ').title()} event detected")
        
        content = news_item.get('content', '').lower()
        
        if 'beat' in content and 'earnings' in content:
            reasons.append("• Earnings beat expectations")
        if 'revenue growth' in content or 'revenue up' in content:
            reasons.append("• Revenue growth detected")
        if 'guidance raised' in content or 'raised guidance' in content:
            reasons.append("• Guidance raised")
        
        if components['sentiment'] >= 80:
            reasons.append("• Strong positive sentiment")
        elif components['sentiment'] <= 20:
            reasons.append("• Strong negative sentiment")
        
        if not reasons:
            reasons.append("• Limited signals detected")
        
        total_score = sum(components[k] * self.weights[k] for k in components)
        
        if total_score >= 70:
            return f"**SIGNAL**\n\nKey factors:\n" + "\n".join(reasons[:4])
        elif total_score >= 45:
            return f"**WATCH**\n\nNotable factors:\n" + "\n".join(reasons[:3])
        else:
            return f"**LOW PRIORITY**\n\nLimited impact:\n" + "\n".join(reasons[:2])
