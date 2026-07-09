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
import requests
import time

# ============================================================
# IMPORTACIÓN DE YAHOO_PROXY (SOLUCIÓN DEFINITIVA)
# ============================================================
# Agregar el directorio actual al path para importar módulos locales
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from yahoo_proxy import yahoo_proxy

# Importación directa (layers ahora está en app/)
from layers.layer4_measurement import calculate_narrative_divergence_index
from news_pipeline import process_news_for_ticker

# ============================================================
# CREAR APLICACIÓN FLASK
# ============================================================
app = Flask(__name__)
app.register_blueprint(yahoo_proxy)

# Configurar CORS correctamente
CORS(app, origins=[
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://signaliq-zeta-ten.vercel.app",
    "https://signaliq-zeta.vercel.app",
    "https://signaliq-l8mi.onrender.com"
], supports_credentials=True)


from functools import lru_cache
from datetime import datetime, timedelta

# ============================================================
# CACHÉ PARA /api/signals-live
# ============================================================
import hashlib
import json
from datetime import datetime, timedelta
from functools import lru_cache

# Configuración del caché
CACHE_TTL = 60  # 60 segundos (1 minuto)
_cache = {}  # Diccionario para almacenar los resultados
_cache_timestamps = {}  # Para rastrear cuándo se creó cada caché

def get_cache_key(tickers_str: str) -> str:
    """Generar una clave única para el caché"""
    return hashlib.md5(tickers_str.encode()).hexdigest()

def get_cached_signals(tickers_str: str):
    """Obtener señales con caché de 60 segundos"""
    cache_key = get_cache_key(tickers_str)
    now = datetime.now()
    
    # Verificar si el caché existe y no ha expirado
    if cache_key in _cache and cache_key in _cache_timestamps:
        elapsed = (now - _cache_timestamps[cache_key]).total_seconds()
        if elapsed < CACHE_TTL:
            logger.info(f"📊 CACHÉ: Usando datos en caché para {tickers_str} (edad: {elapsed:.1f}s)")
            return _cache[cache_key]
    
    # Procesar los datos (no hay caché o expiró)
    logger.info(f"📊 CACHÉ: Procesando {tickers_str} (sin caché)")
    tickers = tickers_str.split(',')
    
    results = []
    for ticker in tickers:
        try:
            news_data = process_news_for_ticker(ticker)
            sentiment_zscore = calculate_sentiment_zscore(news_data['sentiment'])
            momentum_zscore = 0.0
            ndi = calculate_narrative_divergence_index(sentiment_zscore, momentum_zscore)
            if ndi is None:
                ndi = 0.0
            
            regime = classify_regime(ndi)
            price = get_price_yfinance(ticker)
            
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
            results.append({
                'ticker': ticker,
                'ndi': 0,
                'sentiment_zscore': 0,
                'momentum_zscore': 0,
                'current_price': None,
                'regime': 'NEUTRAL',
                'confidence': 0
            })
    
    response = {
        'success': True,
        'signals': results,
        'count': len(results),
        'cached': False,
        'timestamp': now.isoformat()
    }
    
    # Guardar en caché
    _cache[cache_key] = response
    _cache_timestamps[cache_key] = now
    
    return response

# ============================================================
# CONFIGURACIÓN DE YFINANCE CON SESIÓN PERSISTENTE
# ============================================================

def get_yfinance_session():
    """Crear una sesión persistente para yfinance con headers"""
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive'
    })
    return session

# Crear la sesión al inicio
yf_session = get_yfinance_session()

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
    if news_sentiment is None:
        return 0.0
    return float(news_sentiment)

def calculate_momentum_zscore(price_history):
    if not price_history or len(price_history) < 2:
        return 0.0
    
    returns = []
    for i in range(1, len(price_history)):
        if price_history[i-1] != 0:
            returns.append((price_history[i] - price_history[i-1]) / price_history[i-1])
    
    if not returns:
        return 0.0
    
    last_return = returns[-1]
    mean_return = np.mean(returns)
    std_return = np.std(returns) if np.std(returns) > 0 else 1.0
    
    return (last_return - mean_return) / std_return


# ============================================================
# FUNCIONES DE PRECIOS (SOLO YFINANCE)
# ============================================================

def get_price_yfinance(ticker):
    """Obtener precio desde Yahoo Finance"""
    try:
        stock = yf.Ticker(ticker, session=yf_session)
        hist = stock.history(period="2d", timeout=10)
        if not hist.empty:
            price = hist['Close'].iloc[-1]
            logger.info(f"💰 yfinance: ${price} para {ticker}")
            return price
    except Exception as e:
        logger.error(f"❌ yfinance error para {ticker}: {str(e)}")
    return None

def get_price(ticker):
    """Obtener precio desde Yahoo Finance"""
    return get_price_yfinance(ticker)

def get_company_info(ticker):
    """Obtener información de la empresa desde yfinance"""
    try:
        stock = yf.Ticker(ticker, session=yf_session)
        info = stock.info
        return {
            'company_name': info.get('longName', info.get('shortName', ticker)),
            'sector': info.get('sector', 'Unknown'),
            'industry': info.get('industry', 'Unknown')
        }
    except Exception as e:
        logger.warning(f"⚠️ No se pudo obtener info de {ticker}: {str(e)}")
        return {
            'company_name': ticker,
            'sector': 'Unknown',
            'industry': 'Unknown'
        }


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
    """Endpoint para el dashboard de señales en vivo (con caché)"""
    tickers_param = request.args.get('tickers', '')
    ticker_list = [t.strip() for t in tickers_param.split(',') if t.strip()]
    
    if not ticker_list:
        return jsonify({'success': False, 'error': 'No tickers provided'}), 400
    
    # Ordenar tickers para que el caché funcione correctamente
    tickers_str = ','.join(sorted(ticker_list))
    
    # Obtener del caché (o procesar si no existe)
    result = get_cached_signals(tickers_str)
    
    # Filtrar solo los tickers solicitados
    ticker_set = set(ticker_list)
    filtered_signals = [s for s in result['signals'] if s['ticker'] in ticker_set]
    
    return jsonify({
        'success': True,
        'signals': filtered_signals,
        'count': len(filtered_signals),
        'cached': result.get('cached', False),
        'cache_timestamp': result.get('timestamp')
    })

@app.route('/api/ticker/analysis/<ticker>')
def ticker_analysis(ticker):
    try:
        ticker = ticker.upper()
        logger.info(f"📊 Analizando {ticker}")
        
        # 1. Obtener noticias REALES
        news_data = process_news_for_ticker(ticker)
        news_items = []
        for h, s in zip(news_data['headlines'], news_data['scores']):
            news_items.append({
                'headline': h,
                'sentiment': s,
                'source': 'RSS Feed'
            })
        
        # 2. Obtener precio (desde Yahoo Finance)
        price = get_price_yfinance(ticker)
        price_available = price is not None
        price_history = []
        
        # 3. Obtener historial de precios para momentum
        if price_available:
            try:
                stock = yf.Ticker(ticker, session=yf_session)
                hist = stock.history(period="5d", timeout=10)
                if not hist.empty:
                    price_history = hist['Close'].tolist()
            except:
                pass
        
        # 4. Calcular z-scores
        sentiment_zscore = calculate_sentiment_zscore(news_data['sentiment'])
        momentum_zscore = calculate_momentum_zscore(price_history) if price_available else 0.0
        
        # 5. Calcular NDI
        ndi = calculate_narrative_divergence_index(sentiment_zscore, momentum_zscore)
        if ndi is None:
            ndi = 0.0
        
        regime = classify_regime(ndi)
        
        # 6. Obtener información de la empresa
        company_info = get_company_info(ticker)
        company_name = company_info['company_name']
        sector = company_info['sector']
        industry = company_info['industry']
        
        # 7. Construir respuesta
        response = {
            'ticker': ticker,
            'companyName': company_name,
            'sector': sector,
            'industry': industry,
            'price_unavailable': not price_available,
            'ndi': round(ndi, 3),
            'statusLabel': regime['regime'],
            'statusColor': regime['color'],
            'updatedAt': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S'),
            'price': price,
            'quantitativeMetrics': {
                'sentiment': round(sentiment_zscore, 3),
                'momentum': round(momentum_zscore, 3),
                'divergence': round(ndi, 3),
                'sourcesCount': len(news_data['headlines'])
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
            'aiInterpretation': f"{ticker}: NDI {ndi:.3f} - {regime['regime']}. {news_data['count']} noticias procesadas con sentimiento {news_data['sentiment']:.3f}.",
            'newsSummary': {
                'items': news_items,
                'positiveCount': sum(1 for s in news_data['scores'] if s > 0.1),
                'negativeCount': sum(1 for s in news_data['scores'] if s < -0.1),
                'averageSentiment': news_data['sentiment']
            },
            'relativeContext': {
                'sectorName': sector,
                'comparison': {
                    'tickerSentiment': round(sentiment_zscore, 3),
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
                'insight': f"{ticker}: NDI {ndi:.3f} - {regime['regime']}. Sentimiento de noticias: {news_data['sentiment']:.3f}"
            }
        }
        
        if not price_available:
            response['message'] = "Precio no disponible temporalmente, pero las noticias se muestran correctamente."
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"❌ Error en ticker_analysis: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/prices/<ticker>')
def get_prices(ticker):
    """Obtener historial de precios para el gráfico"""
    try:
        ticker = ticker.upper()
        logger.info(f"📊 Obteniendo historial de precios para {ticker}")
        
        # Crear una nueva sesión con headers más completos
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        })
        
        # Usar yfinance con la sesión
        import yfinance as yf
        stock = yf.Ticker(ticker, session=session)
        
        # Intentar obtener datos con diferentes períodos
        periods = ["5d", "7d", "14d", "30d"]
        hist = None
        
        for period in periods:
            try:
                logger.info(f"🔄 Intentando con período {period}...")
                hist = stock.history(period=period, timeout=15)
                if hist is not None and not hist.empty:
                    logger.info(f"✅ Datos encontrados para {ticker} con período {period}")
                    break
            except Exception as e:
                logger.warning(f"⚠️ Falló período {period}: {str(e)}")
                continue
        
        if hist is not None and not hist.empty:
            price_history = []
            for date, row in hist.iterrows():
                price_history.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'close': float(row['Close'])
                })
            return jsonify({
                'ticker': ticker,
                'price_history': price_history
            })
        else:
            # Si no hay datos, devolver datos de ejemplo
            logger.warning(f"⚠️ No se encontraron datos para {ticker}, usando datos de ejemplo")
            # Generar datos de ejemplo para que el gráfico funcione
            import random
            from datetime import datetime, timedelta
            
            sample_history = []
            base_price = 200.0 if ticker == 'NVDA' else 100.0
            current_date = datetime.now()
            
            for i in range(30, 0, -1):
                date = current_date - timedelta(days=i)
                price = base_price + random.uniform(-10, 10)
                sample_history.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'close': round(price, 2)
                })
            
            return jsonify({
                'ticker': ticker,
                'price_history': sample_history,
                'sample': True,
                'message': 'Datos de muestra generados'
            })
            
    except Exception as e:
        logger.error(f"❌ Error en /api/prices/{ticker}: {str(e)}")
        return jsonify({'error': str(e)}), 500
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