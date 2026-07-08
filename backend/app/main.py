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

# Importación directa (layers ahora está en app/)
from layers.layer4_measurement import calculate_narrative_divergence_index
from news_pipeline import process_news_for_ticker

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend', 'app'))

app = Flask(__name__)

# Configurar CORS correctamente (SIN duplicar cabeceras)
CORS(app, origins=[
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://signaliq-zeta-ten.vercel.app",
    "https://signaliq-zeta.vercel.app",
    "https://signaliq-l8mi.onrender.com"
], supports_credentials=True)

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

# Manejar solicitudes OPTIONS para CORS (sin duplicar Access-Control-Allow-Origin)
@app.after_request
def after_request(response):
    # No agregar Access-Control-Allow-Origin aquí porque CORS ya lo maneja
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
# FUNCIONES DE PRECIOS E INFORMACIÓN (PRIORIZANDO TWELVE DATA)
# ============================================================

def get_price_twelve_data(ticker):
    """Obtener precio desde Twelve Data API (fuente principal)"""
    api_key = os.environ.get('TWELVE_DATA_API_KEY', '')
    if not api_key:
        logger.warning("⚠️ TWELVE_DATA_API_KEY no configurada")
        return None
    
    try:
        url = f"https://api.twelvedata.com/price?symbol={ticker}&apikey={api_key}"
        response = requests.get(url, timeout=5)
        data = response.json()
        if 'price' in data:
            price = float(data['price'])
            logger.info(f"💰 Twelve Data: ${price} para {ticker}")
            return price
        else:
            logger.warning(f"⚠️ Twelve Data: respuesta inesperada para {ticker}: {data}")
    except Exception as e:
        logger.error(f"❌ Twelve Data error para {ticker}: {str(e)}")
    return None

def get_price_yfinance(ticker):
    """Obtener precio desde Yahoo Finance (fallback)"""
    try:
        start = time.time()
        stock = yf.Ticker(ticker, session=yf_session)
        hist = stock.history(period="2d", timeout=15)
        if not hist.empty:
            price = hist['Close'].iloc[-1]
            logger.info(f"💰 yfinance: ${price} para {ticker} (tardó {time.time() - start:.2f}s)")
            return price
        else:
            logger.warning(f"⚠️ yfinance: sin datos para {ticker}")
    except Exception as e:
        logger.error(f"❌ yfinance error para {ticker}: {str(e)}")
    return None

def get_price_alpha_vantage(ticker):
    """Obtener precio desde Alpha Vantage API (fallback 2)"""
    api_key = os.environ.get('ALPHA_VANTAGE_API_KEY', '')
    if not api_key:
        return None
    
    try:
        url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={ticker}&apikey={api_key}"
        response = requests.get(url, timeout=5)
        data = response.json()
        if 'Global Quote' in data and '05. price' in data['Global Quote']:
            price = float(data['Global Quote']['05. price'])
            logger.info(f"💰 Alpha Vantage: ${price} para {ticker}")
            return price
    except Exception as e:
        logger.error(f"❌ Alpha Vantage error para {ticker}: {str(e)}")
    return None

def get_price(ticker):
    """Intentar obtener precio: Twelve Data primero, luego fallbacks"""
    # 1. Intentar Twelve Data (PRINCIPAL - funciona en Render)
    price = get_price_twelve_data(ticker)
    if price is not None:
        return price
    
    # 2. Intentar yfinance (FALLBACK)
    price = get_price_yfinance(ticker)
    if price is not None:
        return price
    
    # 3. Intentar Alpha Vantage (FALLBACK 2)
    price = get_price_alpha_vantage(ticker)
    if price is not None:
        return price
    
    logger.warning(f"⚠️ No se pudo obtener precio para {ticker} de ninguna fuente")
    return None

def get_company_info(ticker):
    """Obtener información de la empresa desde Twelve Data (principal)"""
    # 1. Intentar Twelve Data (PRINCIPAL - funciona en Render)
    try:
        api_key = os.environ.get('TWELVE_DATA_API_KEY', '')
        if api_key:
            logger.info(f"🔍 Intentando obtener info de {ticker} desde Twelve Data...")
            # Usar el endpoint /quote para obtener información completa
            url = f"https://api.twelvedata.com/quote?symbol={ticker}&apikey={api_key}"
            response = requests.get(url, timeout=5)
            data = response.json()
            
            # Log para depuración
            logger.info(f"📊 Respuesta de Twelve Data para {ticker}: {data}")
            
            company_name = data.get('name', ticker)
            # El sector puede venir en diferentes campos
            sector = data.get('sector', data.get('exchange', 'Unknown'))
            industry = data.get('industry', 'Unknown')
            
            # Si el sector sigue siendo Unknown, intentar con el endpoint /profile
            if sector == 'Unknown' or sector == ticker:
                logger.info(f"🔍 Intentando obtener perfil de {ticker} desde Twelve Data...")
                profile_url = f"https://api.twelvedata.com/profile?symbol={ticker}&apikey={api_key}"
                profile_response = requests.get(profile_url, timeout=5)
                profile_data = profile_response.json()
                logger.info(f"📊 Perfil de Twelve Data para {ticker}: {profile_data}")
                
                sector = profile_data.get('sector', sector)
                industry = profile_data.get('industry', industry)
            
            logger.info(f"✅ Info obtenida de Twelve Data: {company_name}, {sector}, {industry}")
            return {
                'company_name': company_name,
                'sector': sector,
                'industry': industry
            }
    except Exception as e:
        logger.warning(f"⚠️ Twelve Data falló para info de {ticker}: {str(e)}")
    
    # 2. Intentar yfinance (FALLBACK)
    try:
        logger.info(f"🔍 Intentando obtener info de {ticker} desde yfinance...")
        stock = yf.Ticker(ticker, session=yf_session)
        info = stock.info
        
        company_name = info.get('longName', info.get('shortName', ticker))
        sector = info.get('sector', 'Unknown')
        industry = info.get('industry', 'Unknown')
        
        logger.info(f"✅ Info obtenida de yfinance: {company_name}, {sector}, {industry}")
        return {
            'company_name': company_name,
            'sector': sector,
            'industry': industry
        }
    except Exception as e:
        logger.warning(f"⚠️ yfinance falló para info de {ticker}: {str(e)}")
    
    # 3. Si todo falla
    logger.warning(f"⚠️ No se pudo obtener info de {ticker} de ninguna fuente")
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
    """Endpoint para el dashboard de señales en vivo"""
    tickers_param = request.args.get('tickers', '')
    ticker_list = [t.strip() for t in tickers_param.split(',') if t.strip()]
    
    if not ticker_list:
        return jsonify({'success': False, 'error': 'No tickers provided'}), 400
    
    results = []
    for ticker in ticker_list:
        try:
            news_data = process_news_for_ticker(ticker)
            sentiment_zscore = calculate_sentiment_zscore(news_data['sentiment'])
            momentum_zscore = 0.0
            ndi = calculate_narrative_divergence_index(sentiment_zscore, momentum_zscore)
            if ndi is None:
                ndi = 0.0
            
            regime = classify_regime(ndi)
            price = get_price(ticker)
            
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
        
        # 1. Obtener noticias REALES
        news_data = process_news_for_ticker(ticker)
        news_items = []
        for h, s in zip(news_data['headlines'], news_data['scores']):
            news_items.append({
                'headline': h,
                'sentiment': s,
                'source': 'RSS Feed'
            })
        
        # 2. Obtener precio (Twelve Data primero)
        price = get_price(ticker)
        price_available = price is not None
        price_history = []
        
        # 3. Obtener historial de precios para momentum (desde yfinance)
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
        
        # 6. Obtener información de la empresa (Twelve Data primero)
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
        
        # Intentar Twelve Data primero
        api_key = os.environ.get('TWELVE_DATA_API_KEY', '')
        if api_key:
            try:
                url = f"https://api.twelvedata.com/time_series?symbol={ticker}&interval=1day&outputsize=30&apikey={api_key}"
                response = requests.get(url, timeout=10)
                data = response.json()
                
                if 'values' in data:
                    price_history = []
                    for item in data['values']:
                        price_history.append({
                            'date': item['datetime'][:10],
                            'close': float(item['close'])
                        })
                    price_history.reverse()
                    return jsonify({
                        'ticker': ticker,
                        'price_history': price_history
                    })
            except Exception as e:
                logger.warning(f"⚠️ Twelve Data falló para historial de {ticker}: {str(e)}")
        
        # Fallback: yfinance
        stock = yf.Ticker(ticker, session=yf_session)
        hist = stock.history(period="30d", timeout=10)
        if not hist.empty:
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
            return jsonify({'error': 'No data available'}), 404
    except Exception as e:
        logger.error(f"❌ Error en /api/prices/{ticker}: {str(e)}")
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
    logger.info("📊 Usando yfinance + noticias reales")
    app.run(host='0.0.0.0', port=port, debug=False)