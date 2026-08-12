"""NDI Service simplificado — usa funciones de Layer 3."""

from typing import Dict, Any, List
from datetime import datetime, date, timedelta
from pathlib import Path

from app.layers.layer3_sentiment import polarity
from app.layers.layer4_orchestrator import process_asset
from app.layers.layer4_persistence import PersistenceTracker


class NDIServiceSimple:
    """
    Versión simplificada que usa funciones de Layer 3.
    """

    def __init__(self, state_file: str = "persistence_state.json"):
        self.tracker = PersistenceTracker(Path(state_file))

    def calculate(self, ticker: str, prices: List[float], headlines: List[str]) -> Dict[str, Any]:
        """
        Calcula NDI usando funciones de Layer 3 y Layer 4.
        """
        try:
            # 1. Calcular sentimiento con función polarity
            if headlines:
                sentiment_scores = [polarity(h) for h in headlines[:20]]
                sentiment_raw = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0.0
            else:
                sentiment_raw = 0.0

            # 2. Calcular momentum simple
            if len(prices) >= 2:
                momentum_raw = (prices[-1] - prices[-2]) / prices[-2] if prices[-2] != 0 else 0.0
            else:
                momentum_raw = 0.0

            # 3. Calcular z-scores simulados (usando valores normalizados)
            # En una implementación real, usaríamos Layer 3 completo
            sentiment_z = sentiment_raw * 2.0
            momentum_z = momentum_raw * 5.0

            # 4. Procesar con Layer 4
            date_str = datetime.now().isoformat()
            result = process_asset(
                ticker=ticker,
                sentiment_zscore=sentiment_z,
                momentum_zscore=momentum_z,
                price_history=prices,
                tracker=self.tracker,
                date_string=date_str
            )

            return {
                'ticker': ticker,
                'ndi': result.get('ndi', 0.0),
                'ndi_delta': result.get('ndi_delta', 0.0),
                'ndi_trend': result.get('ndi_trend', 'INSUFFICIENT_DATA'),
                'regime': result.get('regime', 'INSUFFICIENT_DATA'),
                'signal_state': result.get('signal_state', 'INACTIVE'),
                'confidence': result.get('confidence', 'INSUFFICIENT_DATA'),
                'streak': self.tracker.get_streak(ticker),
                'risk_level': result.get('risk_level', 'NORMAL'),
                'attention': result.get('attention', ''),
                'sentiment_zscore': sentiment_z,
                'momentum_zscore': momentum_z,
                'source': 'layers_simple',
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            return self._fallback(ticker, str(e))

    def _fallback(self, ticker: str, reason: str) -> Dict[str, Any]:
        return {
            'ticker': ticker,
            'ndi': 0.0,
            'ndi_delta': 0.0,
            'ndi_trend': 'INSUFFICIENT_DATA',
            'regime': 'INSUFFICIENT_DATA',
            'signal_state': 'INACTIVE',
            'confidence': 'INSUFFICIENT_DATA',
            'streak': 0,
            'risk_level': 'NORMAL',
            'attention': f'Error: {reason}',
            'sentiment_zscore': 0.0,
            'momentum_zscore': 0.0,
            'source': 'fallback',
            'timestamp': datetime.now().isoformat()
        }


# Instancia global
ndi_service = NDIServiceSimple()
