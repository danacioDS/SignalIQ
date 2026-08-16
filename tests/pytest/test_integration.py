"""
Tests de integración para la API de SignalIQ
Requiere que la API esté corriendo en localhost:10000
"""

import pytest
import requests
import json
import time

BASE_URL = "http://localhost:10000"

class TestIntegration:
    """Tests de integración para API en local"""
    
    def test_health_check(self):
        """Verificar health check endpoint (corregido)"""
        response = requests.get(f"{BASE_URL}/health")
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'healthy'
        assert 'mode' in data
        assert data['mode'] == 'alpha_vantage_twelve_yahoo'
    
    def test_ticker_aapl(self):
        """Verificar ticker AAPL"""
        response = requests.get(f"{BASE_URL}/api/ticker/AAPL")
        assert response.status_code == 200
        data = response.json()
        assert data['ticker'] == 'AAPL'
        assert 'ndi' in data
        assert 'signal' in data
        assert 'price' in data
        assert 'confidence' in data
        # Verificar que la señal sea válida
        assert data['signal'] in ['BUY', 'SELL', 'HOLD', 'MONITOR']
    
    def test_ticker_googl(self):
        """Verificar ticker GOOGL"""
        response = requests.get(f"{BASE_URL}/api/ticker/GOOGL")
        assert response.status_code == 200
        data = response.json()
        assert data['ticker'] == 'GOOGL'
        assert 'ndi' in data
        assert 'regime' in data
    
    def test_ticker_with_news(self):
        """Verificar que trae noticias"""
        response = requests.get(f"{BASE_URL}/api/ticker/AAPL?news=true")
        assert response.status_code == 200
        data = response.json()
        assert 'news_count' in data
        assert data['news_count'] >= 0
        if data['news_count'] > 0:
            assert 'headlines' in data
            assert len(data['headlines']) > 0
    
    def test_signals_live(self):
        """Verificar señales en vivo"""
        response = requests.get(f"{BASE_URL}/api/signals-live")
        assert response.status_code == 200
        data = response.json()
        assert 'data' in data or 'success' in data
        # Manejar ambos formatos de respuesta
        signals = data.get('data', [])
        if not signals:
            # Si no hay data, verificar que hay mensaje
            assert 'message' in data or 'timestamp' in data
        else:
            first = signals[0]
            assert 'ticker' in first
            assert 'signal' in first
            assert 'ndi' in first
    
    def test_invalid_ticker(self):
        """Verificar manejo de ticker inválido"""
        response = requests.get(f"{BASE_URL}/api/ticker/INVALID123")
        # Debe devolver error (404 o 400)
        assert response.status_code in [400, 404, 500]
    
    def test_response_time(self):
        """Verificar tiempo de respuesta (< 2 segundos)"""
        start = time.time()
        response = requests.get(f"{BASE_URL}/api/ticker/AAPL")
        elapsed = time.time() - start
        assert elapsed < 2.0, f"Tiempo de respuesta muy lento: {elapsed:.2f}s"
        assert response.status_code == 200
    
    def test_no_secrets_in_response(self):
        """Verificar que no hay secretos en la respuesta"""
        response = requests.get(f"{BASE_URL}/api/ticker/AAPL")
        data = response.text.lower()
        # Verificar que no haya patrones de API keys
        assert 'key' not in data or 'api' not in data
        assert 'secret' not in data
        assert 'token' not in data
    
    def test_price_history_format(self):
        """Verificar formato del historial de precios"""
        response = requests.get(f"{BASE_URL}/api/ticker/AAPL")
        data = response.json()
        assert 'price_history' in data
        history = data['price_history']
        assert isinstance(history, list)
        if len(history) > 0:
            first = history[0]
            assert 'date' in first
            assert 'close' in first
            assert 'ndi' in first
    
    def test_cache_headers(self):
        """Verificar headers de caché"""
        response = requests.get(f"{BASE_URL}/api/ticker/AAPL")
        assert response.status_code == 200
        # Verificar que hay headers de caché o timestamp
        data = response.json()
        assert 'timestamp' in data
