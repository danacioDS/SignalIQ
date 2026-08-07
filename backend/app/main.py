"""
SignalIQ API - Optimizado con Caché y Mínimo Consumo de APIs
"""
import os
import logging
import time
import random
from datetime import datetime, timedelta
from threading import Lock

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

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
        return cached, 'cache'
    
    # 1. Twelve Data (requiere API key - PRIORIDAD)
    if TWELVE_DATA_API_KEY:
        try:
            url = f"https://api.twelvedata.com/price?symbol={ticker}&apikey={TWELVE_DATA_API_KEY}"
            response = requests.get(url, timeout=5)
            data = response.json()
            if 'price' in data and data['price'] is not None:
                price = float(data['price'])
                set_cached(cache_key, price, 'price')
                logger.info(f"💰 Precio de Twelve Data: {ticker} = ${price:.2f}")
                return price, 'twelvedata'
        except Exception as e:
            logger.warning(f"Twelve Data falló para {ticker}: {str(e)}")
    
    # 2. Alpha Vantage (requiere API key)
    if ALPHA_VANTAGE_API_KEY:
        try:
            url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={ticker}&apikey={ALPHA_VANTAGE_API_KEY}"
            response = requests.get(url, timeout=5)
            data = response.json()
            if 'Global Quote' in data and '05. price' in data['Global Quote']:
                price = float(data['Global Quote']['05. price'])
                set_cached(cache_key, price, 'price')
                logger.info(f"💰 Precio de Alpha Vantage: {ticker} = ${price:.2f}")
                return price, 'alphavantage'
        except Exception as e:
            logger.warning(f"Alpha Vantage falló para {ticker}: {str(e)}")
    
    # 3. Yahoo Finance (fallback, no requiere API key)
    try:
        ticker_obj = yf.Ticker(ticker)
        hist = ticker_obj.history(period="1d")
        if not hist.empty:
            price = float(hist['Close'].iloc[-1])
            set_cached(cache_key, price, 'price')
            logger.info(f"💰 Precio de Yahoo Finance: {ticker} = ${price:.2f}")
            return price, 'yahoo'
    except Exception as e:
        logger.warning(f"Yahoo Finance falló para {ticker}: {str(e)}")
    
    # 4. Sin datos disponibles - NO SIMULAR
    logger.error(f"❌ No se pudo obtener precio para {ticker} de NINGUNA fuente")
    return None, 'unavailable'


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


def calculate_ndi(ticker):
    """
    Calcula NDI usando Twelve Data o Alpha Vantage.
    """
    try:
        # Obtener precio actual
        price = get_current_price(ticker)
        if not price:
            logger.warning(f"No hay precio disponible para {ticker}")
            return 0.0
        
        # Obtener historial
        history_data = get_price_history(ticker, days=30)
        
        # Extraer lista de precios
        if isinstance(history_data, dict):
            history = history_data.get('history', [])
        else:
            history = history_data if isinstance(history_data, list) else []
        
        if not history or len(history) < 10:
            logger.warning(f"Historial insuficiente para {ticker}")
            return 0.0
        
        # Calcular momentum
        try:
            close_prices = []
            for h in history:
                if isinstance(h, dict) and 'close' in h:
                    close_prices.append(float(h['close']))
                elif isinstance(h, (int, float)):
                    close_prices.append(float(h))
            
            if len(close_prices) < 10:
                return 0.0
            
            current_price = close_prices[-1]
            price_10d_ago = close_prices[-10]
            
            if price_10d_ago == 0:
                return 0.0
            
            momentum = (current_price - price_10d_ago) / price_10d_ago
        except Exception as e:
            logger.warning(f"Error calculando momentum: {str(e)}")
            momentum = 0.0
        
        # Obtener sentimiento de noticias
        try:
            news_data = process_news_for_ticker(ticker)
            sentiment = news_data.get('sentiment', 0.0)
            news_count = news_data.get('count', 0)
            
            if news_count == 0:
                sentiment = max(-1, min(1, momentum * 8))
                logger.info(f"📊 Sin noticias, sentimiento simulado: {sentiment:.3f}")
        except Exception as e:
            logger.warning(f"Error obteniendo sentimiento: {str(e)}")
            sentiment = 0.0
        
        # Calcular NDI
        ndi_raw = sentiment - momentum
        ndi_scaled = ndi_raw * 3.0
        ndi = max(-3.0, min(3.0, ndi_scaled))
        
        logger.info(f"📊 NDI {ticker}: sentiment={sentiment:.3f}, momentum={momentum:.3f}, ndi={ndi:.3f}")
        return ndi
        
    except Exception as e:
        logger.error(f"Error calculando NDI para {ticker}: {str(e)}", exc_info=True)
        return 0.0



def get_current_price(ticker):
    """
    Obtiene el precio actual para un ticker.
    Retorna float o None si no está disponible.
    """
    try:
        # Primero intentar con Twelve Data o Alpha Vantage
        price, _ = get_price(ticker)
        if price:
            return float(price)
    except Exception as e:
        logger.warning(f"Error obteniendo precio actual para {ticker}: {str(e)}")
    
    # Si todo falla, retornar None (no fallback simulado)
    logger.warning(f"No se pudo obtener precio actual para {ticker}")
    return None

def get_current_price(ticker):
    """
    Obtiene el precio actual para un ticker usando get_price.
    Retorna float o None si no está disponible.
    """
    try:
        price = get_price(ticker)
        if price and isinstance(price, (int, float)):
            return float(price)
        return None
    except Exception as e:
        logger.warning(f"Error obteniendo precio actual para {ticker}: {str(e)}")
        return None
