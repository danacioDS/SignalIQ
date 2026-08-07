"""
SignalIQ API - Optimizado con Caché y Mínimo Consumo de APIs
from dotenv import load_dotenv
load_dotenv()
# ============================================================
# DEPURACIÓN: Verificar variables de entorno
# ============================================================
import os
# ============================================================
# CONFIGURACIÓN DE API KEYS (desde variables de entorno)
# ============================================================
import os
TWELVE_DATA_API_KEY = os.environ.get('TWELVE_DATA_API_KEY', '')
ALPHA_VANTAGE_API_KEY = os.environ.get('ALPHA_VANTAGE_API_KEY', '')

# ============================================================

logger.info(f"🔍 TWELVE_DATA_API_KEY: {'✅' if os.getenv('TWELVE_DATA_API_KEY') else '❌'}")
logger.info(f"🔍 ALPHA_VANTAGE_API_KEY: {'✅' if os.getenv('ALPHA_VANTAGE_API_KEY') else '❌'}")

# Si no están disponibles, mostrar los nombres de todas las variables
if not os.getenv('TWELVE_DATA_API_KEY'):
    logger.warning("⚠️ TWELVE_DATA_API_KEY no encontrada en variables de entorno")
    logger.warning(f"📋 Variables disponibles: {list(os.environ.keys())[:10]}")


# Claves directas para pruebas
"""
import os
# ============================================================
# CONFIGURACIÓN DE API KEYS (desde variables de entorno)
# ============================================================
import os
TWELVE_DATA_API_KEY = os.environ.get('TWELVE_DATA_API_KEY', '')
ALPHA_VANTAGE_API_KEY = os.environ.get('ALPHA_VANTAGE_API_KEY', '')

# ============================================================

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
    """Obtiene precio con prioridad: Twelve Data -> Alpha Vantage -> Yahoo -> Fallback."""
    cache_key = f'price_{ticker}'
    cached = get_cached(cache_key, 'price')
    if cached is not None:
        return cached
    
    # 1. Twelve Data (PRIORIDAD ABSOLUTA)
    try:
        url = f"https://api.twelvedata.com/price?symbol={ticker}&apikey={TWELVE_DATA_API_KEY}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if 'price' in data and data['price'] is not None:
                price = float(data['price'])
                set_cached(cache_key, price, 'price')
                logger.info(f"💰 Twelve Data: {ticker} = ${price:.2f}")
                return price
    except Exception as e:
        logger.warning(f"Twelve Data falló: {e}")
    
    # 2. Alpha Vantage
    if ALPHA_VANTAGE_API_KEY:
        try:
            url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={ticker}&apikey={ALPHA_VANTAGE_API_KEY}"
            response = requests.get(url, timeout=5)
            data = response.json()
            if 'Global Quote' in data and '05. price' in data['Global Quote']:
                price = float(data['Global Quote']['05. price'])
                set_cached(cache_key, price, 'price')
                logger.info(f"💰 Alpha Vantage: {ticker} = ${price:.2f}")
                return price
        except Exception as e:
            logger.warning(f"Alpha Vantage falló: {e}")
    
    # 3. Yahoo Finance (fallback)
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="2d")
        if not hist.empty:
            price = float(hist['Close'].iloc[-1])
            set_cached(cache_key, price, 'price')
            logger.info(f"💰 Yahoo Finance: {ticker} = ${price:.2f}")
            return price
    except Exception as e:
        logger.warning(f"Yahoo Finance falló: {e}")
    
    # 4. Fallback final
    logger.error(f"❌ No hay precio disponible para {ticker}")
    return FALLBACK_PRICES.get(ticker, 100.0)



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

def get_current_price(ticker):
    """Obtiene el precio actual para un ticker."""
    try:
        price = get_price(ticker)
        if price and isinstance(price, (int, float)):
            return float(price)
        return None
    except Exception as e:
        logger.warning(f"Error obteniendo precio para {ticker}: {str(e)}")
        return None
