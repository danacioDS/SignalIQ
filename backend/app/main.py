"""
SignalIQ API - Optimizado con Caché y Mínimo Consumo de APIs
"""
import os
import logging
import time
import random
from datetime import datetime, timedelta
from threading import Lock

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from flask import Flask, jsonify, request
from flask_cors import CORS
import yfinance as yf
import requests
import numpy as np
# ⭐ IMPORTAR EL PIPELINE DE NOTICIAS REALES
# Try relative import first (when imported as module)
try:
    from .news_pipeline import process_news_for_ticker
except ImportError:
    # Fallback to absolute import (when run as script)
    from news_pipeline import process_news_for_ticker

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# ============================================================
# CONFIGURACIÓN
# ============================================================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API Keys
ALPHA_VANTAGE_API_KEY = os.environ.get('ALPHA_VANTAGE_API_KEY', '')
TWELVE_DATA_API_KEY = os.environ.get('TWELVE_DATA_API_KEY', '')

# Caché optimizado
cache = {}
cache_lock = Lock()
CACHE_TTL = {
    'price': 300,
    'history': 600,
    'ticker': 300,
    'signals': 60,
}

TICKERS = ['AAPL', 'MSFT', 'NVDA', 'GOOGL', 'META', 'AMD', 'AMZN', 'TSLA', 'JPM', 'KO']

FALLBACK_PRICES = {
    'AAPL': 316.22, 'MSFT': 380.20, 'NVDA': 850.10,
    'GOOGL': 358.89, 'META': 320.40, 'AMD': 150.80,
    'AMZN': 185.60, 'TSLA': 406.55, 'JPM': 155.30, 'KO': 60.20
}

# ============================================================
# CACHÉ
# ============================================================

def get_cached(key, cache_type='ticker'):
    with cache_lock:
        if key in cache:
            data, timestamp = cache[key]
            ttl = CACHE_TTL.get(cache_type, 60)
            if (datetime.now() - timestamp).total_seconds() < ttl:
                logger.info(f"📊 CACHÉ: {key}")
                return data
    return None

def set_cached(key, value, cache_type='ticker'):
    with cache_lock:
        cache[key] = (value, datetime.now())

# ============================================================
# PRECIOS
# ============================================================

def get_price(ticker):
    cache_key = f'price_{ticker}'
    cached = get_cached(cache_key, 'price')
    if cached is not None:
        return cached, 'cache'  # Cache hit returns tuple
    
    # 1. Alpha Vantage
    if ALPHA_VANTAGE_API_KEY:
        try:
            url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={ticker}&apikey={ALPHA_VANTAGE_API_KEY}"
            response = requests.get(url, timeout=5)
            data = response.json()
            if 'Global Quote' in data and '05. price' in data['Global Quote']:
                price = float(data['Global Quote']['05. price'])
                set_cached(cache_key, price, 'price')
                return price, "alphavantage"
        except Exception as e:
                logger.warning(f"Alpha Vantage falló para {ticker}: {str(e)}", exc_info=True)
    
    # 2. Twelve Data
    if TWELVE_DATA_API_KEY:
        try:
            url = f"https://api.twelvedata.com/price?symbol={ticker}&apikey={TWELVE_DATA_API_KEY}"
            response = requests.get(url, timeout=5)
            data = response.json()
            if 'price' in data and data['price'] is not None:
                price = float(data['price'])
                set_cached(cache_key, price, 'price')
                return price, "alphavantage"
        except Exception as e:
                logger.warning(f"Alpha Vantage falló para {ticker}: {str(e)}", exc_info=True)
    
    # 3. Yahoo Finance
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="2d")
        if not hist.empty:
            price = float(hist['Close'].iloc[-1])
            set_cached(cache_key, price, 'price')
            return price, "alphavantage"
    except Exception as e:
            logger.warning(f"Alpha Vantage falló para {ticker}: {str(e)}", exc_info=True)
    
    # 4. Fallback
    price = FALLBACK_PRICES.get(ticker, 100.0)
    set_cached(cache_key, price, 'price')
    return price, "alphavantage"

def get_current_price(ticker):
    """Get current price using get_price, return float only."""
    try:
        price, _ = get_price(ticker)
        return price
    except Exception as e:
        logger.warning(f"Could not get current price for {ticker}: {str(e)}")
        return FALLBACK_PRICES.get(ticker, 100.0)


# ============================================================
# HISTORIAL
# ============================================================

def get_price_history(ticker, days=30):
    """
    Obtiene historial de precios con metadata de calidad.
    """
    result = {
        'history': [],
        'data_quality': 'REAL',
        'source': None,
        'simulated': False,
        'last_updated': None,
        'warning': None
    }
    
    # Intentar obtener datos reales
    try:
        ticker_obj = yf.Ticker(ticker)
        hist = ticker_obj.history(period=f'{days}d')
        
        if not hist.empty:
            result['history'] = [
                {'date': idx.strftime('%Y-%m-%d'), 'close': float(row['Close'])}
                for idx, row in hist.iterrows()
            ]
            result['source'] = 'yahoo'
            result['last_updated'] = datetime.now().isoformat()
            logger.info(f"Historial real obtenido para {ticker} ({len(result['history'])} días)")
            return result
    except Exception as e:
        logger.warning(f"No se pudo obtener historial real para {ticker}: {str(e)}")
    
    # Generar datos simulados (con etiqueta)
    current_price = get_current_price(ticker)
    if current_price is None:
        current_price = FALLBACK_PRICES.get(ticker, 100.0)
    
    # Simulación conservadora
    result['history'] = []
    for i in range(days):
        price = current_price * (1 + 0.001 * (i - days/2))
        result['history'].append({
            'date': (datetime.now() - timedelta(days=days-i)).strftime('%Y-%m-%d'),
            'close': round(price, 2)
        })
    
    result['data_quality'] = 'SIMULATED'
    result['source'] = 'fallback'
    result['simulated'] = True
    result['warning'] = '⚠️ Historical prices are simulated - use with caution'
    result['last_updated'] = datetime.now().isoformat()
    
    logger.warning(f"Usando datos simulados para {ticker}")
    return result

def get_ticker_data(ticker):
    """
    Get comprehensive ticker data for API endpoints.
    """
    try:
        # Get price
        price, source = get_price(ticker)
        
        # Get price history
        history_data = get_price_history(ticker, days=30)
        
        # Get news sentiment
        news_data = process_news_for_ticker(ticker)
        
        # Calculate NDI
        ndi = calculate_ndi(ticker, news_data, history_data)
        
        return {
            'ticker': ticker,
            'current_price': price,
            'price_source': source,
            'price_history': history_data.get('history', []),
            'data_quality': history_data.get('data_quality', 'UNKNOWN'),
            'sentiment': news_data.get('sentiment', 0.0),
            'news_count': news_data.get('count', 0),
            'headlines': news_data.get('headlines', []),
            'ndi': ndi,
            'regime': classify_regime(ndi),
            'confidence': calculate_confidence(ndi)
        }
    except Exception as e:
        logger.error(f"Error getting ticker data for {ticker}: {str(e)}", exc_info=True)
        return None


def classify_regime(ndi):
    if ndi > 2.0:
        return {'regime': 'EXTREME OVERHEATING', 'color': 'red', 'label': 'SELL'}
    elif ndi > 1.5:
        return {'regime': 'OVERHEATING', 'color': 'orange', 'label': 'REDUCE'}
    elif ndi > 0.5:
        return {'regime': 'WATCHING', 'color': 'orange', 'label': 'MONITOR'}
    elif ndi > -0.5:
        return {'regime': 'NEUTRAL', 'color': 'yellow', 'label': 'HOLD'}
    elif ndi > -1.5:
        return {'regime': 'ALIGNED', 'color': 'green', 'label': 'BUY'}
    elif ndi > -2.0:
        return {'regime': 'STRONG UNDERVALUED', 'color': 'green', 'label': 'STRONG BUY'}
    else:
        return {'regime': 'CAPITULATION', 'color': 'blue', 'label': 'ACCUMULATE'}

# ============================================================
# Calcular NDI y Regímenes
# ============================================================

def calculate_ndi(ticker, news_data=None, history_data=None):
    """
    Calculate NDI for a ticker using sentiment and momentum.
    """
    try:
        # Get news sentiment
        if news_data is None:
            news_data = process_news_for_ticker(ticker)
        
        # Get price history
        if history_data is None:
            history_data = get_price_history(ticker, days=30)
        
        # Extract history list from dict
        history = history_data.get('history', []) if isinstance(history_data, dict) else history_data
        
        if not history or len(history) < 10:
            logger.warning(f"Not enough history for {ticker}: {len(history) if history else 0}")
            return 0.0
        
        # Calculate momentum (10-day return)
        current_price = history[-1]['close'] if isinstance(history[-1], dict) else history[-1]
        price_10d_ago = history[-10]['close'] if isinstance(history[-10], dict) else history[-10]
        
        if price_10d_ago == 0:
            return 0.0
        
        momentum = (current_price - price_10d_ago) / price_10d_ago
        
        # Get sentiment
        sentiment = news_data.get('sentiment', 0.0) if isinstance(news_data, dict) else 0.0
        
        # Calculate NDI with scaling
        ndi_raw = sentiment - momentum
        ndi_scaled = ndi_raw * 3.0
        ndi_clamped = max(-3.0, min(3.0, ndi_scaled))
        
        logger.info(f"NDI for {ticker}: sentiment={sentiment:.3f}, momentum={momentum:.3f}, ndi={ndi_clamped:.3f}")
        return ndi_clamped
        
    except Exception as e:
        logger.error(f"Error calculando NDI para {ticker}: {str(e)}", exc_info=True)
        return 0.0


def require_api_key(f):
    """Decorator to optionally require API key."""
    from functools import wraps
    
    @wraps(f)
    def decorated(*args, **kwargs):
        # Si no hay API_KEY configurada, permitir todo
        if not API_KEY:
            return f(*args, **kwargs)
        
        # Verificar API key en header
        api_key = request.headers.get('X-API-Key')
        if api_key != API_KEY:
            return jsonify({'error': 'Invalid or missing API key'}), 401
        return f(*args, **kwargs)
    return decorated

# Aplicar a endpoints (opcional - descomentar para activar)
# @app.route('/api/ticker/<ticker>')
# @require_api_key
# @limiter.limit("10 per minute")

@app.route('/api/prices', methods=['GET'])
def get_all_prices():
    """Return current prices for all tracked tickers."""
    tickers = ['NVDA', 'AAPL', 'MSFT', 'TSLA', 'GOOGL', 'META', 'AMD', 'AMZN', 'JPM', 'KO']
    result = {}
    
    for ticker in tickers:
        try:
            price, source = get_price(ticker)
            if price:
                result[ticker] = {
                    'price': float(price),
                    'source': source,
                    'timestamp': datetime.now().isoformat()
                }
        except Exception as e:
            logger.warning(f"Error getting price for {ticker}: {str(e)}")
            result[ticker] = {'error': str(e)}
    
    return jsonify(result)

@app.route('/api/signals-intel', methods=['GET'])
def get_signals_intel():
    """Return comprehensive signals for frontend."""
    ticker = request.args.get('ticker')
    
    if ticker:
        data = get_ticker_data(ticker)
        if data:
            return jsonify(data)
        return jsonify({'error': f'Ticker {ticker} not found'}), 404
    
    tickers = ['NVDA', 'AAPL', 'MSFT', 'TSLA', 'GOOGL', 'META', 'AMD', 'AMZN', 'JPM', 'KO']
    results = {}
    for t in tickers:
        try:
            data = get_ticker_data(t)
            if data:
                results[t] = data
        except Exception as e:
            logger.warning(f"Error getting signals for {t}: {str(e)}")
            results[t] = {'error': str(e)}
    
    return jsonify(results)
