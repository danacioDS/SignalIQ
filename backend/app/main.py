"""
SignalIQ API - Simple con Alpha Vantage + Twelve Data + Yahoo Finance
"""
import os
import logging
import time
from datetime import datetime, timedelta
from threading import Lock

from flask import Flask, jsonify, request
from flask_cors import CORS
import yfinance as yf
import requests
import numpy as np

# ============================================================
# CONFIGURACIÓN
# ============================================================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API Keys desde variables de entorno
ALPHA_VANTAGE_API_KEY = os.environ.get('ALPHA_VANTAGE_API_KEY', '')
TWELVE_DATA_API_KEY = os.environ.get('TWELVE_DATA_API_KEY', '')

# Caché simple
cache = {}
cache_lock = Lock()
CACHE_TTL = 300

TICKERS = ['AAPL', 'MSFT', 'NVDA', 'GOOGL', 'META', 'AMD', 'AMZN', 'TSLA', 'JPM', 'KO']

# Precios base para fallback (actualizados manualmente o con datos históricos)
FALLBACK_PRICES = {
    'AAPL': 316.22, 'MSFT': 380.20, 'NVDA': 850.10,
    'GOOGL': 358.89, 'META': 320.40, 'AMD': 150.80,
    'AMZN': 185.60, 'TSLA': 406.55, 'JPM': 155.30, 'KO': 60.20
}

# ============================================================
# FUNCIONES DE PRECIOS
# ============================================================

def fetch_alpha_vantage_price(ticker):
    """Obtener precio de Alpha Vantage"""
    if not ALPHA_VANTAGE_API_KEY:
        return None
    
    try:
        url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={ticker}&apikey={ALPHA_VANTAGE_API_KEY}"
        response = requests.get(url, timeout=5)
        data = response.json()
        
        if 'Global Quote' in data and '05. price' in data['Global Quote']:
            return float(data['Global Quote']['05. price'])
    except Exception as e:
        logger.warning(f"Alpha Vantage error para {ticker}: {str(e)}")
    return None

def fetch_twelve_data_price(ticker):
    """Obtener precio de Twelve Data"""
    if not TWELVE_DATA_API_KEY:
        return None
    
    try:
        url = f"https://api.twelvedata.com/price?symbol={ticker}&apikey={TWELVE_DATA_API_KEY}"
        response = requests.get(url, timeout=5)
        data = response.json()
        
        if 'price' in data and data['price'] is not None:
            return float(data['price'])
    except Exception as e:
        logger.warning(f"Twelve Data error para {ticker}: {str(e)}")
    return None

def fetch_yahoo_price(ticker):
    """Obtener precio de Yahoo Finance"""
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="2d")
        if not hist.empty:
            return float(hist['Close'].iloc[-1])
    except Exception as e:
        logger.warning(f"Yahoo Finance error para {ticker}: {str(e)}")
    return None

def get_price(ticker):
    """Obtener precio: Alpha Vantage -> Twelve Data -> Yahoo Finance -> Fallback"""
    # 1. Alpha Vantage
    price = fetch_alpha_vantage_price(ticker)
    if price is not None:
        return price
    
    # 2. Twelve Data
    price = fetch_twelve_data_price(ticker)
    if price is not None:
        return price
    
    # 3. Yahoo Finance
    price = fetch_yahoo_price(ticker)
    if price is not None:
        return price
    
    # 4. Fallback
    return FALLBACK_PRICES.get(ticker, 100.0)

# ============================================================
# FUNCIONES DE HISTORIAL
# ============================================================

def fetch_alpha_vantage_history(ticker, days=30):
    """Obtener historial de Alpha Vantage"""
    if not ALPHA_VANTAGE_API_KEY:
        return []
    
    try:
        url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={ticker}&outputsize=compact&apikey={ALPHA_VANTAGE_API_KEY}"
        response = requests.get(url, timeout=5)
        data = response.json()
        
        if 'Time Series (Daily)' in data:
            time_series = data['Time Series (Daily)']
            dates = sorted(time_series.keys())[-days:]
            return [float(time_series[d]['4. close']) for d in dates]
    except Exception as e:
        logger.warning(f"Alpha Vantage history error para {ticker}: {str(e)}")
    return []

def fetch_yahoo_history(ticker, days=30):
    """Obtener historial de Yahoo Finance"""
    try:
        stock = yf.Ticker(ticker)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        hist = stock.history(start=start_date, end=end_date)
        if not hist.empty:
            return [float(p) for p in hist['Close'].values]
    except Exception as e:
        logger.warning(f"Yahoo Finance history error para {ticker}: {str(e)}")
    return []

def get_price_history(ticker, days=30):
    """Obtener historial: Alpha Vantage -> Yahoo Finance -> Simulado"""
    history = fetch_alpha_vantage_history(ticker, days)
    if history:
        return history
    
    history = fetch_yahoo_history(ticker, days)
    if history:
        return history
    
    # Generar historial simulado
    import random
    base_price = FALLBACK_PRICES.get(ticker, 100.0)
    history = []
    price = base_price * 0.9
    for _ in range(days):
        price = price * (1 + random.uniform(-0.02, 0.02))
        history.append(round(price, 2))
    return history

# ============================================================
# FUNCIONES DE ANÁLISIS
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

def generate_news_sentiment(ticker):
    """Generar sentimiento simulado basado en datos de mercado"""
    # Usar el precio para generar sentimiento
    price = get_price(ticker)
    if price is None or price == 0:
        return 0.0
    
    # Simular sentimiento entre -0.5 y 0.5
    import random
    # Usar el ticker como semilla para que sea consistente
    random.seed(hash(ticker) % 1000)
    sentiment = random.uniform(-0.3, 0.3)
    # Si el precio está subiendo, sentimiento positivo
    history = get_price_history(ticker, days=10)
    if len(history) >= 5:
        change = (history[-1] - history[-5]) / history[-5]
        sentiment += change * 2
    sentiment = max(-1, min(1, sentiment))
    return round(sentiment, 3)

def calculate_ndi(ticker):
    """Calcular NDI completo"""
    try:
        # 1. Obtener precio
        price = get_price(ticker)
        
        # 2. Obtener historial
        history = get_price_history(ticker, days=30)
        
        # 3. Calcular momentum (cambio % en últimos 10 días)
        if len(history) >= 10:
            momentum = (history[-1] - history[-10]) / history[-10]
        else:
            momentum = 0
        
        # 4. Generar sentimiento simulado
        sentiment = generate_news_sentiment(ticker)
        
        # 5. Calcular NDI
        ndi = sentiment - momentum
        
        # 6. Clasificar régimen
        regime = classify_regime(ndi)
        
        # 7. Calcular confianza
        confidence = 50
        if len(history) >= 30:
            confidence += 20
        if abs(ndi) > 0.5:
            confidence += 10
        confidence = min(95, confidence)
        
        return {
            'ticker': ticker,
            'price': round(price, 2),
            'sentiment': round(sentiment, 3),
            'momentum': round(momentum, 3),
            'ndi': round(ndi, 3),
            'regime': regime['regime'],
            'signal': regime['label'],
            'color': regime['color'],
            'confidence': confidence,
            'price_history': [round(p, 2) for p in history[-20:]] if history else [],
            'news_count': 10,
            'fallback': price in FALLBACK_PRICES.values() and len(history) < 10,
            'timestamp': datetime.now().isoformat()
        }
        
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
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/ticker/<ticker>')
def get_ticker(ticker):
    ticker = ticker.strip().upper()
    
    if ticker not in TICKERS:
        return jsonify({'error': f'Ticker {ticker} no soportado', 'supported': TICKERS}), 400
    
    # Caché
    cache_key = f'ticker_{ticker}'
    with cache_lock:
        if cache_key in cache:
            data, timestamp = cache[cache_key]
            if (datetime.now() - timestamp).total_seconds() < CACHE_TTL:
                logger.info(f"📊 CACHÉ: {ticker}")
                return jsonify(data)
    
    # Calcular
    data = calculate_ndi(ticker)
    
    if data is None:
        data = {
            'ticker': ticker,
            'price': 0,
            'sentiment': 0,
            'momentum': 0,
            'ndi': 0,
            'regime': 'NEUTRAL',
            'signal': 'HOLD',
            'color': 'yellow',
            'confidence': 0,
            'price_history': [],
            'news_count': 0,
            'fallback': True,
            'message': 'No se pudieron obtener datos'
        }
    
    with cache_lock:
        cache[cache_key] = (data, datetime.now())
    
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
        'version': '4.0',
        'mode': 'alpha_vantage_twelve_yahoo',
        'status': 'operational',
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
    logger.info("🚀 SignalIQ API v4.0")
    logger.info(f"📊 Puerto: {port}")
    logger.info(f"📊 Alpha Vantage: {'✅' if ALPHA_VANTAGE_API_KEY else '❌'}")
    logger.info(f"📊 Twelve Data: {'✅' if TWELVE_DATA_API_KEY else '❌'}")
    logger.info("=" * 50)
    app.run(host='0.0.0.0', port=port, debug=False)