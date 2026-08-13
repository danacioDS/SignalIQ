from dotenv import load_dotenv
load_dotenv()
"""
SignalIQ API - Optimizado con Caché y Mínimo Consumo de APIs
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
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
# Import news_pipeline - absoluto para Render
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
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
# NOMBRES COMERCIALES DE EMPRESAS
# ============================================================
COMPANY_NAMES = {
    'AAPL': 'Apple Inc.',
    'MSFT': 'Microsoft Corp.',
    'NVDA': 'NVIDIA Corp.',
    'GOOGL': 'Alphabet Inc.',
    'META': 'Meta Platforms Inc.',
    'AMD': 'Advanced Micro Devices',
    'AMZN': 'Amazon.com Inc.',
    'TSLA': 'Tesla Inc.',
    'JPM': 'JPMorgan Chase & Co.',
    'KO': 'The Coca-Cola Company',
    'NOK': 'Nokia Oyj'
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
    """
    Obtiene el precio actual del ticker.

    Prioridad:
    1. Caché
    2. Twelve Data
    3. Alpha Vantage
    4. Yahoo Finance
    5. Fallback estático (último recurso)
    """
    ticker = ticker.strip().upper()
    cache_key = f'price_{ticker}'

    # ========================================================
    # CACHÉ
    # ========================================================
    cached = get_cached(cache_key, 'price')
    if cached is not None:
        return cached, "cache"

    # ========================================================
    # 1. TWELVE DATA - FUENTE PRIMARIA
    # ========================================================
    if TWELVE_DATA_API_KEY:
        try:
            url = "https://api.twelvedata.com/price"
            params = {
                "symbol": ticker,
                "apikey": TWELVE_DATA_API_KEY
            }

            response = requests.get(url, params=params, timeout=5)

            logger.info(
                f"Twelve Data status={response.status_code} ticker={ticker}"
            )

            if response.status_code == 200:
                data = response.json()
                raw_price = data.get("price")

                if raw_price is not None:
                    try:
                        price = float(raw_price)

                        if np.isfinite(price) and price > 0:
                            set_cached(cache_key, price, 'price')

                            logger.info(
                                f"💰 Twelve Data: {ticker} = ${price:.2f}"
                            )

                            return price, "twelve_data"

                        logger.warning(
                            f"⚠️ Twelve Data precio inválido para "
                            f"{ticker}: {raw_price}"
                        )

                    except (TypeError, ValueError):
                        logger.warning(
                            f"⚠️ Twelve Data precio no numérico para "
                            f"{ticker}: {raw_price}"
                        )
                else:
                    logger.warning(
                        f"⚠️ Twelve Data no devolvió precio para "
                        f"{ticker}: {data}"
                    )

            else:
                logger.warning(
                    f"⚠️ Twelve Data HTTP {response.status_code}: "
                    f"{response.text[:200]}"
                )

        except Exception as e:
            logger.warning(
                f"⚠️ Twelve Data falló para {ticker}: "
                f"{type(e).__name__}: {e}"
            )
    else:
        logger.warning("⚠️ TWELVE_DATA_API_KEY no configurada")

    # ========================================================
    # 2. ALPHA VANTAGE - BACKUP
    # ========================================================
    if ALPHA_VANTAGE_API_KEY:
        try:
            url = "https://www.alphavantage.co/query"
            params = {
                "function": "GLOBAL_QUOTE",
                "symbol": ticker,
                "apikey": ALPHA_VANTAGE_API_KEY
            }

            response = requests.get(url, params=params, timeout=5)

            logger.info(
                f"Alpha Vantage status={response.status_code} "
                f"ticker={ticker}"
            )

            if response.status_code == 200:
                data = response.json()

                if "Note" in data:
                    logger.warning(
                        f"⚠️ Alpha Vantage rate limit para {ticker}"
                    )

                elif "Information" in data:
                    logger.warning(
                        f"⚠️ Alpha Vantage no disponible para {ticker}: "
                        f"{data['Information'][:150]}"
                    )

                elif (
                    "Global Quote" in data
                    and "05. price" in data["Global Quote"]
                ):
                    try:
                        price = float(
                            data["Global Quote"]["05. price"]
                        )

                        if np.isfinite(price) and price > 0:
                            set_cached(cache_key, price, 'price')

                            logger.info(
                                f"🔄 Alpha Vantage: "
                                f"{ticker} = ${price:.2f}"
                            )

                            return price, "alpha_vantage"

                    except (TypeError, ValueError):
                        logger.warning(
                            f"⚠️ Alpha Vantage precio inválido "
                            f"para {ticker}"
                        )

                else:
                    logger.warning(
                        f"⚠️ Alpha Vantage sin precio para {ticker}: "
                        f"{data}"
                    )

            else:
                logger.warning(
                    f"⚠️ Alpha Vantage HTTP "
                    f"{response.status_code}"
                )

        except Exception as e:
            logger.warning(
                f"⚠️ Alpha Vantage falló para {ticker}: "
                f"{type(e).__name__}: {e}"
            )
    else:
        logger.warning(
            "⚠️ ALPHA_VANTAGE_API_KEY no configurada"
        )

    # ========================================================
    # 3. YAHOO FINANCE
    # ========================================================
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="2d")

        if not hist.empty and "Close" in hist.columns:
            price = float(hist["Close"].iloc[-1])

            if np.isfinite(price) and price > 0:
                set_cached(cache_key, price, 'price')

                logger.info(
                    f"🔄 Yahoo Finance: "
                    f"{ticker} = ${price:.2f}"
                )

                return price, "yahoo"

        logger.warning(
            f"⚠️ Yahoo Finance sin datos para {ticker}"
        )

    except Exception as e:
        logger.warning(
            f"⚠️ Yahoo Finance falló para {ticker}: "
            f"{type(e).__name__}: {e}"
        )

    # ========================================================
    # 4. FALLBACK - ÚLTIMO RECURSO
    # ========================================================
    price = FALLBACK_PRICES.get(ticker, 100.0)

    set_cached(cache_key, price, 'price')

    logger.warning(
        f"🚨 FALLBACK para {ticker}: ${price:.2f}"
    )

    return price, "fallback"


def get_price_history(ticker, days=30):
    """
    Obtiene historial de precios reales.
    Prioridad: Twelve Data -> Alpha Vantage -> Yahoo -> fallback simulado.
    """
    cache_key = f'history_{ticker}_{days}'
    cached = get_cached(cache_key, 'history')
    if cached is not None:
        return cached

    history = []

    # 1. Twelve Data
    if TWELVE_DATA_API_KEY:
        try:
            url = "https://api.twelvedata.com/time_series"
            params = {
                "symbol": ticker,
                "interval": "1day",
                "outputsize": days,
                "apikey": TWELVE_DATA_API_KEY
            }

            response = requests.get(url, params=params, timeout=10)
            data = response.json()

            if 'values' in data:
                values = data['values']
                history = [
                    float(item['close'])
                    for item in reversed(values)
                    if item.get('close') is not None
                ]

                if history:
                    set_cached(cache_key, history, 'history')
                    logger.info(
                        f"📊 Twelve Data: historial real para {ticker} "
                        f"({len(history)} días)"
                    )
                    return history

        except Exception as e:
            logger.warning(f"Twelve Data histórico falló: {e}")

    # 2. Alpha Vantage
    if ALPHA_VANTAGE_API_KEY:
        try:
            url = "https://www.alphavantage.co/query"
            params = {
                "function": "TIME_SERIES_DAILY",
                "symbol": ticker,
                "outputsize": "compact",
                "apikey": ALPHA_VANTAGE_API_KEY
            }

            response = requests.get(url, params=params, timeout=10)
            data = response.json()

            if 'Time Series (Daily)' in data:
                time_series = data['Time Series (Daily)']
                dates = sorted(time_series.keys())[-days:]

                history = [
                    float(time_series[d]['4. close'])
                    for d in dates
                ]

                if history:
                    set_cached(cache_key, history, 'history')
                    logger.info(
                        f"📊 Alpha Vantage: historial real para {ticker} "
                        f"({len(history)} días)"
                    )
                    return history

        except Exception as e:
            logger.warning(f"Alpha Vantage histórico falló: {e}")

    # 3. Yahoo Finance
    try:
        ticker_obj = yf.Ticker(ticker)
        hist = ticker_obj.history(period=f'{days}d')

        if not hist.empty:
            history = [float(row['Close']) for _, row in hist.iterrows()]
            set_cached(cache_key, history, 'history')
            logger.info(
                f"📊 Yahoo Finance: historial real para {ticker} "
                f"({len(history)} días)"
            )
            return history

    except Exception as e:
        logger.warning(f"Yahoo Finance histórico falló: {e}")

    # 4. Fallback simulado (con advertencia)
    current_price, _ = get_price(ticker)
    if current_price is None:
        current_price = FALLBACK_PRICES.get(ticker, 100.0)

    history = []
    for i in range(days):
        price = current_price * (1 + 0.001 * (i - days/2))
        history.append(round(price, 2))

    set_cached(cache_key, history, 'history')
    logger.warning(f"⚠️ Usando historial SIMULADO para {ticker}")
    return history


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
        price, price_source = get_price(ticker)
                # get_price_history devuelve lista de precios o dict con 'history'
        history_result = get_price_history(ticker, days=30)
        if isinstance(history_result, dict):
            history = history_result.get('history', [])
        else:
            history = history_result
        
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
    "https://signaliq-l8mi.onrender.com"
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
            try:
                data = calculate_ndi(ticker)
                if data:
                    results.append(data)
            except Exception as e:
                logger.error(f"Error en signals_live para {ticker}: {e}")
                # Añadir placeholder para tickers con error
                results.append({
                    'ticker': ticker,
                    'price': 0,
                    'current_price': 0,
                    'ndi': 0,
                    'sentiment': 0,
                    'momentum': 0,
                    'regime': 'NEUTRAL',
                    'signal': 'HOLD',
                    'color': 'yellow',
                    'confidence': 50,
                    'price_history': []
                })
    
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


# ============================================================
# ARRANQUE DEL SERVIDOR
# ============================================================

# ============================================================
# FUNCIONES PARA ENDPOINTS
# ============================================================

def get_ticker_data(ticker):
    """Obtiene datos completos de un ticker para /api/signals-intel."""
    try:
        data = calculate_ndi(ticker)
        if not data:
            return None
        return data
    except Exception as e:
        logger.error(f"Error en get_ticker_data para {ticker}: {e}")
        return None

# ============================================================
# ENDPOINTS
# ============================================================

@app.route('/api/prices', methods=['GET'])
def get_all_prices():
    """Return current prices for all tracked tickers."""
    logger.info("📊 /api/prices: iniciando")
    
    tickers = ['NVDA', 'AAPL', 'MSFT', 'TSLA', 'GOOGL', 'META', 'AMD', 'AMZN', 'JPM', 'KO']
    result = {}
    
    for ticker in tickers:
        try:
            logger.info(f"  🔍 Obteniendo precio para {ticker}")
            price, source = get_price(ticker)
            if price:
                result[ticker] = {'price': float(price), 'source': source}
                logger.info(f"  ✅ {ticker}: {price} ({source})")
            else:
                result[ticker] = {'error': 'No price available'}
                logger.warning(f"  ⚠️ {ticker}: sin precio")
        except Exception as e:
            result[ticker] = {'error': str(e)}
            logger.error(f"  ❌ {ticker}: {e}")
    
    logger.info("📊 /api/prices: completado")
    return jsonify(result)

@app.route('/api/signals-intel', methods=['GET'])
def get_signals_intel():
    """Return comprehensive signals for frontend."""
    ticker = request.args.get('ticker')
    if ticker:
        data = get_ticker_data(ticker)
        if data:
            return jsonify(data)
        return jsonify({'error': f'Ticker {ticker} not found'}), 404
    
    tickers = ['NVDA', 'AAPL', 'MSFT', 'TSLA', 'GOOGL', 'META', 'AMD', 'AMZN', 'JPM', 'KO']
    results = {}
    for t in tickers:
        try:
            data = get_ticker_data(t)
            if data:
                results[t] = data
        except Exception as e:
            results[t] = {'error': str(e)}
    return jsonify(results)


@app.route('/api/market-intelligence/analysis', methods=['POST'])
def get_mi_analysis():
    """Genera análisis de 5 líneas para Market Intelligence"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        ticker = data.get('ticker')
        sentiment = data.get('sentiment', 0.0)
        momentum = data.get('momentum', 0.0)
        ndi = data.get('ndi', 0.0)
        regime = data.get('regime', 'UNKNOWN')
        news = data.get('news', [])
        
        if not ticker:
            return jsonify({'error': 'Ticker is required'}), 400
        
        from layers.llm_router import analyze_market_intelligence
        analysis = analyze_market_intelligence(
            ticker=ticker,
            sentiment=sentiment,
            momentum=momentum,
            ndi=ndi,
            regime=regime,
            news=news
        )
        
        return jsonify({
            'ticker': ticker,
            'analysis': analysis
        })
        
    except Exception as e:
        logger.error(f"Error in MI analysis: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/metrics', methods=['GET'])
def get_market_metrics():
    """Return aggregated NDI market intelligence metrics."""
    import numpy as np
    
    cache_key = 'market_metrics'
    cached = get_cached(cache_key, 'metrics')
    if cached is not None:
        return jsonify(cached)
    
    tickers = ['NVDA', 'AAPL', 'MSFT', 'TSLA', 'GOOGL', 'META']
    results = []
    
    for ticker in tickers:
        try:
            data = calculate_ndi(ticker)
            if data and isinstance(data, dict):
                results.append({
                    'ticker': ticker,
                    'price': data.get('price'),
                    'sentiment': data.get('sentiment'),
                    'momentum': data.get('momentum'),
                    'ndi': data.get('ndi'),
                    'regime': data.get('regime'),
                    'confidence': data.get('confidence')
                })
        except Exception as e:
            logger.error(f"Error en {ticker}: {e}")
    
    # Calcular métricas
    ndi_values = [r['ndi'] for r in results if r.get('ndi') is not None]
    sentiment_values = [r['sentiment'] for r in results if r.get('sentiment') is not None]
    momentum_values = [r['momentum'] for r in results if r.get('momentum') is not None]
    confidence_values = [r['confidence'] for r in results if r.get('confidence') is not None]
    
    # Correlaciones
    sentiment_ndi_corr = 0
    if len(sentiment_values) > 1 and len(ndi_values) > 1 and len(sentiment_values) == len(ndi_values):
        sentiment_ndi_corr = float(np.corrcoef(sentiment_values, ndi_values)[0, 1])
    
    momentum_ndi_corr = 0
    if len(momentum_values) > 1 and len(ndi_values) > 1 and len(momentum_values) == len(ndi_values):
        momentum_ndi_corr = float(np.corrcoef(momentum_values, ndi_values)[0, 1])
    
    # Regímenes
    regime_counts = {
        'NEUTRAL': len([r for r in results if r.get('regime') == 'NEUTRAL']),
        'ALIGNED': len([r for r in results if r.get('regime') == 'ALIGNED']),
        'WATCHING': len([r for r in results if r.get('regime') == 'WATCHING']),
        'OVERHEATING': len([r for r in results if r.get('regime') == 'OVERHEATING']),
        'CAPITULATION': len([r for r in results if r.get('regime') == 'CAPITULATION'])
    }
    
    # Market alignment
    aligned = 0
    for r in results:
        s = r.get('sentiment', 0)
        m = r.get('momentum', 0)
        if (s > 0 and m > 0) or (s < 0 and m < 0):
            aligned += 1
    market_alignment = round((aligned / len(results)) * 100, 1) if results else 0
    
    metrics = {
        'ndi_mean': float(np.mean(ndi_values)) if ndi_values else 0,
        'ndi_std': float(np.std(ndi_values)) if ndi_values else 0,
        'ndi_range': float(np.max(ndi_values) - np.min(ndi_values)) if ndi_values else 0,
        'sentiment_ndi_corr': round(sentiment_ndi_corr, 4) if sentiment_ndi_corr else 0,
        'momentum_ndi_corr': round(momentum_ndi_corr, 4) if momentum_ndi_corr else 0,
        'confidence_mean': float(np.mean(confidence_values)) if confidence_values else 0,
        'regime_counts': regime_counts,
        'market_alignment': market_alignment
    }
    
    response = {
        'generated_at': datetime.now().isoformat(),
        'source': 'cache',
        'tickers': results,
        'metrics': metrics
    }
    
    # Reemplazar NaN por None (válido en JSON)
    for key, value in metrics.items():
        if isinstance(value, float) and np.isnan(value):
            metrics[key] = None
    
    set_cached(cache_key, response, 'metrics')
    logger.info(f"📊 /api/metrics: {len(results)} tickers procesados")
    return jsonify(response)
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    logger.info("=" * 50)
    logger.info("🚀 SignalIQ API v6.2 - Con price_history SIEMPRE")
    logger.info(f"📊 Puerto: {port}")
    logger.info(f"📊 Cache TTL: {CACHE_TTL}")
    logger.info(f"📊 Alpha Vantage: {'✅' if ALPHA_VANTAGE_API_KEY else '❌'}")
    logger.info(f"📊 Twelve Data: {'✅' if TWELVE_DATA_API_KEY else '❌'}")
    logger.info("=" * 50)
    app.run(host='0.0.0.0', port=port, debug=False)
