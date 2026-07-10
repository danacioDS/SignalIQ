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
        except:
            pass
    
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
        except:
            pass
    
    # 3. Yahoo Finance
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="2d")
        if not hist.empty:
            price = float(hist['Close'].iloc[-1])
            set_cached(cache_key, price, 'price')
            return price
    except:
        pass
    
    # 4. Fallback
    price = FALLBACK_PRICES.get(ticker, 100.0)
    set_cached(cache_key, price, 'price')
    return price

# ============================================================
# HISTORIAL
# ============================================================

def get_price_history(ticker, days=30):
    cache_key = f'history_{ticker}_{days}'
    cached = get_cached(cache_key, 'history')
    if cached is not None:
        return cached
    
    history = []
    
    # 1. Alpha Vantage
    if ALPHA_VANTAGE_API_KEY:
        try:
            url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={ticker}&outputsize=compact&apikey={ALPHA_VANTAGE_API_KEY}"
            response = requests.get(url, timeout=5)
            data = response.json()
            if 'Time Series (Daily)' in data:
                time_series = data['Time Series (Daily)']
                dates = sorted(time_series.keys())[-days:]
                history = [float(time_series[d]['4. close']) for d in dates]
                if history:
                    set_cached(cache_key, history, 'history')
                    return history
        except:
            pass
    
    # 2. Yahoo Finance
    try:
        stock = yf.Ticker(ticker)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        hist = stock.history(start=start_date, end=end_date)
        if not hist.empty:
            history = [float(p) for p in hist['Close'].values]
            set_cached(cache_key, history, 'history')
            return history
    except:
        pass
    
    # 3. Historial simulado (más realista)
    base_price = FALLBACK_PRICES.get(ticker, 100.0)
    price = base_price * 0.9
    # Tendencias diferentes por ticker para más variedad
    trend = random.uniform(-0.005, 0.005)
    for i in range(days):
        # Añadir tendencia y ruido
        price = price * (1 + trend + random.uniform(-0.03, 0.03))
        history.append(round(price, 2))
    
    set_cached(cache_key, history, 'history')
    return history

# ============================================================
# ANÁLISIS NDI - VERSIÓN MEJORADA
# ============================================================

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
        headlines = news_data.get('headlines', [])  # ⭐ Agregar esta línea
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
                sentiment = change_5d * 5 + volatility * 2
                sentiment = max(-1, min(1, sentiment))
            else:
                sentiment = 0.0
        
        # Momentum
        if len(history) >= 10:
            momentum = (history[-1] - history[-10]) / history[-10]
        else:
            momentum = 0
        
        # NDI = Sentiment - Momentum
        ndi = sentiment - momentum
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
            confidence += 10  # ⭐ Bonus por noticias reales
        confidence = min(95, confidence)
        
        # ⭐ FORMATO CORRECTO PARA EL FRONTEND (con ndi para el gráfico)
        price_history_formatted = []
        history_data = history[-20:] if history else []
        for i, p in enumerate(history_data):
            date = (datetime.now() - timedelta(days=len(history_data) - i)).strftime('%Y-%m-%d')
            price_history_formatted.append({
                'date': date,
                'close': round(p, 2),
                'ndi': round(ndi, 3)  # ⭐ Para el gráfico
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
            'price_history': price_history_formatted,
            'news_count': news_count,
            'headlines': headlines[:5] if headlines else [],  # ⭐ Agregar esta línea
            'timestamp': datetime.now().isoformat()
        }
        
        set_cached(cache_key, result, 'ticker')
        return result
        
    except Exception as e:
        logger.error(f"Error calculando {ticker}: {str(e)}")
        return None

# ============================================================
# APLICACIÓN FLASK
# ============================================================

app = Flask(__name__)
CORS(app)

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
    if data is None:
        data = {
            'ticker': ticker,
            'price': 0,
            'current_price': 0,
            'sentiment': 0,
            'momentum': 0,
            'ndi': 0,
            'regime': 'NEUTRAL',
            'signal': 'HOLD',
            'color': 'yellow',
            'confidence': 0,
            'price_history': [],
            'fallback': True,
            'message': 'No se pudieron obtener datos'
        }
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
        'version': '6.0',
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
    logger.info("🚀 SignalIQ API v6.0 - NDI más sensible")
    logger.info(f"📊 Puerto: {port}")
    logger.info(f"📊 Cache TTL: {CACHE_TTL}")
    logger.info(f"📊 Alpha Vantage: {'✅' if ALPHA_VANTAGE_API_KEY else '❌'}")
    logger.info(f"📊 Twelve Data: {'✅' if TWELVE_DATA_API_KEY else '❌'}")
    logger.info("=" * 50)
    app.run(host='0.0.0.0', port=port, debug=False)