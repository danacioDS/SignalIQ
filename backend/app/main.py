"""SignalIQ API - Production (Sin Mocks)"""

import os
import json
import logging
import re as _re
import time
from datetime import datetime, timezone
from functools import wraps
from typing import Optional, List, Dict, Any, Tuple
import atexit
import yfinance as yf

from flask import Flask, request, jsonify, send_from_directory, g
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import google.generativeai as genai
import numpy as np
from psycopg2 import sql
from psycopg2.extras import RealDictCursor

from app.auth import require_api_key, require_api_key_optional
from app.db import init_pool, close_pool, execute_query_one, get_connection, put_connection
from app.llm_service import llm_service
from app.market_intelligence import market_intel_bp
from app.scoring.signal_score import SignalIQScore
from app.classification.event_classifier import EventClassifier

# ============================================================
# CONFIGURACIÓN DESDE ENTORNO
# ============================================================

class Config:
    """Configuración dinámica desde variables de entorno"""
    
    # Database
    DATABASE_URL = os.environ.get('DATABASE_URL')
    
    # API Keys
    GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')
    GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
    
    # Redis para rate limiting
    REDIS_URL = os.environ.get('REDIS_URL', 'memory://')
    
    # CORS - Configurable desde entorno
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '').split(',') if os.environ.get('CORS_ORIGINS') else [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://signaliq-zeta-ten.vercel.app",
        "https://signaliq-zeta.vercel.app",
        "https://signaliq-l8mi.onrender.com",
        "http://localhost:10000",
        "http://127.0.0.1:10000"
    ]
    
    # Features
    USE_JSON_LOGS = os.environ.get('USE_JSON_LOGS', 'true').lower() == 'true'
    DEBUG = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    
    # Limits
    MAX_TICKER_LEN = int(os.environ.get('MAX_TICKER_LEN', 10))
    MAX_TEXT_LEN = int(os.environ.get('MAX_TEXT_LEN', 10000))
    TICKER_REGEX = _re.compile(os.environ.get('TICKER_REGEX', r"^[A-Z0-9-]{1,10}$"))
    
    # NDI Constants
    NDI_CLAMP_MIN = float(os.environ.get('NDI_CLAMP_MIN', -3.0))
    NDI_CLAMP_MAX = float(os.environ.get('NDI_CLAMP_MAX', 3.0))
    CONFIDENCE_MIN = float(os.environ.get('CONFIDENCE_MIN', 10.0))
    CONFIDENCE_MAX = float(os.environ.get('CONFIDENCE_MAX', 95.0))
    
    # Server
    PORT = int(os.environ.get("PORT", 10000))
    HOST = os.environ.get("HOST", "0.0.0.0")
    
    # Static files
    STATIC_DIR = os.environ.get('STATIC_DIR', os.path.join(os.path.dirname(os.path.dirname(__file__)), "static"))
    
    # Rate Limits - Configurable desde entorno
    RATE_LIMITS = {
        'default': os.environ.get('RATE_LIMIT_DEFAULT', "200 per day,50 per hour").split(','),
        'prices': os.environ.get('RATE_LIMIT_PRICES', "10 per minute"),
        'signals': os.environ.get('RATE_LIMIT_SIGNALS', "30 per minute"),
        'analyze': os.environ.get('RATE_LIMIT_ANALYZE', "10 per minute"),
        'classify': os.environ.get('RATE_LIMIT_CLASSIFY', "30 per minute")
    }
    
    # Gemini Model
    GEMINI_MODEL = os.environ.get('GEMINI_MODEL', "gemini-2.0-flash")
    
    # Swagger
    SWAGGER_URL = os.environ.get('SWAGGER_URL', '/api/docs')
    SWAGGER_FILE = os.environ.get('SWAGGER_FILE', '/static/swagger.json')
    
    # Database retry
    DB_MAX_RETRIES = int(os.environ.get('DB_MAX_RETRIES', 3))
    DB_RETRY_DELAY = float(os.environ.get('DB_RETRY_DELAY', 0.5))
    
    # Price history limit
    PRICE_HISTORY_LIMIT = int(os.environ.get('PRICE_HISTORY_LIMIT', 60))
    MOMENTUM_PERIOD = int(os.environ.get('MOMENTUM_PERIOD', 20))
    
    # Default tickers
    DEFAULT_TICKERS = os.environ.get('DEFAULT_TICKERS', 'NVDA,AAPL,MSFT,TSLA,GOOGL,META,AMD,AMZN,JPM,KO')
    
    # App info
    APP_NAME = os.environ.get('APP_NAME', 'SignalIQ')
    APP_VERSION = os.environ.get('APP_VERSION', '2026-07-07')
    APP_BUILD = os.environ.get('APP_BUILD', 'yfinance_only')
    APP_ENV = os.environ.get('APP_ENV', 'production')
    APP_MODE = os.environ.get('APP_MODE', 'REAL')

# ============================================================
# LOGGING ESTRUCTURADO
# ============================================================

class JSONFormatter(logging.Formatter):
    """Formatter para logs en formato JSON"""
    def format(self, record):
        return json.dumps({
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'level': record.levelname,
            'name': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        })

def setup_logging():
    """Configura el sistema de logging dinámicamente"""
    logger = logging.getLogger(__name__)
    handler = logging.StreamHandler()
    
    if Config.USE_JSON_LOGS:
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(logging.Formatter(
            os.environ.get('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ))
    
    logger.addHandler(handler)
    logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))
    return logger

logger = setup_logging()

def log_info(msg: str, **kwargs):
    """Log informativo con soporte para JSON"""
    if Config.USE_JSON_LOGS:
        logger.info(msg, extra=kwargs)
    else:
        logger.info(f"{msg} {kwargs if kwargs else ''}")

def log_error(msg: str, **kwargs):
    """Log de error con soporte para JSON"""
    if Config.USE_JSON_LOGS:
        logger.error(msg, extra=kwargs)
    else:
        logger.error(f"{msg} {kwargs if kwargs else ''}")

def log_debug(msg: str, **kwargs):
    """Log de debug con soporte para JSON"""
    if Config.USE_JSON_LOGS:
        logger.debug(msg, extra=kwargs)
    else:
        logger.debug(f"{msg} {kwargs if kwargs else ''}")

# ============================================================
# VALIDACIÓN DE CONFIGURACIÓN
# ============================================================

def validate_config():
    """Valida que todas las variables de entorno necesarias estén configuradas"""
    errors = []
    
    if not Config.DATABASE_URL:
        errors.append("DATABASE_URL environment variable is required")
    
    if not Config.GOOGLE_API_KEY:
        errors.append("GOOGLE_API_KEY environment variable is required")
    
    if errors:
        for error in errors:
            log_error(error)
        raise ValueError("Configuration validation failed: " + "; ".join(errors))
    
    log_info("Configuration validated successfully", env=Config.APP_ENV)

# ============================================================
# UTILIDADES
# ============================================================

def retry_db_operation(max_retries: Optional[int] = None, delay: Optional[float] = None):
    """Decorator para reintentar operaciones de base de datos"""
    max_retries = max_retries or Config.DB_MAX_RETRIES
    delay = delay or Config.DB_RETRY_DELAY
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        log_debug(f"Database operation retry {attempt + 1}/{max_retries}", 
                                 error=str(e))
                        time.sleep(delay * (attempt + 1))
                        continue
                    raise
            raise last_exception
        return wrapper
    return decorator

def calculate_ndi(closes: List[float]) -> Tuple[float, float, float]:
    """Calcula el NDI (Normalized Divergence Index)"""
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
    
    momentum_period = Config.MOMENTUM_PERIOD
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
    ndi = max(Config.NDI_CLAMP_MIN, min(Config.NDI_CLAMP_MAX, ndi))
    
    return ndi, sentiment_zscore, momentum_zscore

def classify_regime(ndi: float) -> Dict[str, str]:
    """Clasifica el régimen basado en el NDI usando umbrales configurables"""
    thresholds = {
        'extreme_overheating': float(os.environ.get('THRESHOLD_EXTREME_OVERHEATING', 2.0)),
        'overheating': float(os.environ.get('THRESHOLD_OVERHEATING', 1.5)),
        'watching': float(os.environ.get('THRESHOLD_WATCHING', 0.5)),
        'stable': float(os.environ.get('THRESHOLD_STABLE', -0.5)),
        'aligned': float(os.environ.get('THRESHOLD_ALIGNED', -1.5)),
        'strong_undervalued': float(os.environ.get('THRESHOLD_STRONG_UNDERVALUED', -2.0))
    }
    
    if ndi > thresholds['extreme_overheating']:
        return {
            'regime': os.environ.get('REGIME_EXTREME_OVERHEATING', 'Extreme Overheating'),
            'color': os.environ.get('COLOR_EXTREME_OVERHEATING', 'red'),
            'code': os.environ.get('CODE_EXTREME_OVERHEATING', 'EXTREME_OVERHEATING'),
            'recommendation': os.environ.get('REC_EXTREME_OVERHEATING', 'SELL')
        }
    elif ndi > thresholds['overheating']:
        return {
            'regime': os.environ.get('REGIME_OVERHEATING', 'Overheating'),
            'color': os.environ.get('COLOR_OVERHEATING', 'orange'),
            'code': os.environ.get('CODE_OVERHEATING', 'OVERHEATING'),
            'recommendation': os.environ.get('REC_OVERHEATING', 'REDUCE')
        }
    elif ndi > thresholds['watching']:
        return {
            'regime': os.environ.get('REGIME_WATCHING', 'Watching'),
            'color': os.environ.get('COLOR_WATCHING', 'yellow'),
            'code': os.environ.get('CODE_WATCHING', 'WATCHING'),
            'recommendation': os.environ.get('REC_WATCHING', 'MONITOR')
        }
    elif ndi > thresholds['stable']:
        return {
            'regime': os.environ.get('REGIME_STABLE', 'Stable'),
            'color': os.environ.get('COLOR_STABLE', 'green'),
            'code': os.environ.get('CODE_STABLE', 'STABLE'),
            'recommendation': os.environ.get('REC_STABLE', 'HOLD')
        }
    elif ndi > thresholds['aligned']:
        return {
            'regime': os.environ.get('REGIME_ALIGNED', 'Aligned'),
            'color': os.environ.get('COLOR_ALIGNED', 'green'),
            'code': os.environ.get('CODE_ALIGNED', 'ALIGNED'),
            'recommendation': os.environ.get('REC_ALIGNED', 'BUY')
        }
    else:
        return {
            'regime': os.environ.get('REGIME_STRONG_UNDERVALUED', 'Strong Undervalued'),
            'color': os.environ.get('COLOR_STRONG_UNDERVALUED', 'darkgreen'),
            'code': os.environ.get('CODE_STRONG_UNDERVALUED', 'STRONG_UNDERVALUED'),
            'recommendation': os.environ.get('REC_STRONG_UNDERVALUED', 'STRONG_BUY')
        }

def validate_ticker(ticker: str) -> bool:
    """Valida un ticker contra la expresión regular configurada"""
    return bool(Config.TICKER_REGEX.match(ticker))

def get_price_history(ticker: str, limit: Optional[int] = None) -> Optional[List[float]]:
    """Obtiene el historial de precios de yfinance"""
    try:
        limit = limit or Config.PRICE_HISTORY_LIMIT
        stock = yf.Ticker(ticker)
        hist = stock.history(period=f"{limit}d")
        
        if hist.empty:
            log_error(f"No price data found for {ticker}")
            return None
        
        closes = hist['Close'].tolist()
        return closes[-limit:] if len(closes) > limit else closes
    except Exception as e:
        log_error(f"Error fetching price history for {ticker}", error=str(e))
        return None

def get_ticker_info(ticker: str) -> Optional[Dict[str, Any]]:
    """Obtiene información del ticker de yfinance"""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        return info
    except Exception as e:
        log_error(f"Error fetching ticker info for {ticker}", error=str(e))
        return None

# ============================================================
# INICIALIZACIÓN DE FLASK
# ============================================================

app = Flask(__name__, static_folder=Config.STATIC_DIR)

# Configuración de CORS
CORS(app, origins=Config.CORS_ORIGINS)

# Configuración de Rate Limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=Config.RATE_LIMITS['default'],
    storage_uri=Config.REDIS_URL
)

# Configuración de Gemini
genai.configure(api_key=Config.GOOGLE_API_KEY)

# Inicializar servicios
signal_score = SignalIQScore()
event_classifier = EventClassifier()

# ============================================================
# MIDDLEWARE Y HOOKS
# ============================================================

@app.before_request
def before_request():
    """Hook ejecutado antes de cada request"""
    g.start_time = time.time()
    g.request_id = f"{int(time.time() * 1000)}-{os.urandom(4).hex()}"

@app.after_request
def after_request(response):
    """Hook ejecutado después de cada request"""
    if hasattr(g, 'start_time'):
        elapsed = time.time() - g.start_time
        log_info("Request completed", 
                path=request.path,
                method=request.method,
                status=response.status_code,
                elapsed_ms=round(elapsed * 1000, 2),
                request_id=getattr(g, 'request_id', None))
    return response

@app.errorhandler(404)
def not_found(error):
    """Manejo de error 404"""
    return jsonify({
        'error': 'Resource not found',
        'status': 404,
        'timestamp': datetime.now(timezone.utc).isoformat()
    }), 404

@app.errorhandler(429)
def rate_limit_handler(error):
    """Manejo de error 429 (Rate Limit)"""
    return jsonify({
        'error': 'Rate limit exceeded',
        'message': 'Please slow down your requests',
        'status': 429,
        'timestamp': datetime.now(timezone.utc).isoformat()
    }), 429

@app.errorhandler(500)
def internal_error(error):
    """Manejo de error 500"""
    log_error("Internal server error", error=str(error))
    return jsonify({
        'error': 'Internal server error',
        'status': 500,
        'timestamp': datetime.now(timezone.utc).isoformat()
    }), 500

# ============================================================
# RUTAS DE LA API
# ============================================================

@app.route('/', methods=['GET'])
def root():
    """Endpoint raíz con información de la API"""
    return jsonify({
        'name': Config.APP_NAME,
        'version': Config.APP_VERSION,
        'build': Config.APP_BUILD,
        'environment': Config.APP_ENV,
        'mode': Config.APP_MODE,
        'status': 'operational',
        'endpoints': [
            '/health',
            '/api/prices',
            '/api/signals',
            '/api/analyze',
            '/api/classify',
            '/api/regimes',
            '/api/tickers',
            '/api/ticker-info',
            '/api/market-intelligence'
        ]
    })

@app.route('/health', methods=['GET'])
def health():
    """Endpoint de salud para monitoreo"""
    db_status = 'disconnected'
    try:
        # Verificar conexión a la base de datos
        conn = get_connection()
        if conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
            db_status = 'connected'
            put_connection(conn)
    except Exception as e:
        log_error("Health check database error", error=str(e))
        db_status = 'error'
    
    return jsonify({
        'status': 'healthy' if db_status == 'connected' else 'degraded',
        'version': Config.APP_VERSION,
        'database': db_status,
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'uptime': time.time() - app.start_time if hasattr(app, 'start_time') else 0
    })

@app.route('/api/prices', methods=['GET'])
@limiter.limit(Config.RATE_LIMITS['prices'])
@require_api_key_optional
def get_prices():
    """Obtiene precios históricos para uno o más tickers"""
    tickers_param = request.args.get('tickers', '')
    limit = request.args.get('limit', Config.PRICE_HISTORY_LIMIT, type=int)
    
    if not tickers_param:
        return jsonify({
            'error': 'Missing tickers parameter',
            'example': '/api/prices?tickers=NVDA,AAPL&limit=30'
        }), 400
    
    tickers = [t.strip().upper() for t in tickers_param.split(',') if t.strip()]
    
    if not tickers:
        return jsonify({'error': 'No valid tickers provided'}), 400
    
    # Validar tickers
    invalid_tickers = [t for t in tickers if not validate_ticker(t)]
    if invalid_tickers:
        return jsonify({
            'error': 'Invalid ticker format',
            'invalid_tickers': invalid_tickers,
            'max_length': Config.MAX_TICKER_LEN
        }), 400
    
    results = {}
    for ticker in tickers:
        prices = get_price_history(ticker, limit)
        if prices:
            results[ticker] = {
                'prices': prices,
                'count': len(prices),
                'latest': prices[-1] if prices else None
            }
        else:
            results[ticker] = {'error': 'No data available'}
    
    return jsonify({
        'tickers': results,
        'limit': limit,
        'timestamp': datetime.now(timezone.utc).isoformat()
    })

@app.route('/api/signals', methods=['GET'])
@limiter.limit(Config.RATE_LIMITS['signals'])
@require_api_key_optional
def get_signals():
    """Obtiene señales NDI para uno o más tickers"""
    tickers_param = request.args.get('tickers', '')
    limit = request.args.get('limit', Config.PRICE_HISTORY_LIMIT, type=int)
    
    if not tickers_param:
        return jsonify({
            'error': 'Missing tickers parameter',
            'example': '/api/signals?tickers=NVDA,AAPL&limit=30'
        }), 400
    
    tickers = [t.strip().upper() for t in tickers_param.split(',') if t.strip()]
    
    if not tickers:
        return jsonify({'error': 'No valid tickers provided'}), 400
    
    invalid_tickers = [t for t in tickers if not validate_ticker(t)]
    if invalid_tickers:
        return jsonify({
            'error': 'Invalid ticker format',
            'invalid_tickers': invalid_tickers,
            'max_length': Config.MAX_TICKER_LEN
        }), 400
    
    results = {}
    for ticker in tickers:
        prices = get_price_history(ticker, limit)
        if prices and len(prices) >= 2:
            ndi, sentiment, momentum = calculate_ndi(prices)
            regime = classify_regime(ndi)
            
            results[ticker] = {
                'ndi': round(ndi, 4),
                'sentiment_zscore': round(sentiment, 4),
                'momentum_zscore': round(momentum, 4),
                'regime': regime,
                'latest_price': prices[-1],
                'price_count': len(prices)
            }
        else:
            results[ticker] = {'error': 'Insufficient price data'}
    
    return jsonify({
        'tickers': results,
        'timestamp': datetime.now(timezone.utc).isoformat()
    })

@app.route('/api/analyze', methods=['POST'])
@limiter.limit(Config.RATE_LIMITS['analyze'])
@require_api_key
def analyze_text():
    """Analiza texto usando Gemini AI"""
    data = request.json
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    text = data.get('text', '')
    ticker = data.get('ticker', '').upper()
    
    if not text:
        return jsonify({'error': 'Text is required'}), 400
    
    if len(text) > Config.MAX_TEXT_LEN:
        return jsonify({
            'error': f'Text too long. Maximum length is {Config.MAX_TEXT_LEN} characters'
        }), 400
    
    if ticker and not validate_ticker(ticker):
        return jsonify({
            'error': 'Invalid ticker format',
            'max_length': Config.MAX_TICKER_LEN
        }), 400
    
    try:
        # Usar el servicio LLM
        analysis = llm_service.analyze_sentiment(text, ticker)
        
        # Clasificar el evento
        event_type = event_classifier.classify(text)
        
        return jsonify({
            'analysis': analysis,
            'event_type': event_type,
            'ticker': ticker if ticker else None,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
    except Exception as e:
        log_error("Error analyzing text", error=str(e))
        return jsonify({'error': 'Analysis failed', 'details': str(e)}), 500

@app.route('/api/classify', methods=['POST'])
@limiter.limit(Config.RATE_LIMITS['classify'])
@require_api_key_optional
def classify_event():
    """Clasifica un evento textual"""
    data = request.json
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    text = data.get('text', '')
    ticker = data.get('ticker', '').upper()
    
    if not text:
        return jsonify({'error': 'Text is required'}), 400
    
    if len(text) > Config.MAX_TEXT_LEN:
        return jsonify({
            'error': f'Text too long. Maximum length is {Config.MAX_TEXT_LEN} characters'
        }), 400
    
    try:
        classification = event_classifier.classify(text)
        
        return jsonify({
            'classification': classification,
            'ticker': ticker if ticker else None,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
    except Exception as e:
        log_error("Error classifying event", error=str(e))
        return jsonify({'error': 'Classification failed', 'details': str(e)}), 500

@app.route('/api/regimes', methods=['GET'])
@require_api_key_optional
def get_regimes():
    """Obtiene la definición de todos los regímenes posibles"""
    regimes = []
    ndi_values = [-2.5, -1.8, -1.0, 0.0, 1.0, 1.8, 2.5]
    
    for ndi in ndi_values:
        regime = classify_regime(ndi)
        regime['ndi_example'] = ndi
        regimes.append(regime)
    
    return jsonify({
        'regimes': regimes,
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'description': 'Regime classification based on NDI (Normalized Divergence Index)'
    })

@app.route('/api/tickers', methods=['GET'])
@require_api_key_optional
def get_tickers():
    """Obtiene la lista de tickers predeterminados o busca tickers"""
    query = request.args.get('q', '')
    
    if query:
        # Búsqueda de tickers (simplificada)
        default_tickers = Config.DEFAULT_TICKERS.split(',')
        matches = [t for t in default_tickers if query.upper() in t]
        
        if not matches:
            # Intentar buscar en yfinance
            try:
                stock = yf.Ticker(query.upper())
                info = stock.info
                if info.get('symbol'):
                    matches = [info['symbol']]
            except:
                matches = []
        
        return jsonify({
            'results': matches,
            'query': query,
            'count': len(matches)
        })
    
    # Devolver tickers predeterminados
    default_tickers = Config.DEFAULT_TICKERS.split(',')
    return jsonify({
        'tickers': default_tickers,
        'count': len(default_tickers),
        'description': 'Default tickers'
    })

@app.route('/api/ticker-info', methods=['GET'])
@require_api_key_optional
def get_ticker_info_endpoint():
    """Obtiene información detallada de un ticker"""
    ticker = request.args.get('ticker', '').upper()
    
    if not ticker:
        return jsonify({'error': 'Ticker parameter is required'}), 400
    
    if not validate_ticker(ticker):
        return jsonify({
            'error': 'Invalid ticker format',
            'max_length': Config.MAX_TICKER_LEN
        }), 400
    
    info = get_ticker_info(ticker)
    if not info:
        return jsonify({'error': f'No information found for {ticker}'}), 404
    
    # Extraer información relevante
    relevant_info = {
        'symbol': info.get('symbol', ticker),
        'name': info.get('longName', info.get('shortName', 'N/A')),
        'sector': info.get('sector', 'N/A'),
        'industry': info.get('industry', 'N/A'),
        'market_cap': info.get('marketCap', 'N/A'),
        'pe_ratio': info.get('trailingPE', 'N/A'),
        'dividend_yield': info.get('dividendYield', 'N/A'),
        'beta': info.get('beta', 'N/A'),
        'fifty_two_week_high': info.get('fiftyTwoWeekHigh', 'N/A'),
        'fifty_two_week_low': info.get('fiftyTwoWeekLow', 'N/A'),
        'currency': info.get('currency', 'USD')
    }
    
    return jsonify({
        'ticker': ticker,
        'info': relevant_info,
        'timestamp': datetime.now(timezone.utc).isoformat()
    })

@app.route('/api/market-intelligence', methods=['GET'])
@limiter.limit("5 per minute")
@require_api_key_optional
def get_market_intelligence():
    """Obtiene inteligencia de mercado para un sector o ticker"""
    sector = request.args.get('sector', 'technology')
    ticker = request.args.get('ticker', '').upper()
    
    if ticker and not validate_ticker(ticker):
        return jsonify({
            'error': 'Invalid ticker format',
            'max_length': Config.MAX_TICKER_LEN
        }), 400
    
    try:
        # Obtener precios para análisis
        if ticker:
            prices = get_price_history(ticker, 30)
            if prices and len(prices) >= 2:
                ndi, sentiment, momentum = calculate_ndi(prices)
                regime = classify_regime(ndi)
            else:
                ndi = sentiment = momentum = 0
                regime = classify_regime(0)
        else:
            ndi = sentiment = momentum = 0
            regime = classify_regime(0)
        
        # Generar resumen usando LLM
        summary = llm_service.generate_market_summary(sector, ticker)
        
        return jsonify({
            'sector': sector,
            'ticker': ticker if ticker else None,
            'market_regime': regime,
            'ndi': round(ndi, 4) if ticker else None,
            'summary': summary,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
    except Exception as e:
        log_error("Error getting market intelligence", error=str(e))
        return jsonify({'error': 'Failed to get market intelligence', 'details': str(e)}), 500

@app.route('/api/market-intelligence/trends', methods=['GET'])
@limiter.limit("5 per minute")
@require_api_key_optional
def get_market_trends():
    """Obtiene tendencias del mercado basadas en indicadores"""
    try:
        # Obtener datos de tickers principales
        default_tickers = Config.DEFAULT_TICKERS.split(',')[:5]
        trends = {}
        
        for ticker in default_tickers:
            prices = get_price_history(ticker, 30)
            if prices and len(prices) >= 2:
                ndi, sentiment, momentum = calculate_ndi(prices)
                regime = classify_regime(ndi)
                trends[ticker] = {
                    'ndi': round(ndi, 4),
                    'regime': regime['regime'],
                    'recommendation': regime['recommendation'],
                    'color': regime['color']
                }
        
        # Calcular tendencia general
        ndi_values = [t['ndi'] for t in trends.values() if 'ndi' in t]
        avg_ndi = np.mean(ndi_values) if ndi_values else 0
        overall_regime = classify_regime(avg_ndi)
        
        return jsonify({
            'overall_regime': overall_regime,
            'avg_ndi': round(avg_ndi, 4),
            'tickers': trends,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
    except Exception as e:
        log_error("Error getting market trends", error=str(e))
        return jsonify({'error': 'Failed to get market trends', 'details': str(e)}), 500

# ============================================================
# REGISTRO DE BLUEPRINTS
# ============================================================

# Registrar blueprint de market intelligence
app.register_blueprint(market_intel_bp, url_prefix='/api/market-intelligence')

# ============================================================
# INICIALIZACIÓN Y CIERRE
# ============================================================

@app.before_first_request
def initialize_app():
    """Inicializa la aplicación antes del primer request"""
    try:
        # Validar configuración
        validate_config()
        
        # Inicializar pool de conexiones
        if Config.DATABASE_URL:
            init_pool(Config.DATABASE_URL)
            log_info("Database connection pool initialized")
        
        # Configurar Gemini
        if Config.GOOGLE_API_KEY:
            genai.configure(api_key=Config.GOOGLE_API_KEY)
            log_info("Gemini API configured")
        
        # Guardar tiempo de inicio
        app.start_time = time.time()
        
        log_info(f"Application initialized: {Config.APP_NAME} v{Config.APP_VERSION}")
    except Exception as e:
        log_error("Failed to initialize application", error=str(e))
        raise

@atexit.register
def shutdown():
    """Limpieza al cerrar la aplicación"""
    try:
        close_pool()
        log_info("Database connection pool closed")
    except Exception as e:
        log_error("Error closing database pool", error=str(e))
    
    log_info(f"Application {Config.APP_NAME} shutdown complete")

# ============================================================
# PUNTO DE ENTRADA
# ============================================================

if __name__ == '__main__':
    try:
        # Validar configuración antes de iniciar
        validate_config()
        
        # Inicializar pool de conexiones
        if Config.DATABASE_URL:
            init_pool(Config.DATABASE_URL)
        
        # Iniciar servidor
        log_info(f"Starting {Config.APP_NAME} v{Config.APP_VERSION}")
        log_info(f"Environment: {Config.APP_ENV}")
        log_info(f"Mode: {Config.APP_MODE}")
        log_info(f"Server running on {Config.HOST}:{Config.PORT}")
        
        app.run(
            host=Config.HOST,
            port=Config.PORT,
            debug=Config.DEBUG,
            threaded=True
        )
    except Exception as e:
        log_error("Failed to start application", error=str(e))
        raise