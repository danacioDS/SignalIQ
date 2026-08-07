"""
SignalIQ API - Optimizado con Caché y Mínimo Consumo de APIs
"""
import os
import logging
import time
import random
from datetime import datetime, timedelta
from threading import Lock

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
        return cached
    
    # 1. Alpha Vantage
    if ALPHA_VANTAGE_API_KEY:
        try:
            url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={ticker}&apikey={ALPHA_VANTAGE_API_KEY}"
            response = requests.get(url, timeout=5)
            data = response.json()
            if 'Global Quote' in data and '05. price' in data['Global Quote']:
                price = float(data['Global Quote']['05. price'])
                set_cached(cache_key, price, 'price')
                return price
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
                return price
        except Exception as e:
                logger.warning(f"Alpha Vantage falló para {ticker}: {str(e)}", exc_info=True)
    
    # 3. Yahoo Finance
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="2d")
        if not hist.empty:
            price = float(hist['Close'].iloc[-1])
            set_cached(cache_key, price, 'price')
            return price
    except Exception as e:
            logger.warning(f"Alpha Vantage falló para {ticker}: {str(e)}", exc_info=True)
    
    # 4. Fallback
    price = FALLBACK_PRICES.get(ticker, 100.0)
    set_cached(cache_key, price, 'price')
    return price

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
    cache_key = f'ticker_{ticker}'
    cached = get_cached(cache_key, 'ticker')
    if cached is not None:
        return cached
    
    try:
        price = get_price(ticker)
        history = get_price_history(ticker, days=30)
        
        # ⭐ NOTICIAS REALES DEL PIPELINE
        news_data = process_news_for_ticker(ticker)
        sentiment = news_data.get('sentiment', 0.0)
        headlines = news_data.get('headlines', [])
        news_count = news_data.get('count', 0)
        
        # Si no hay noticias, usar sentimiento simulado como fallback
        if news_count == 0:
            logger.info(f"📊 Sin noticias para {ticker}, usando sentimiento simulado")
            if len(history) >= 5:
                change_5d = (history[-1] - history[-5]) / history[-5]
                returns = []
                recent = history[-10:] if len(history) >= 10 else history
                for i in range(1, len(recent)):
                    if recent[i-1] != 0:
                        returns.append((recent[i] - recent[i-1]) / recent[i-1])
                volatility = np.std(returns) if len(returns) > 1 else 0.01
                sentiment = change_5d * 8 + volatility * 3  # ⭐ Más peso al cambio de precio
                sentiment = max(-1, min(1, sentiment))
            else:
                sentiment = 0.0
        
        # Momentum
        if len(history) >= 10:
            momentum = (history[-1] - history[-10]) / history[-10]
        else:
            momentum = 0
        
        # NDI = Sentiment - Momentum
        ## ndi = sentiment - momentum
        # DESPUÉS (con factor de escala)
        ndi = (sentiment - momentum) * 3  # ⭐ Factor de escala para más sensibilidad
        regime = classify_regime(ndi)
        
        # Confianza (aumenta si hay noticias reales)
        confidence = 50
        if len(history) >= 30:
            confidence += 20
        if abs(ndi) > 0.5:
            confidence += 15
        if abs(ndi) > 1.0:
            confidence += 10
        if news_count > 0:
            confidence += 10
        confidence = min(95, confidence)
        
        # ⭐ PRICE_HISTORY - SIEMPRE CON 20 PUNTOS
        price_history_formatted = []
        history_data = history[-20:] if history else []
        
        # Si history está vacío, generar datos simulados
        if not history_data:
            logger.warning(f"⚠️ Historial vacío para {ticker}, generando datos simulados")
            base_price = price if price and price > 0 else FALLBACK_PRICES.get(ticker, 100.0)
            for i in range(20):
                variation = 1 + (i - 10) * 0.005 + random.uniform(-0.02, 0.02)
                simulated_price = base_price * variation
                history_data.append(round(simulated_price, 2))
        
        for i, p in enumerate(history_data):
            date = (datetime.now() - timedelta(days=len(history_data) - i)).strftime('%Y-%m-%d')
            price_history_formatted.append({
                'date': date,
                'close': round(p, 2),
                'ndi': round(ndi, 3)
            })
        
        result = {
            'ticker': ticker,
            'price': round(price, 2),
            'current_price': round(price, 2),
            'sentiment': round(sentiment, 3),
            'momentum': round(momentum, 3),
            'ndi': round(ndi, 3),
            'regime': regime['regime'],
            'signal': regime['label'],
            'color': regime['color'],
            'confidence': confidence,
            'price_history': price_history_formatted,  # ⭐ SIEMPRE CON DATOS
            'news_count': news_count,
            'headlines': headlines[:5] if headlines else [],
            'timestamp': datetime.now().isoformat()
        }
        
        set_cached(cache_key, result, 'ticker')
        return result
        
    except Exception as e:
        logger.error(f"Error calculando {ticker}: {str(e)}")
        # ⭐ EN CASO DE ERROR, DEVOLVER DATOS MÍNIMOS
        return {
            'ticker': ticker,
            'price': FALLBACK_PRICES.get(ticker, 100.0),
            'current_price': FALLBACK_PRICES.get(ticker, 100.0),
            'sentiment': 0.0,
            'momentum': 0.0,
            'ndi': 0.0,
            'regime': 'NEUTRAL',
            'signal': 'HOLD',
            'color': 'yellow',
            'confidence': 50,
            'price_history': [
                {'date': (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d'), 
                 'close': FALLBACK_PRICES.get(ticker, 100.0) * (1 + (i - 10) * 0.005),
                 'ndi': 0.0}
                for i in range(20)
            ],
            'news_count': 0,
            'headlines': [],
            'timestamp': datetime.now().isoformat()
        }

# ============================================================
# APLICACIÓN FLASK
# ============================================================

app = Flask(__name__)

# ⭐ CONFIGURAR CORS CORRECTAMENTE
CORS(app, origins=[
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://signaliq-zeta-ten.vercel.app",
    "https://signaliq-zeta.vercel.app",
    "https://signaliq-api.onrender.com",
    "https://signaliq-api.onrender.com"
])

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'mode': 'alpha_vantage_twelve_yahoo',
        'cache_ttl': CACHE_TTL,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/ticker/<ticker>')
def get_ticker(ticker):
    ticker = ticker.strip().upper()
    if ticker not in TICKERS:
        return jsonify({'error': f'Ticker {ticker} no soportado', 'supported': TICKERS}), 400
    
    data = calculate_ndi(ticker)
    return jsonify(data)

@app.route('/api/signals-live')
def signals_live():
    tickers_param = request.args.get('tickers', '')
    if tickers_param:
        ticker_list = [t.strip().upper() for t in tickers_param.split(',') if t.strip()]
    else:
        ticker_list = TICKERS
    
    results = []
    for ticker in ticker_list:
        if ticker in TICKERS:
            data = calculate_ndi(ticker)
            if data:
                results.append(data)
    
    return jsonify({
        'success': True,
        'signals': results,
        'count': len(results),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/tickers')
def get_tickers():
    return jsonify({'tickers': TICKERS, 'count': len(TICKERS)})

@app.route('/')
def root():
    return jsonify({
        'name': 'SignalIQ API',
        'version': '6.2',
        'mode': 'alpha_vantage_twelve_yahoo',
        'status': 'operational',
        'cache_ttl': CACHE_TTL,
        'endpoints': {
            'health': '/health',
            'ticker': '/api/ticker/TSLA',
            'signals': '/api/signals-live',
            'tickers': '/api/tickers'
        }
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    logger.info("=" * 50)
    logger.info("🚀 SignalIQ API v6.1 - Con price_history SIEMPRE")
    logger.info(f"📊 Puerto: {port}")
    logger.info(f"📊 Cache TTL: {CACHE_TTL}")
    logger.info(f"📊 Alpha Vantage: {'✅' if ALPHA_VANTAGE_API_KEY else '❌'}")
    logger.info(f"📊 Twelve Data: {'✅' if TWELVE_DATA_API_KEY else '❌'}")
    logger.info("=" * 50)
    app.run(host='0.0.0.0', port=port, debug=False)
@app.route('/api/prices', methods=['GET'])
def get_all_prices():
    """
    Return current prices for all tracked tickers.
    Used by frontend yahoo-finance-service.ts
    """
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
            else:
                result[ticker] = {
                    'price': None,
                    'source': 'none',
                    'error': 'No price available'
                }
        except Exception as e:
            logger.warning(f"Error getting price for {ticker}: {str(e)}")
            result[ticker] = {
                'price': None,
                'source': 'error',
                'error': str(e)
            }
    
    return jsonify(result)

@app.route('/api/signals-intel', methods=['GET'])
def get_signals_intel():
    """
    Return comprehensive signals for frontend.
    Used by ExpandedRow.tsx
    """
    ticker = request.args.get('ticker')
    
    if ticker:
        # Single ticker
        data = get_ticker_data(ticker)
        if data:
            return jsonify(data)
        return jsonify({'error': f'Ticker {ticker} not found'}), 404
    
    # All tickers
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
