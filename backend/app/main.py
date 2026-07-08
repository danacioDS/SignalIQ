"""
SignalIQ API - Con noticias reales
"""
import os
import sys
import logging
from datetime import datetime, timezone
from flask import Flask, jsonify, request
from flask_cors import CORS
import yfinance as yf
import numpy as np

# Importación directa (layers ahora está en app/)
from layers.layer4_measurement import calculate_narrative_divergence_index
from news_pipeline import process_news_for_ticker

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend', 'app'))

app = Flask(__name__)

# Configurar CORS para permitir solicitudes desde Vercel
CORS(app, origins=[
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://signaliq-zeta-ten.vercel.app",
    "https://signaliq-zeta.vercel.app",
    "https://signaliq-l8mi.onrender.com"
])

# Manejar solicitudes OPTIONS para CORS
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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

def calculate_sentiment_zscore(news_sentiment):
    """
    Calcula el z-score del sentimiento basado en noticias.
    Usa valores históricos simulados para la demostración.
    """
    if news_sentiment is None:
        return 0.0
    
    # Por ahora, usamos una transformación simple
    # En producción, esto vendría de Layer 3
    return float(news_sentiment)

def calculate_momentum_zscore(price_history):
    """
    Calcula el z-score del momentum basado en precios históricos.
    """
    if not price_history or len(price_history) < 2:
        return 0.0
    
    # Calcular retornos diarios
    returns = []
    for i in range(1, len(price_history)):
        if price_history[i-1] != 0:
            returns.append((price_history[i] - price_history[i-1]) / price_history[i-1])
    
    if not returns:
        return 0.0
    
    # Calcular z-score del último retorno
    last_return = returns[-1]
    mean_return = np.mean(returns)
    std_return = np.std(returns) if np.std(returns) > 0 else 1.0
    
    return (last_return - mean_return) / std_return

# ============================================================
# RUTAS
# ============================================================

@app.route('/')
def root():
    return jsonify({
        'name': 'SignalIQ API',
        'version': '2026-07-07',
        'status': 'operational',
        'mode': 'yfinance_with_news'
    })

@app.route('/health')
@app.route('/api/health')
def health():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'mode': 'yfinance_with_news'
    })

@app.route('/api/signals-live')
def signals_live():
    """Endpoint para el dashboard de señales en vivo"""
    tickers_param = request.args.get('tickers', '')
    ticker_list = [t.strip() for t in tickers_param.split(',') if t.strip()]
    
    if not ticker_list:
        return jsonify({'success': False, 'error': 'No tickers provided'}), 400
    
    results = []
    for ticker in ticker_list:
        try:
            # Obtener noticias para cada ticker
            news_data = process_news_for_ticker(ticker)
            
            # Calcular NDI
            sentiment_zscore = calculate_sentiment_zscore(news_data['sentiment'])
            momentum_zscore = 0.0
            ndi = calculate_narrative_divergence_index(sentiment_zscore, momentum_zscore)
            if ndi is None:
                ndi = 0.0
            
            regime = classify_regime(ndi)
            
            # Intentar obtener precio
            price = None
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(period="1d")
                if not hist.empty:
                    price = hist['Close'].iloc[-1]
            except:
                pass
            
            results.append({
                'ticker': ticker,
                'ndi': ndi,
                'sentiment_zscore': sentiment_zscore,
                'momentum_zscore': momentum_zscore,
                'current_price': price,
                'regime': regime['regime'],
                'confidence': 70
            })
        except Exception as e:
            logger.error(f"Error procesando {ticker}: {e}")
            # Agregar un resultado de fallback
            results.append({
                'ticker': ticker,
                'ndi': 0,
                'sentiment_zscore': 0,
                'momentum_zscore': 0,
                'current_price': None,
                'regime': 'NEUTRAL',
                'confidence': 0
            })
    
    return jsonify({
        'success': True,
        'signals': results,
        'count': len(results)
    })

@app.route('/api/ticker/analysis/<ticker>')
def ticker_analysis(ticker):
    try:
        ticker = ticker.upper()
        logger.info(f"📊 Analizando {ticker}")
        
        # 1. Obtener noticias REALES (SIEMPRE)
        news_data = process_news_for_ticker(ticker)
        news_items = []
        for h, s in zip(news_data['headlines'], news_data['scores']):
            news_items.append({
                'headline': h,
                'sentiment': s,
                'source': 'RSS Feed'
            })
        
        # 2. Intentar obtener precio (yfinance) con User-Agent
        price_available = False
        price = None
        price_history = []
        
        try:
            # Configurar headers para simular un navegador
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            stock = yf.Ticker(ticker, headers=headers)
            hist = stock.history(period="5d", timeout=10)
            if not hist.empty:
                price_available = True
                price = hist['Close'].iloc[-1]
                price_history = hist['Close'].tolist()
                logger.info(f"💰 Precio obtenido para {ticker}: ${price}")
            else:
                logger.warning(f"⚠️ No hay datos de precio para {ticker}")
        except Exception as e:
            logger.error(f"❌ Error al obtener precio para {ticker}: {str(e)}")
        

@app.route('/api/tickers')
def get_tickers():
    return jsonify({
        'tickers': ['NVDA', 'AAPL', 'MSFT', 'TSLA', 'GOOGL', 'META', 'AMD', 'AMZN', 'JPM', 'KO'],
        'count': 10
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"🚀 SignalIQ API en puerto {port}")
    logger.info("📊 Usando yfinance + noticias reales")
    app.run(host='0.0.0.0', port=port, debug=False)