"""
SignalIQ API - Con noticias reales
Versión: 8.1 - Con endpoint /api/ticker/<ticker>
"""
import os
import sys
import logging
import uuid
import json
import time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from threading import Lock, Semaphore
from functools import wraps
from typing import Optional, Dict, List, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

from flask import Flask, jsonify, request, g
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
import yfinance as yf
import numpy as np
import requests
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed

# ============================================================
# CONFIGURACIÓN CENTRALIZADA
# ============================================================
class Config:
    """Configuración centralizada de la aplicación"""
    ENV = os.environ.get('ENV', 'production')
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    # Caché - TTL en segundos
    CACHE_TTL = {
        'signal': 60,
        'price': 30,
        'history': 300,
        'history_full': 300,
        'news': 300,
        'health': 60,
        'ticker': 60  # Nuevo TTL para ticker individual
    }
    
    # Threads y concurrencia
    MAX_WORKERS = int(os.environ.get('MAX_TICKER_THREADS', 2))
    MAX_TICKERS = 10
    API_SEMAPHORE = 3
    
    # APIs
    TWELVE_DATA_API_KEY = os.environ.get('TWELVE_DATA_API_KEY', '')
    ALPHA_VANTAGE_API_KEY = os.environ.get('ALPHA_VANTAGE_API_KEY', '')
    REDIS_URL = os.environ.get('REDIS_URL', '')
    
    # CORS
    CORS_ORIGINS = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://signaliq-zeta-ten.vercel.app",
        "https://signaliq-zeta.vercel.app",
        "https://signaliq-l8mi.onrender.com",
        "https://signaliq-api.onrender.com"
    ]
    
    # Timeouts y retries
    REQUEST_TIMEOUT = 10
    MAX_RETRIES = 3
    RETRY_DELAY = 1
    
    # Rate limiting
    RATE_LIMIT = "30 per minute"
    RATE_LIMIT_ANALYSIS = "10 per minute"
    
    # Circuit Breaker
    CIRCUIT_BREAKER_THRESHOLD = 5
    CIRCUIT_BREAKER_TIMEOUT = 60


# ============================================================
# CIRCUIT BREAKER
# ============================================================
class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """Circuit Breaker para APIs externas"""
    
    def __init__(self, name: str, threshold: int = 5, timeout: int = 60):
        self.name = name
        self.threshold = threshold
        self.timeout = timeout
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self._lock = Lock()
    
    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with self._lock:
                if self.state == CircuitState.OPEN:
                    if time.time() - self.last_failure_time > self.timeout:
                        self.state = CircuitState.HALF_OPEN
                        logger.info(f"🔌 Circuit Breaker {self.name}: HALF_OPEN")
                    else:
                        logger.warning(f"🔌 Circuit Breaker {self.name}: OPEN - saltando llamada")
                        return None
                
                try:
                    result = func(*args, **kwargs)
                    if result is not None:
                        if self.state == CircuitState.HALF_OPEN:
                            self.state = CircuitState.CLOSED
                            self.failure_count = 0
                            logger.info(f"🔌 Circuit Breaker {self.name}: CLOSED (éxito en half-open)")
                        return result
                    else:
                        self._record_failure()
                        return None
                except Exception as e:
                    self._record_failure()
                    raise e
        
        return wrapper
    
    def _record_failure(self):
        with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            if self.failure_count >= self.threshold:
                self.state = CircuitState.OPEN
                logger.warning(f"🔌 Circuit Breaker {self.name}: OPEN (fallos: {self.failure_count})")


# ============================================================
# INSTANCIAS DE CIRCUIT BREAKER
# ============================================================
cb_twelvedata = CircuitBreaker("twelvedata", threshold=5, timeout=60)
cb_alphavantage = CircuitBreaker("alphavantage", threshold=5, timeout=60)
cb_news = CircuitBreaker("news_pipeline", threshold=3, timeout=30)


# ============================================================
# SEMÁFORO PARA CONTROL DE CONCURRENCIA
# ============================================================
_api_semaphore = Semaphore(Config.API_SEMAPHORE)


def with_semaphore(func):
    """Decorador para limitar llamadas simultáneas a APIs externas"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        with _api_semaphore:
            return func(*args, **kwargs)
    return wrapper


# ============================================================
# REQUEST ID PARA TRAZABILIDAD
# ============================================================
def get_request_id():
    """Obtener o generar un ID único para la request"""
    try:
        if not hasattr(g, 'request_id'):
            g.request_id = str(uuid.uuid4())[:8]
        return g.request_id
    except RuntimeError:
        return "system"


# ============================================================
# LOGGING CON REQUEST ID
# ============================================================
class RequestIdFilter(logging.Filter):
    def filter(self, record):
        try:
            record.request_id = getattr(g, 'request_id', 'unknown')
        except RuntimeError:
            record.request_id = 'system'
        return True


logging.basicConfig(
    level=logging.INFO,
    format='[%(request_id)s] %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)
logger.addFilter(RequestIdFilter())


# ============================================================
# RETRY DECORATOR CON BACKOFF EXPONENCIAL
# ============================================================
def retry(max_retries=3, delay=1, exponential=True):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    result = func(*args, **kwargs)
                    if result is not None:
                        return result
                    if attempt < max_retries - 1:
                        wait_time = delay * (2 ** attempt) if exponential else delay * (attempt + 1)
                        logger.info(f"⏳ Reintento {attempt + 1}/{max_retries} en {wait_time}s")
                        time.sleep(wait_time)
                        continue
                except requests.exceptions.RequestException as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        wait_time = delay * (2 ** attempt) if exponential else delay * (attempt + 1)
                        logger.warning(f"⏳ Error, reintento {attempt + 1}/{max_retries} en {wait_time}s: {str(e)}")
                        time.sleep(wait_time)
                        continue
                    raise
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        wait_time = delay * (2 ** attempt) if exponential else delay * (attempt + 1)
                        time.sleep(wait_time)
                        continue
                    raise
            return None
        return wrapper
    return decorator


# ============================================================
# MÉTRICAS BÁSICAS
# ============================================================
@dataclass
class Metrics:
    request_id: str
    endpoint: str
    start_time: float
    end_time: float = 0.0
    duration_ms: float = 0.0
    cache_hit: bool = False
    api_calls: int = 0
    status_code: int = 200
    
    def finish(self, status_code: int = 200):
        self.end_time = time.time()
        self.duration_ms = (self.end_time - self.start_time) * 1000
        self.status_code = status_code


# ============================================================
# CACHÉ THREAD-SAFE
# ============================================================
_cache = {
    'signal': {},
    'price': {},
    'history': {},
    'history_full': {},
    'news': {},
    'health': {},
    'ticker': {}  # Nuevo caché para ticker
}
_cache_timestamps = {
    'signal': {},
    'price': {},
    'history': {},
    'history_full': {},
    'news': {},
    'health': {},
    'ticker': {}
}
_cache_lock = Lock()

_redis_client = None
if Config.REDIS_URL:
    try:
        import redis
        _redis_client = redis.from_url(Config.REDIS_URL, decode_responses=True)
        logger.info("✅ Redis conectado correctamente")
    except Exception as e:
        logger.warning(f"⚠️ Redis no disponible: {str(e)}")


def get_cache_key(prefix: str, *args) -> str:
    key_parts = [prefix] + [str(a) for a in args]
    return hashlib.md5('_'.join(key_parts).encode()).hexdigest()


def get_from_cache(cache_type: str, key: str):
    if _redis_client:
        try:
            value = _redis_client.get(f"{cache_type}:{key}")
            if value:
                return json.loads(value)
        except Exception as e:
            logger.warning(f"⚠️ Redis get error: {str(e)}")
    
    with _cache_lock:
        if cache_type not in _cache:
            return None
        
        now = datetime.now()
        if key in _cache[cache_type] and key in _cache_timestamps[cache_type]:
            elapsed = (now - _cache_timestamps[cache_type][key]).total_seconds()
            if elapsed < Config.CACHE_TTL.get(cache_type, 60):
                return _cache[cache_type][key]
    return None


def set_in_cache(cache_type: str, key: str, value):
    ttl = Config.CACHE_TTL.get(cache_type, 60)
    
    if _redis_client:
        try:
            _redis_client.setex(f"{cache_type}:{key}", ttl, json.dumps(value))
        except Exception as e:
            logger.warning(f"⚠️ Redis set error: {str(e)}")
    
    with _cache_lock:
        if cache_type not in _cache:
            return
        _cache[cache_type][key] = value
        _cache_timestamps[cache_type][key] = datetime.now()


# ============================================================
# IMPORTACIÓN DE MÓDULOS PERSONALIZADOS
# ============================================================
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from yahoo_proxy import yahoo_proxy
except ImportError:
    logger.warning("⚠️ yahoo_proxy no encontrado")
    yahoo_proxy = None

try:
    from layers.layer4_measurement import calculate_narrative_divergence_index
except ImportError:
    logger.warning("⚠️ layer4_measurement no encontrado")
    def calculate_narrative_divergence_index(sentiment, momentum):
        return sentiment * 0.6 + momentum * 0.4

try:
    from news_pipeline import process_news_for_ticker
except ImportError:
    logger.warning("⚠️ news_pipeline no encontrado")
    def process_news_for_ticker(ticker):
        return {
            'headlines': [f"Noticias sobre {ticker}"],
            'scores': [0.2],
            'sentiment': 0.2,
            'count': 1
        }


# ============================================================
# CREAR APLICACIÓN FLASK
# ============================================================
app = Flask(__name__)

if yahoo_proxy:
    app.register_blueprint(yahoo_proxy)

# CORS
CORS(app, origins=Config.CORS_ORIGINS, supports_credentials=False)

# Talisman - Security Headers
Talisman(
    app,
    content_security_policy={
        'default-src': "'self'",
        'script-src': "'self'",
        'style-src': "'self'",
    },
    force_https=False,
    frame_options='DENY',
    referrer_policy='strict-origin-when-cross-origin'
)

# Rate Limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=[Config.RATE_LIMIT]
)


# ============================================================
# GLOBAL ERROR HANDLER
# ============================================================
@app.errorhandler(Exception)
def handle_error(e):
    logger.exception(f"Error no manejado: {str(e)}")
    return jsonify({
        'error': 'Internal server error',
        'request_id': get_request_id(),
        'timestamp': datetime.now(timezone.utc).isoformat()
    }), 500


# ============================================================
# REQUEST METRICS (MIDDLEWARE)
# ============================================================
@app.before_request
def before_request():
    g.start_time = time.time()
    g.metrics = Metrics(
        request_id=get_request_id(),
        endpoint=request.path,
        start_time=g.start_time
    )


@app.after_request
def after_request(response):
    if hasattr(g, 'metrics'):
        g.metrics.finish(response.status_code)
        logger.info(
            f"📊 {g.metrics.endpoint} | "
            f"{g.metrics.duration_ms:.0f}ms | "
            f"status={g.metrics.status_code} | "
            f"cache={g.metrics.cache_hit} | "
            f"api_calls={g.metrics.api_calls}"
        )
    return response


# ============================================================
# INFORMACIÓN DE EMPRESAS
# ============================================================
COMPANY_INFO = {
    "AAPL": {"company_name": "Apple Inc.", "sector": "Technology", "industry": "Consumer Electronics"},
    "MSFT": {"company_name": "Microsoft Corporation", "sector": "Technology", "industry": "Software"},
    "NVDA": {"company_name": "NVIDIA Corporation", "sector": "Technology", "industry": "Semiconductors"},
    "GOOGL": {"company_name": "Alphabet Inc.", "sector": "Technology", "industry": "Internet"},
    "META": {"company_name": "Meta Platforms Inc.", "sector": "Technology", "industry": "Internet"},
    "AMD": {"company_name": "Advanced Micro Devices Inc.", "sector": "Technology", "industry": "Semiconductors"},
    "AMZN": {"company_name": "Amazon.com Inc.", "sector": "Consumer", "industry": "E-commerce"},
    "TSLA": {"company_name": "Tesla Inc.", "sector": "Automotive", "industry": "Electric Vehicles"},
    "JPM": {"company_name": "JPMorgan Chase & Co.", "sector": "Financial", "industry": "Banking"},
    "KO": {"company_name": "The Coca-Cola Company", "sector": "Consumer", "industry": "Beverages"}
}

SUPPORTED_TICKERS = tuple(COMPANY_INFO.keys())
FINANCIAL_DISCLAIMER = "⚠️ SignalIQ proporciona señales analíticas. Esto NO es asesoramiento financiero."


def get_company_info(ticker):
    return COMPANY_INFO.get(ticker, {
        'company_name': ticker,
        'sector': 'Unknown',
        'industry': 'Unknown'
    })


def get_market_status():
    try:
        ny_time = datetime.now(ZoneInfo("America/New_York"))
        is_weekday = ny_time.weekday() < 5
        is_trading_hours = (ny_time.hour > 9 or (ny_time.hour == 9 and ny_time.minute >= 30)) and ny_time.hour < 16
        return "open" if (is_weekday and is_trading_hours) else "closed"
    except Exception as e:
        logger.warning(f"⚠️ Error obteniendo market status: {str(e)}")
        return "unknown"


# ============================================================
# HEALTH CHECK CON CACHÉ
# ============================================================
def check_services():
    cache_key = 'health_check'
    
    cached = get_from_cache('health', cache_key)
    if cached is not None:
        return cached
    
    services = {}
    
    if Config.TWELVE_DATA_API_KEY:
        try:
            url = f"https://api.twelvedata.com/price?symbol=AAPL&apikey={Config.TWELVE_DATA_API_KEY}"
            response = requests.get(url, timeout=3)
            services['twelvedata'] = 'ok' if response.status_code == 200 else 'error'
        except:
            services['twelvedata'] = 'error'
    else:
        services['twelvedata'] = 'not_configured'
    
    if Config.ALPHA_VANTAGE_API_KEY:
        try:
            url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=AAPL&apikey={Config.ALPHA_VANTAGE_API_KEY}"
            response = requests.get(url, timeout=3)
            services['alphavantage'] = 'ok' if response.status_code == 200 else 'error'
        except:
            services['alphavantage'] = 'error'
    else:
        services['alphavantage'] = 'not_configured'
    
    services['cache'] = 'ok'
    
    if _redis_client:
        try:
            _redis_client.ping()
            services['redis'] = 'ok'
        except:
            services['redis'] = 'error'
    else:
        services['redis'] = 'not_configured'
    
    try:
        from news_pipeline import process_news_for_ticker
        services['news_pipeline'] = 'configured'
    except:
        services['news_pipeline'] = 'not_configured'
    
    set_in_cache('health', cache_key, services)
    return services


# ============================================================
# FUNCIONES DE NOTICIAS
# ============================================================
@cb_news
def get_news(ticker):
    cache_key = get_cache_key('news', ticker)
    
    cached = get_from_cache('news', cache_key)
    if cached is not None:
        logger.info(f"📊 CACHÉ: Noticias para {ticker}")
        if hasattr(g, 'metrics'):
            g.metrics.cache_hit = True
        return cached
    
    logger.info(f"📊 Obteniendo noticias para {ticker}")
    news_data = process_news_for_ticker(ticker)
    
    if not news_data or 'sentiment' not in news_data:
        logger.warning(f"⚠️ Respuesta inválida de news_pipeline para {ticker}")
        return {'headlines': [], 'scores': [], 'sentiment': 0.0, 'count': 0}
    
    set_in_cache('news', cache_key, news_data)
    return news_data


# ============================================================
# FUNCIONES DE PRECIOS
# ============================================================
@with_semaphore
@retry(max_retries=Config.MAX_RETRIES, delay=Config.RETRY_DELAY, exponential=True)
@cb_twelvedata
def fetch_twelvedata_price(ticker):
    if not Config.TWELVE_DATA_API_KEY:
        return None
    
    url = f"https://api.twelvedata.com/price?symbol={ticker}&apikey={Config.TWELVE_DATA_API_KEY}"
    response = requests.get(url, timeout=Config.REQUEST_TIMEOUT)
    response.raise_for_status()
    
    data = response.json()
    
    if not data or 'price' not in data or data['price'] is None:
        logger.warning(f"⚠️ Twelve Data respuesta inválida para {ticker}: {data}")
        return None
    
    try:
        return float(data['price'])
    except (ValueError, TypeError):
        logger.warning(f"⚠️ Twelve Data precio inválido para {ticker}: {data.get('price')}")
        return None


@with_semaphore
@retry(max_retries=Config.MAX_RETRIES, delay=Config.RETRY_DELAY, exponential=True)
@cb_alphavantage
def fetch_alphavantage_price(ticker):
    if not Config.ALPHA_VANTAGE_API_KEY:
        return None
    
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={ticker}&apikey={Config.ALPHA_VANTAGE_API_KEY}"
    response = requests.get(url, timeout=Config.REQUEST_TIMEOUT)
    response.raise_for_status()
    
    data = response.json()
    
    if not data or 'Global Quote' not in data:
        return None
    
    quote = data['Global Quote']
    if '05. price' not in quote or quote['05. price'] is None:
        return None
    
    try:
        return float(quote['05. price'])
    except (ValueError, TypeError):
        return None


def fetch_yfinance_price(ticker):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="2d")
        if not hist.empty:
            return float(hist['Close'].iloc[-1])
    except Exception as e:
        logger.error(f"❌ yfinance error para {ticker}: {str(e)}")
    return None


def get_price(ticker):
    cache_key = get_cache_key('price', ticker)
    
    cached = get_from_cache('price', cache_key)
    if cached is not None:
        logger.info(f"📊 CACHÉ: Precio para {ticker}: ${cached}")
        if hasattr(g, 'metrics'):
            g.metrics.cache_hit = True
        return cached
    
    logger.info(f"🔍 Obteniendo precio para {ticker}")
    
    if hasattr(g, 'metrics'):
        g.metrics.api_calls += 1
    
    price = fetch_twelvedata_price(ticker)
    if price is not None:
        set_in_cache('price', cache_key, price)
        return price
    
    if hasattr(g, 'metrics'):
        g.metrics.api_calls += 1
    
    price = fetch_alphavantage_price(ticker)
    if price is not None:
        set_in_cache('price', cache_key, price)
        return price
    
    price = fetch_yfinance_price(ticker)
    if price is not None:
        set_in_cache('price', cache_key, price)
        return price
    
    logger.warning(f"❌ No se pudo obtener precio para {ticker} de ninguna fuente")
    return None


# ============================================================
# FUNCIONES DE HISTORIAL
# ============================================================
@with_semaphore
@retry(max_retries=Config.MAX_RETRIES, delay=Config.RETRY_DELAY, exponential=True)
@cb_twelvedata
def fetch_twelvedata_history_full(ticker, days=30):
    if not Config.TWELVE_DATA_API_KEY:
        return None
    
    url = f"https://api.twelvedata.com/time_series?symbol={ticker}&interval=1day&outputsize={days}&apikey={Config.TWELVE_DATA_API_KEY}"
    response = requests.get(url, timeout=Config.REQUEST_TIMEOUT)
    response.raise_for_status()
    
    data = response.json()
    
    if not data or 'values' not in data or not data['values']:
        logger.warning(f"⚠️ Twelve Data history inválida para {ticker}")
        return None
    
    history = []
    for item in data['values']:
        try:
            history.append({
                'date': item['datetime'][:10],
                'close': float(item['close'])
            })
        except (KeyError, ValueError, TypeError):
            continue
    
    if not history:
        return None
    
    history.reverse()
    logger.info(f"✅ Twelve Data: {len(history)} registros para {ticker}")
    return history


@with_semaphore
@retry(max_retries=Config.MAX_RETRIES, delay=Config.RETRY_DELAY, exponential=True)
@cb_alphavantage
def fetch_alphavantage_history_full(ticker, days=30):
    if not Config.ALPHA_VANTAGE_API_KEY:
        return None
    
    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={ticker}&outputsize=compact&apikey={Config.ALPHA_VANTAGE_API_KEY}"
    response = requests.get(url, timeout=Config.REQUEST_TIMEOUT)
    response.raise_for_status()
    
    data = response.json()
    
    if not data or 'Time Series (Daily)' not in data:
        return None
    
    time_series = data['Time Series (Daily)']
    history = []
    dates = sorted(time_series.keys(), reverse=True)[:days]
    
    for date in dates:
        try:
            history.append({
                'date': date,
                'close': float(time_series[date]['4. close'])
            })
        except (KeyError, ValueError, TypeError):
            continue
    
    if not history:
        return None
    
    history.reverse()
    logger.info(f"✅ Alpha Vantage: {len(history)} registros para {ticker}")
    return history


def get_price_history_full(ticker, days=30):
    cache_key = get_cache_key('history_full', ticker, str(days))
    
    cached = get_from_cache('history_full', cache_key)
    if cached is not None:
        logger.info(f"📊 CACHÉ: Historial completo para {ticker} ({days}d)")
        if hasattr(g, 'metrics'):
            g.metrics.cache_hit = True
        return cached
    
    logger.info(f"📊 Obteniendo historial completo para {ticker} ({days}d)")
    
    if hasattr(g, 'metrics'):
        g.metrics.api_calls += 1
    
    history = fetch_twelvedata_history_full(ticker, days)
    if history is not None:
        set_in_cache('history_full', cache_key, history)
        return history
    
    if hasattr(g, 'metrics'):
        g.metrics.api_calls += 1
    
    history = fetch_alphavantage_history_full(ticker, days)
    if history is not None:
        set_in_cache('history_full', cache_key, history)
        return history
    
    logger.warning(f"⚠️ No se pudo obtener historial para {ticker} de ninguna fuente")
    return []


def get_price_history(ticker, days=30):
    history = get_price_history_full(ticker, days)
    return [item['close'] for item in history] if history else []


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
    try:
        return float(news_sentiment)
    except (ValueError, TypeError):
        return 0.0


def calculate_momentum_zscore(price_history):
    if not price_history or len(price_history) < 2:
        return 0.0
    
    history = price_history[-10:] if len(price_history) >= 10 else price_history
    
    returns = []
    for i in range(1, len(history)):
        if history[i-1] != 0:
            returns.append((history[i] - history[i-1]) / history[i-1])
    
    if not returns:
        return 0.0
    
    last_return = returns[-1]
    mean_return = np.mean(returns)
    std_return = np.std(returns) if np.std(returns) > 0 else 1.0
    
    return (last_return - mean_return) / std_return


def calculate_confidence(sentiment_zscore, momentum_zscore, news_count, history_len):
    confidence = 50
    
    if news_count >= 5:
        confidence += 15
    elif news_count >= 3:
        confidence += 8
    
    if history_len >= 30:
        confidence += 15
    elif history_len >= 15:
        confidence += 8
    
    if abs(momentum_zscore) > 0.5:
        confidence += 5
    
    if abs(sentiment_zscore) > 0.5:
        confidence += 5
    
    return min(95, confidence)


# ============================================================
# PROCESAMIENTO DE TICKERS
# ============================================================
def process_ticker(ticker):
    try:
        news_data = get_news(ticker)
        sentiment_zscore = calculate_sentiment_zscore(news_data.get('sentiment'))
        
        price_history = get_price_history(ticker, days=30)
        momentum_zscore = calculate_momentum_zscore(price_history)
        
        ndi = calculate_narrative_divergence_index(sentiment_zscore, momentum_zscore)
        if ndi is None:
            ndi = 0.0
        
        regime = classify_regime(ndi)
        price = get_price(ticker)
        
        confidence = calculate_confidence(
            sentiment_zscore,
            momentum_zscore,
            len(news_data.get('headlines', [])),
            len(price_history)
        )
        
        return {
            'ticker': ticker,
            'ndi': ndi,
            'sentiment_zscore': sentiment_zscore,
            'momentum_zscore': momentum_zscore,
            'current_price': price,
            'regime': regime['regime'],
            'confidence': confidence,
            'news_count': len(news_data.get('headlines', [])),
            'price_history_len': len(price_history)
        }
    except Exception as e:
        logger.error(f"Error procesando {ticker}: {e}")
        return {
            'ticker': ticker,
            'ndi': 0,
            'sentiment_zscore': 0,
            'momentum_zscore': 0,
            'current_price': None,
            'regime': 'NEUTRAL',
            'confidence': 0,
            'news_count': 0,
            'price_history_len': 0
        }


def process_tickers_parallel(tickers):
    normalized = [t.strip().upper() for t in tickers if t.strip()]
    unique_tickers = list(set(normalized))
    
    if len(unique_tickers) > Config.MAX_TICKERS:
        logger.warning(f"⚠️ Demasiados tickers: {len(unique_tickers)}, limitando a {Config.MAX_TICKERS}")
        unique_tickers = unique_tickers[:Config.MAX_TICKERS]
    
    valid_tickers = [t for t in unique_tickers if t in SUPPORTED_TICKERS]
    invalid_tickers = [t for t in unique_tickers if t not in SUPPORTED_TICKERS]
    
    if invalid_tickers:
        logger.warning(f"⚠️ Tickers inválidos ignorados: {invalid_tickers}")
    
    if not valid_tickers:
        return [], invalid_tickers
    
    results = []
    with ThreadPoolExecutor(max_workers=Config.MAX_WORKERS) as executor:
        future_to_ticker = {executor.submit(process_ticker, ticker): ticker for ticker in valid_tickers}
        for future in as_completed(future_to_ticker):
            result = future.result()
            if result:
                results.append(result)
    return results, invalid_tickers


# ============================================================
# CACHÉ PARA SEÑALES
# ============================================================
def get_cached_signals(tickers_str: str):
    cache_key = get_cache_key('signal', tickers_str)
    
    cached = get_from_cache('signal', cache_key)
    if cached is not None:
        logger.info(f"📊 CACHÉ: Usando datos en caché para {tickers_str}")
        if hasattr(g, 'metrics'):
            g.metrics.cache_hit = True
        return cached
    
    logger.info(f"📊 Procesando {tickers_str} (sin caché)")
    tickers = tickers_str.split(',')
    
    results, invalid = process_tickers_parallel(tickers)
    
    response = {
        'success': True,
        'signals': results,
        'count': len(results),
        'cached': False,
        'timestamp': datetime.now().isoformat(),
        'market_status': get_market_status(),
        'invalid_tickers': invalid if invalid else None
    }
    
    set_in_cache('signal', cache_key, response)
    return response


# ============================================================
# ============================================================
# NUEVO ENDPOINT: /api/ticker/<ticker> 
# ============================================================
@app.route('/api/ticker/<ticker>')
@limiter.limit(Config.RATE_LIMIT_ANALYSIS)
def get_ticker_data(ticker):
    """
    Endpoint específico para obtener datos de un ticker individual
    Este es el endpoint que el frontend está solicitando
    """
    try:
        ticker = ticker.strip().upper()
        logger.info(f"📊 Obteniendo datos para {ticker}")
        
        # Verificar si el ticker es soportado
        if ticker not in SUPPORTED_TICKERS:
            return jsonify({
                'error': f'Ticker {ticker} no soportado',
                'supported_tickers': list(SUPPORTED_TICKERS)
            }), 400
        
        # Verificar caché para este ticker
        cache_key = get_cache_key('ticker', ticker)
        cached = get_from_cache('ticker', cache_key)
        if cached is not None:
            logger.info(f"📊 CACHÉ: Datos para {ticker}")
            if hasattr(g, 'metrics'):
                g.metrics.cache_hit = True
            return jsonify(cached)
        
        # Obtener datos
        news_data = get_news(ticker)
        sentiment_zscore = calculate_sentiment_zscore(news_data.get('sentiment'))
        
        price_history = get_price_history(ticker, days=30)
        momentum_zscore = calculate_momentum_zscore(price_history)
        
        ndi = calculate_narrative_divergence_index(sentiment_zscore, momentum_zscore)
        if ndi is None:
            ndi = 0.0
        
        # Obtener precio actual
        price = get_price(ticker)
        
        # Clasificar régimen
        regime_info = classify_regime(ndi)
        
        # Calcular confianza
        confidence = calculate_confidence(
            sentiment_zscore,
            momentum_zscore,
            len(news_data.get('headlines', [])),
            len(price_history)
        )
        
        # Información de la empresa
        company_info = get_company_info(ticker)
        
        # Preparar respuesta
        response = {
            'ticker': ticker,
            'company_name': company_info['company_name'],
            'sector': company_info['sector'],
            'industry': company_info['industry'],
            'price': price,
            'ndi': round(ndi, 3),
            'sentiment': round(sentiment_zscore, 3),
            'momentum': round(momentum_zscore, 3),
            'regime': regime_info['regime'],
            'signal': regime_info['label'],
            'color': regime_info['color'],
            'confidence': confidence,
            'news_count': len(news_data.get('headlines', [])),
            'market_status': get_market_status(),
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'disclaimer': FINANCIAL_DISCLAIMER
        }
        
        # Guardar en caché
        set_in_cache('ticker', cache_key, response)
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"❌ Error en /api/ticker/{ticker}: {str(e)}")
        return jsonify({
            'error': str(e),
            'ticker': ticker,
            'disclaimer': FINANCIAL_DISCLAIMER
        }), 500


# ============================================================
# RUTAS EXISTENTES DE LA API
# ============================================================
@app.route('/')
def root():
    return jsonify({
        'name': 'SignalIQ API',
        'version': '8.1',
        'status': 'operational',
        'mode': 'twelvedata_with_news',
        'market_status': get_market_status(),
        'disclaimer': FINANCIAL_DISCLAIMER,
        'endpoints': {
            'health': '/health',
            'signals': '/api/signals-live?tickers=AAPL,MSFT',
            'ticker': '/api/ticker/TSLA',
            'analysis': '/api/ticker/analysis/NVDA',
            'prices': '/api/prices/AAPL',
            'tickers': '/api/tickers'
        }
    })


@app.route('/health')
@app.route('/api/health')
@limiter.exempt
def health():
    services = check_services()
    all_ok = all(status == 'ok' for status in services.values() if status != 'not_configured')
    
    return jsonify({
        'status': 'healthy' if all_ok else 'degraded',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'mode': 'twelvedata_with_news',
        'market_status': get_market_status(),
        'services': services,
        'disclaimer': FINANCIAL_DISCLAIMER
    })


@app.route('/api/signals-live')
@limiter.limit(Config.RATE_LIMIT)
def signals_live():
    tickers_param = request.args.get('tickers', '')
    ticker_list = [t.strip() for t in tickers_param.split(',') if t.strip()]
    
    if not ticker_list:
        return jsonify({
            'success': False,
            'error': 'No tickers provided',
            'disclaimer': FINANCIAL_DISCLAIMER
        }), 400
    
    normalized = [t.upper() for t in ticker_list]
    valid_tickers = [t for t in normalized if t in SUPPORTED_TICKERS]
    invalid_tickers = [t for t in normalized if t not in SUPPORTED_TICKERS]
    
    if invalid_tickers:
        logger.warning(f"⚠️ Tickers inválidos ignorados: {invalid_tickers}")
    
    if not valid_tickers:
        return jsonify({
            'success': False,
            'error': 'No valid tickers provided',
            'supported_tickers': list(SUPPORTED_TICKERS),
            'invalid_tickers': invalid_tickers,
            'disclaimer': FINANCIAL_DISCLAIMER
        }), 400
    
    tickers_str = ','.join(sorted(valid_tickers))
    result = get_cached_signals(tickers_str)
    
    ticker_set = set(valid_tickers)
    filtered_signals = [s for s in result['signals'] if s['ticker'] in ticker_set]
    
    return jsonify({
        'success': True,
        'signals': filtered_signals,
        'count': len(filtered_signals),
        'cached': result.get('cached', False),
        'cache_timestamp': result.get('timestamp'),
        'market_status': result.get('market_status', get_market_status()),
        'supported_tickers': list(SUPPORTED_TICKERS),
        'invalid_tickers': invalid_tickers if invalid_tickers else None,
        'disclaimer': FINANCIAL_DISCLAIMER
    })


@app.route('/api/ticker/analysis/<ticker>')
@limiter.limit(Config.RATE_LIMIT_ANALYSIS)
def ticker_analysis(ticker):
    try:
        ticker = ticker.strip().upper()
        logger.info(f"📊 Analizando {ticker}")
        
        if ticker not in SUPPORTED_TICKERS:
            return jsonify({
                'error': f'Ticker {ticker} not supported',
                'supported_tickers': list(SUPPORTED_TICKERS),
                'disclaimer': FINANCIAL_DISCLAIMER
            }), 400
        
        news_data = get_news(ticker)
        news_items = []
        for h, s in zip(news_data.get('headlines', []), news_data.get('scores', [])):
            news_items.append({
                'headline': h,
                'sentiment': s,
                'source': 'RSS Feed'
            })
        
        price = get_price(ticker)
        price_available = price is not None
        
        price_history = get_price_history(ticker, days=30)
        momentum_zscore = calculate_momentum_zscore(price_history)
        
        sentiment_zscore = calculate_sentiment_zscore(news_data.get('sentiment'))
        
        ndi = calculate_narrative_divergence_index(sentiment_zscore, momentum_zscore)
        if ndi is None:
            ndi = 0.0
        
        regime = classify_regime(ndi)
        
        company_info = get_company_info(ticker)
        company_name = company_info['company_name']
        sector = company_info['sector']
        industry = company_info['industry']
        
        confidence = calculate_confidence(
            sentiment_zscore,
            momentum_zscore,
            len(news_data.get('headlines', [])),
            len(price_history)
        )
        
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
            'confidence': confidence,
            'market_status': get_market_status(),
            'quantitativeMetrics': {
                'sentiment': round(sentiment_zscore, 3),
                'momentum': round(momentum_zscore, 3),
                'divergence': round(ndi, 3),
                'sourcesCount': len(news_data.get('headlines', []))
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
            'aiInterpretation': f"{ticker}: NDI {ndi:.3f} - {regime['regime']}. {news_data.get('count', 0)} noticias procesadas con sentimiento {news_data.get('sentiment', 0):.3f}.",
            'newsSummary': {
                'items': news_items,
                'positiveCount': sum(1 for s in news_data.get('scores', []) if s > 0.1),
                'negativeCount': sum(1 for s in news_data.get('scores', []) if s < -0.1),
                'averageSentiment': news_data.get('sentiment', 0)
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
                'insight': f"{ticker}: NDI {ndi:.3f} - {regime['regime']}. Sentimiento de noticias: {news_data.get('sentiment', 0):.3f}"
            },
            'disclaimer': FINANCIAL_DISCLAIMER
        }
        
        if not price_available:
            response['message'] = "Precio no disponible temporalmente, pero las noticias se muestran correctamente."
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"❌ Error en ticker_analysis: {str(e)}")
        return jsonify({
            'error': str(e),
            'disclaimer': FINANCIAL_DISCLAIMER
        }), 500


@app.route('/api/prices/<ticker>')
def get_prices(ticker):
    try:
        ticker = ticker.strip().upper()
        logger.info(f"📊 Obteniendo historial de precios para {ticker}")
        
        if ticker not in SUPPORTED_TICKERS:
            return jsonify({
                'error': f'Ticker {ticker} not supported',
                'supported_tickers': list(SUPPORTED_TICKERS)
            }), 400
        
        history = get_price_history_full(ticker, days=30)
        
        if history:
            return jsonify({
                'ticker': ticker,
                'price_history': history,
                'disclaimer': FINANCIAL_DISCLAIMER
            })
        else:
            return jsonify({
                'ticker': ticker,
                'price_history': [],
                'message': 'No hay datos disponibles para este ticker',
                'disclaimer': FINANCIAL_DISCLAIMER
            }), 200
            
    except Exception as e:
        logger.error(f"❌ Error en /api/prices/{ticker}: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/tickers')
@limiter.exempt
def get_tickers():
    return jsonify({
        'tickers': list(SUPPORTED_TICKERS),
        'count': len(SUPPORTED_TICKERS),
        'disclaimer': FINANCIAL_DISCLAIMER
    })


# ============================================================
# PUNTO DE ENTRADA
# ============================================================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    
    logger.info("=" * 60)
    logger.info("🚀 SignalIQ API v8.1 - Ultimate Production Ready")
    logger.info("=" * 60)
    logger.info(f"📊 Puerto: {port}")
    logger.info(f"📊 Entorno: {Config.ENV}")
    logger.info(f"📊 Modo: twelvedata_with_news")
    logger.info(f"📊 Max Workers: {Config.MAX_WORKERS}")
    logger.info(f"📊 Cache TTL: {Config.CACHE_TTL}")
    logger.info(f"📊 Redis: {'✅ Conectado' if _redis_client else '❌ No configurado'}")
    logger.info(f"📊 Twelve Data: {'✅' if Config.TWELVE_DATA_API_KEY else '❌'} API Key configurada")
    logger.info(f"📊 Alpha Vantage: {'✅' if Config.ALPHA_VANTAGE_API_KEY else '❌'} API Key configurada")
    logger.info("=" * 60)
    logger.info(f"✅ API lista en http://0.0.0.0:{port}")
    logger.info("=" * 60)
    
    app.run(host='0.0.0.0', port=port, debug=Config.DEBUG)
               