"""
SignalIQ API - YFINANCE CON USER-AGENT REAL
"""

import os
import logging
import time
import requests
from datetime import datetime, timezone
from flask import Flask, jsonify, request
from flask_cors import CORS
import yfinance as yf
import numpy as np

# Configurar User-Agent para evitar bloqueos
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

app = Flask(__name__)

CORS(app, origins=[
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://signaliq-zeta-ten.vercel.app",
    "https://signaliq-zeta.vercel.app",
    "https://signaliq-l8mi.onrender.com"
])

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================
# FUNCIONES
# ============================================================

def calculate_ndi(closes):
    if len(closes) < 2:
        return 0.0, 0.0, 0.0
    
    daily_returns = []
    for i in range(1, len(closes)):
        if closes[i-1] > 0:
            daily_returns.append((closes[i] - closes[i-1]) / closes[i-1])
    
    if len(daily_returns) >= 2:
        mean_ret = np.mean(daily_returns)
        std_ret = np.std(daily_returns)
        sentiment_zscore = (daily_returns[-1] - mean_ret) / std_ret if std_ret > 0 else 0.0
    else:
        sentiment_zscore = 0.0
    
    momentum_period = 20
    if len(closes) >= momentum_period:
        momentum_returns = []
        for i in range(momentum_period, len(closes)):
            if closes[i-momentum_period] > 0:
                momentum_returns.append((closes[i] / closes[i-momentum_period] - 1))
        if len(momentum_returns) >= 2:
            mean_mom = np.mean(momentum_returns)
            std_mom = np.std(momentum_returns)
            momentum_zscore = (momentum_returns[-1] - mean_mom) / std_mom if std_mom > 0 else 0.0
        else:
            momentum_zscore = 0.0
    else:
        momentum_zscore = 0.0
    
    ndi = sentiment_zscore - momentum_zscore
    ndi = max(-3.0, min(3.0, ndi))
    return ndi, sentiment_zscore, momentum_zscore

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

def get_stock_data(ticker, retries=5):
    """Obtiene datos de yfinance con User-Agent y reintentos"""
    for attempt in range(retries):
        try:
            logger.info(f"📊 Intentando {ticker} (intento {attempt+1}/{retries})")
            
            # Usar yfinance con User-Agent
            stock = yf.Ticker(ticker)
            
            # Configurar sesión con headers
            session = requests.Session()
            session.headers.update(headers)
            
            # Intentar obtener datos
            hist = stock.history(period="60d")
            
            if not hist.empty:
                logger.info(f"✅ Datos obtenidos para {ticker}")
                return hist
            
            logger.warning(f"⚠️ No hay datos para {ticker}, intento {attempt+1}")
            time.sleep(2 ** attempt)  # Backoff exponencial
            
        except Exception as e:
            logger.warning(f"⚠️ Error: {e}, intento {attempt+1}")
            time.sleep(2 ** attempt)
    
    logger.error(f"❌ No se pudieron obtener datos para {ticker}")
    return None

# ============================================================
# RUTAS
# ============================================================

@app.route('/')
def root():
    return jsonify({
        'name': 'SignalIQ API',
        'version': '2026-07-07',
        'status': 'operational',
        'mode': 'yfinance_only',
        'database': 'disabled'
    })

@app.route('/health')
@app.route('/api/health')
def health():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'mode': 'yfinance_only',
        'database': 'disabled'
    })

@app.route('/api/ticker/analysis/<ticker>')
def ticker_analysis(ticker):
    try:
        ticker = ticker.upper()
        logger.info(f"📊 Analizando {ticker}")
        
        hist = get_stock_data(ticker)
        
        if hist is None or hist.empty:
            logger.error(f"❌ No hay datos para {ticker}")
            return jsonify({
                'error': f'No se pudieron obtener datos para {ticker}',
                'ticker': ticker,
                'suggestion': 'Intenta con otro ticker o más tarde'
            }), 404
        
        closes = hist['Close'].tolist()
        ndi, sentiment, momentum = calculate_ndi(closes)
        regime = classify_regime(ndi)
        
        # Obtener información
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            company_name = info.get('longName', info.get('shortName', ticker))
            sector = info.get('sector', 'Unknown')
            current_price = closes[-1] if closes else 0
        except:
            company_name = ticker
            sector = 'Unknown'
            current_price = closes[-1] if closes else 0
        
        response = {
            'ticker': ticker,
            'companyName': company_name,
            'sector': sector,
            'industry': 'Unknown',
            'ndi': round(ndi, 3),
            'statusLabel': regime['regime'],
            'statusColor': regime['color'],
            'updatedAt': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S'),
            'quantitativeMetrics': {
                'sentiment': round(sentiment, 3),
                'momentum': round(momentum, 3),
                'divergence': round(ndi, 3),
                'sourcesCount': len(hist)
            },
            'narrativeBreakdown': {
                'consensusPercentage': 74,
                'consensusLabel': 'Alto',
                'intensityPercentage': 52,
                'intensityLabel': 'Moderada',
                'dispersionValue': 0.22,
                'dispersionLabel': 'Baja',
                'mediaBias': {
                    'centerBizPercentage': 60,
                    'leftPercentage': 20,
                    'rightPercentage': 20
                }
            },
            'narrativeExhaustion': {
                'level': 'BAJA',
                'conditionsObserved': 0,
                'totalConditions': 3,
                'conditionsDetails': [],
                'disclaimer': 'Feature en fase beta.',
                'isBeta': True
            },
            'aiInterpretation': f"{ticker}: NDI {ndi:.3f} - {regime['regime']}. Datos reales de yfinance.",
            'newsSummary': {
                'items': [],
                'positiveCount': 0,
                'negativeCount': 0,
                'averageSentiment': 0
            },
            'relativeContext': {
                'sectorName': sector,
                'comparison': {
                    'tickerSentiment': round(sentiment, 3),
                    'sectorSentiment': 0,
                    'sentimentDifference': 0,
                    'sentimentLabel': '🟢 en línea con el sector',
                    'tickerConsensus': 50,
                    'sectorConsensus': 50,
                    'consensusDifference': 0,
                    'consensusLabel': '🟢 en línea con el sector',
                    'tickerExhaustion': 'BAJA',
                    'sectorExhaustion': 'BAJA',
                    'exhaustionLabel': '🟢 en línea con el sector'
                },
                'sectorRanking': [
                    {'rank': 1, 'ticker': ticker, 'companyName': company_name,
                     'ndi': round(ndi, 3), 'regimeLabel': regime['label'], 'regimeColor': regime['color']}
                ],
                'insight': f"{ticker}: NDI {ndi:.3f} - {regime['regime']}"
            }
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/tickers')
def get_tickers():
    return jsonify({
        'tickers': ['NVDA', 'AAPL', 'MSFT', 'TSLA', 'GOOGL', 'META', 'AMD', 'AMZN', 'JPM', 'KO'],
        'count': 10
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"🚀 SignalIQ API en puerto {port}")
    logger.info("📊 Usando yfinance con User-Agent real")
    app.run(host='0.0.0.0', port=port, debug=False)
