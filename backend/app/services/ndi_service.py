"""NDI Service — conector entre main.py y Layer 4."""

from typing import Dict, Any, List, Optional
from datetime import datetime, date, timedelta
from pathlib import Path

from app.layers.layer3_orchestrator import Layer3Orchestrator
from app.layers.layer4_orchestrator import process_asset
from app.layers.layer4_persistence import PersistenceTracker
from app.layers.layer3_config import CONFIG


class NDIService:
    """
    Servicio que conecta main.py con el pipeline de Layers.
    """

    def __init__(self, state_file: str = "persistence_state.json"):
        self.layer3 = Layer3Orchestrator(CONFIG)
        self.tracker = PersistenceTracker(Path(state_file))
        self._cache = {}

    def calculate(self, ticker: str, prices: List[float], headlines: List[str]) -> Dict[str, Any]:
        """
        Calcula NDI usando Layer 3 (z-scores) y Layer 4.

        Returns:
            Dict con ndi, ndi_delta, ndi_trend, regime, signal_state,
            confidence, streak, risk_level, attention.
        """
        try:
            # 1. Procesar precios en Layer 3
            base_date = datetime.now().date() - timedelta(days=len(prices) - 1)
            for i, price in enumerate(prices):
                dt = base_date + timedelta(days=i)
                self.layer3.process_price(ticker, dt, float(price))

            # 2. Procesar noticias en Layer 3
            now = datetime.now()
            for headline in headlines[:20]:
                self.layer3.process_headline(
                    headline_text=headline,
                    published_at=now,
                    ingested_at=now,
                    url_param=ticker
                )

            # 3. Finalizar día en Layer 3
            today = datetime.now().date()
            layer3_result = self.layer3.finalize_day(today, tickers=[ticker])

            if ticker not in layer3_result:
                return self._fallback(ticker, "No Layer 3 data")

            # 4. Extraer z-scores del último día
            ticker_data = layer3_result[ticker]
            latest_date = max(ticker_data.keys())
            daily_data = ticker_data[latest_date]

            sentiment_z = daily_data.get('sentiment_zscore', 0.0)
            momentum_z = daily_data.get('momentum_zscore', 0.0)

            # 5. Procesar con Layer 4
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
                'source': 'layers',
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
ndi_service = NDIService()
