"""
SignalIQ API - Versión Simplificada (Funcional)
Solo Yahoo Finance - Rápido - Sin sobreingeniería
"""
import os
import logging
import json
import time
from datetime import datetime, timedelta
from threading import Lock

from flask import Flask, jsonify, request
from flask_cors import CORS
import yfinance as yf
import numpy as np

# ============================================================
# CONFIGURACIÓN
# ============================================================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Caché simple
cache = {}
cache_lock = Lock()
CACHE_TTL = 60

# Tickers soportados
TICKERS = ['AAPL', 'MSFT', 'NVDA', 'GOOGL', 'META', 'AMD', 'AMZN', 'TSLA', 'JPM', 'KO']

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

def calculate_ndi(ticker):
    """Calcular NDI real usando Yahoo Finance"""
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1mo")
        
        if hist.empty:
            return None
        
        # Precios
        prices = [float(p) for p in hist['Close'].values]
        volumes = [float(v) for v in hist['Volume'].values] if not hist['Volume'].empty else []
        
        current_price = prices[-1]
        
        # Momentum: cambio % en últimos 10 días
        if len(prices) >= 10:
            momentum = (prices[-1] - prices[-10]) / prices[-10]
        else:
            momentum = 0
        
        # Sentimiento: basado en precio + volumen
        if len(prices) >= 5 and len(volumes) >= 5:
            price_change = (prices[-1] - prices[-5]) / prices[-5]
            avg_volume = np.mean(volumes[-10:]) if len(volumes) >= 10 else np.mean(volumes)
            volume_ratio = volumes[-1] / avg_volume if avg_volume > 0 else 1
            sentiment = price_change * 5 + (volume_ratio - 1) * 0.3
            sentiment = max(-1, min(1, sentiment))
        else:
            sentiment = 0
        
        ndi = sentiment - momentum
        
        regime = classify_regime(ndi)
        
        return {
            'ticker': ticker,
            'price': round(current_price, 2),
            'sentiment': round(sentiment, 3),
            'momentum': round(momentum, 3),
            'ndi': round(ndi, 3),
            'regime': regime['regime'],
            'signal': regime['label'],
            'color': regime['color'],
            'price_history': [round(p, 2) for p in prices[-20:]],
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error calculando {ticker}: {str(e)}")
        return None

# ============================================================
# CREAR APLICACIÓN FLASK
# ============================================================
app = Flask(__name__)
CORS(app)

# ============================================================
# ENDPOINTS
# ============================================================
@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'mode': 'yahoo_finance'})

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
                return jsonify(data)
    
    # Calcular NDI
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
            'price_history': [],
            'fallback': True,
            'message': 'No se pudieron obtener datos'
        }
    
    # Guardar en caché
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
    
    return jsonify({'success': True, 'signals': results, 'count': len(results)})

@app.route('/api/tickers')
def get_tickers():
    return jsonify({'tickers': TICKERS, 'count': len(TICKERS)})

@app.route('/')
def root():
    return jsonify({
        'name': 'SignalIQ API',
        'version': '3.0',
        'mode': 'yahoo_finance',
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
    logger.info("🚀 SignalIQ API - Versión Simplificada")
    logger.info(f"📊 Puerto: {port}")
    logger.info("=" * 50)
    app.run(host='0.0.0.0', port=port, debug=False)
