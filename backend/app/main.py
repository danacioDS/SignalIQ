"""SignalIQ API - Production Hardened"""

print("=" * 60)
print("SIGNALIQ BUILD 2026-06-16")
print("FILE:", __file__)
print("=" * 60)

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from datetime import datetime, timedelta
import os
import json
import logging
import re as _re
import time
import yfinance as yf
import google.generativeai as genai
import requests

from app.scoring.signal_score import SignalIQScore
from app.classification.event_classifier import EventClassifier
from app.db import init_pool, close_pool, execute_query, execute_query_one, get_connection, put_connection
from app.llm_service import llm_service

# ============================================================
# STRUCTURED LOGGING
# ============================================================
USE_JSON_LOGS = os.environ.get('USE_JSON_LOGS', 'true').lower() == 'true'

class JSONFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'name': record.name,
            'message': record.getMessage(),
            'module': record.module
        })

_logger = logging.getLogger(__name__)
_handler = logging.StreamHandler()
_handler.setFormatter(JSONFormatter())
_logger.addHandler(_handler)
_logger.setLevel(logging.INFO)

def log_info(msg, **kwargs):
    if USE_JSON_LOGS:
        _logger.info(msg, extra=kwargs)
    print(f"[INFO] {msg}")

def log_error(msg, **kwargs):
    if USE_JSON_LOGS:
        _logger.error(msg, extra=kwargs)
    print(f"[ERROR] {msg}")

app = Flask(__name__)
log_info("SignalIQ main.py loaded", event="startup")
CORS(app)

redis_url = os.environ.get('REDIS_URL')
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri=redis_url or "memory://"
)

# ============================================================
# INIT
# ============================================================

signal_scorer = SignalIQScore()
event_classifier = EventClassifier()

# ============================================================
# GEMINI
# ============================================================

def get_api_key():
    for key_name in [
        "GEMINI_API_KEY_1",
        "GEMINI_API_KEY_2",
        "GEMINI_API_KEY_3",
        "GEMINI_API_KEY",
    ]:
        key = os.environ.get(key_name)
        if key:
            return key
    return None

api_key = get_api_key()
model = None

if api_key:
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.0-flash")
        print("✅ Gemini initialized")
    except Exception as e:
        log_error(f"Gemini error: {e}")
else:
    print("❌ Gemini key missing")

# ============================================================
# DB CONNECTION POOL
# ============================================================

if os.environ.get("DATABASE_URL"):
    try:
        init_pool()
        log_info("Database pool initialised")
    except Exception as e:
        log_error(f"Database pool init failed: {e}")

# ============================================================
# INPUT VALIDATION
# ============================================================

_TICKER_RE = _re.compile(r"^[A-Z0-9-]{1,10}$")
_MAX_TICKER_LEN = 10

def _validate_ticker(ticker: str) -> str | None:
    """Validate and normalise a ticker symbol."""
    if not ticker or not ticker.strip():
        return "Ticker symbol is required"
    cleaned = ticker.strip().upper()
    if len(cleaned) > _MAX_TICKER_LEN:
        return f"Ticker symbol too long (max {_MAX_TICKER_LEN} characters)"
    if not _TICKER_RE.match(cleaned):
        return "Ticker symbol must be 1-10 alphanumeric characters or hyphens"
    return None

def _validate_date_range(start_str: str | None, end_str: str | None) -> list[str]:
    """Validate an optional date range (start/end)."""
    errors = []
    today = datetime.now().date()

    for label, raw in [("start_date", start_str), ("end_date", end_str)]:
        if not raw:
            continue
        try:
            dt = datetime.strptime(raw.strip(), "%Y-%m-%d").date()
        except (ValueError, AttributeError):
            errors.append(f"{label} must be in YYYY-MM-DD format")
            continue

        if dt > today:
            errors.append(f"{label} cannot be in the future")
        if (today - dt).days > 365 * 5:
            errors.append(f"{label} cannot be more than 5 years in the past")

    if start_str and end_str:
        try:
            start = datetime.strptime(start_str.strip(), "%Y-%m-%d").date()
            end = datetime.strptime(end_str.strip(), "%Y-%m-%d").date()
            if start > end:
                errors.append("start_date must be before or equal to end_date")
        except (ValueError, AttributeError):
            pass

    return errors

def _validate_classify_input(data: dict) -> list[str]:
    """Validate the JSON body for the ``/api/classify`` endpoint."""
    errors = []
    if not isinstance(data, dict):
        return ["Request body must be a JSON object"]
    title = data.get("title", "")
    content = data.get("content", "")
    if not title and not content:
        errors.append("At least one of 'title' or 'content' is required")
    if title and not isinstance(title, str):
        errors.append("'title' must be a string")
    if content and not isinstance(content, str):
        errors.append("'content' must be a string")
    max_len = 10000
    if len(title) > max_len:
        errors.append(f"'title' exceeds maximum length of {max_len} characters")
    if len(content) > max_len:
        errors.append(f"'content' exceeds maximum length of {max_len} characters")
    return errors

# ============================================================
# FINNHUB API (alternativa a Yahoo Finance para Render)
# ============================================================

def get_stock_data_finnhub(ticker: str) -> dict:
    """Obtiene datos de Finnhub API con manejo de rate limiting."""
    api_key = os.environ.get("FINNHUB_API_KEY")
    if not api_key:
        return {'error': 'Finnhub API key not configured', 'ticker': ticker}
    
    # Pequeña pausa para evitar rate limiting (0.2 segundos)
    time.sleep(0.2)
    
    try:
        url = f"https://finnhub.io/api/v1/stock/candle?symbol={ticker}&resolution=D&count=60&token={api_key}"
        response = requests.get(url, timeout=10)
        
        # Si es rate limit, devolver error controlado
        if response.status_code == 429:
            log_error(f"Finnhub rate limit exceeded for {ticker}")
            return {'error': 'Rate limit exceeded', 'ticker': ticker}
        
        data = response.json()
        
        if "c" in data and data["c"] and len(data["c"]) > 0:
            closes = data["c"]
            timestamps = data["t"]
            
            price_history = []
            for i in range(len(closes)):
                price_history.append({
                    "date": datetime.fromtimestamp(timestamps[i]).strftime("%Y-%m-%d"),
                    "close": closes[i]
                })
            
            current_price = closes[-1] if closes else 0
            prev_price = closes[-5] if len(closes) >= 5 else closes[0] if closes else 0
            
            # Calcular sentimiento y momentum
            if len(closes) > 1:
                daily_return = (closes[-1] - closes[-2]) / closes[-2]
                sentiment = 0.5 + (daily_return * 0.5)
            else:
                sentiment = 0.5
            sentiment = max(0.1, min(0.9, sentiment))
            
            if len(closes) >= 20:
                momentum = (closes[-1] / closes[-20] - 1) * 100
            else:
                momentum = 0
            
            ndi = sentiment - (momentum / 100)
            ndi = max(-2.0, min(2.0, ndi))
            
            if ndi > 1.5:
                regime = "Overheating"
                regime_color = "red"
            elif ndi > 0.5:
                regime = "Watching"
                regime_color = "yellow"
            else:
                regime = "Aligned"
                regime_color = "green"
            
            return {
                'success': True,
                'ticker': ticker,
                'current_price': round(current_price, 2),
                'prev_price': round(prev_price, 2),
                'sentiment': round(sentiment, 3),
                'momentum': round(momentum, 2),
                'ndi': round(ndi, 3),
                'regime': regime,
                'regime_color': regime_color,
                'confidence': round(70 + (abs(ndi) * 15), 1),
                'recommendation': f"{ticker} shows {regime.lower()} divergence.",
                'price_history': price_history
            }
        else:
            return {'error': f'No data found for {ticker}', 'ticker': ticker}
    except requests.exceptions.Timeout:
        return {'error': 'Request timeout', 'ticker': ticker}
    except Exception as e:
        log_error(f"Finnhub error for {ticker}: {str(e)}")
        return {'error': str(e), 'ticker': ticker}

def generate_mock_data(ticker: str) -> dict:
    """Genera datos simulados para la demo cuando la API falla."""
    # Datos de respaldo para los tickers más comunes
    mock_data = {
        'NVDA': {'current_price': 205.10, 'ndi': 0.738, 'regime': 'Overheating'},
        'AAPL': {'current_price': 307.34, 'ndi': 0.522, 'regime': 'Watching'},
        'MSFT': {'current_price': 416.67, 'ndi': 0.668, 'regime': 'Watching'},
        'TSLA': {'current_price': 391.00, 'ndi': 0.532, 'regime': 'Watching'},
        'GOOGL': {'current_price': 175.20, 'ndi': 0.485, 'regime': 'Watching'},
        'META': {'current_price': 512.80, 'ndi': 0.612, 'regime': 'Watching'},
        'AMD': {'current_price': 165.30, 'ndi': 0.558, 'regime': 'Watching'},
        'AMZN': {'current_price': 189.50, 'ndi': 0.445, 'regime': 'Watching'},
        'JPM': {'current_price': 212.40, 'ndi': 0.378, 'regime': 'Watching'},
        'XOM': {'current_price': 118.20, 'ndi': 0.401, 'regime': 'Watching'},
        'KO': {'current_price': 70.80, 'ndi': 0.212, 'regime': 'Aligned'},
    }
    
    data = mock_data.get(ticker, {'current_price': 100.00, 'ndi': 0.45, 'regime': 'Aligned'})
    
    # Crear historial de precios simulado
    price_history = []
    now = datetime.now()
    for i in range(60):
        price_history.append({
            'date': (now - timedelta(days=60-i)).strftime('%Y-%m-%d'),
            'close': data['current_price'] * (1 + (i - 30) / 500)
        })
    
    return {
        'success': True,
        'ticker': ticker,
        'current_price': data['current_price'],
        'prev_price': round(data['current_price'] * 0.95, 2),
        'sentiment': round(0.5 + (data['ndi'] * 0.3), 3),
        'momentum': round(data['ndi'] * 100, 2),
        'ndi': data['ndi'],
        'regime': data['regime'],
        'regime_color': 'red' if data['ndi'] > 0.6 else 'yellow' if data['ndi'] > 0.3 else 'green',
        'confidence': round(65 + (data['ndi'] * 20), 1),
        'recommendation': f"{ticker} shows {data['regime'].lower()} divergence. Market narrative has significantly outpaced price action.",
        'price_history': price_history
    }

def get_ticker_data_sync(ticker: str) -> dict:
    """Obtiene datos de Yahoo Finance para un ticker (versión síncrona)."""
    ticker = ticker.upper()
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period='6mo')
        
        if hist.empty:
            return {'ticker': ticker, 'error': 'No data found'}
        
        current_price = hist['Close'].iloc[-1]
        prev_price = hist['Close'].iloc[-5] if len(hist) >= 5 else hist['Close'].iloc[0]
        
        if len(hist) > 1:
            daily_return = hist['Close'].pct_change().iloc[-1]
            sentiment = 0.5 + (daily_return * 0.5)
        else:
            sentiment = 0.5
        sentiment = max(0.1, min(0.9, sentiment))
        
        if len(hist) >= 20:
            momentum = (hist['Close'].iloc[-1] / hist['Close'].iloc[-20] - 1) * 100
        else:
            momentum = (hist['Close'].iloc[-1] / hist['Close'].iloc[0] - 1) * 100
        
        ndi = sentiment - (momentum / 100)
        ndi = max(-2.0, min(2.0, ndi))
        
        if ndi > 1.5:
            regime = "Overheating"
            color = "red"
        elif ndi > 0.5:
            regime = "Watching"
            color = "yellow"
        else:
            regime = "Aligned"
            color = "green"
        
        price_history = []
        for i in range(max(0, len(hist) - 60), len(hist)):
            price_history.append({
                'date': hist.index[i].strftime('%Y-%m-%d'),
                'close': round(hist['Close'].iloc[i], 2)
            })
        
        return {
            'ticker': ticker,
            'current_price': round(current_price, 2),
            'prev_price': round(prev_price, 2),
            'sentiment': round(sentiment, 3),
            'momentum': round(momentum, 2),
            'ndi': round(ndi, 3),
            'regime': regime,
            'color': color,
            'confidence': round(70 + (abs(ndi) * 15), 1),
            'recommendation': f"{ticker} shows {regime.lower()} divergence.",
            'price_history': price_history
        }
    except Exception as e:
        log_error(f"Error fetching data for {ticker}: {str(e)}")
        return {'ticker': ticker, 'error': str(e)}

# ============================================================
# API ROUTES
# ============================================================

@app.route("/api/health")
def api_health():
    return jsonify({
        "status": "ok",
        "mode": "REAL" if model else "MOCK",
        "timestamp": datetime.now().isoformat()
    })

@app.route("/api/version")
def api_version():
    return jsonify({
        "service": "SignalIQ",
        "version": "2026-06-16",
        "build": "production_hardening"
    })

@app.route("/api/stats")
def api_stats():
    try:
        total = execute_query_one("SELECT COUNT(*) FROM signal_predictions")[0]
        bullish = execute_query_one("SELECT COUNT(*) FROM signal_predictions WHERE signal='BULLISH'")[0]
        avg_score = execute_query_one("SELECT AVG(score) FROM signal_predictions")[0] or 0
        tickers = execute_query_one("SELECT COUNT(DISTINCT ticker) FROM signal_predictions")[0]

        return jsonify({
            "success": True,
            "total_signals": total,
            "bullish_signals": bullish,
            "average_score": round(float(avg_score), 1),
            "active_tickers": tickers
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/signals")
def api_signals():
    try:
        from psycopg2.extras import RealDictCursor
        rows = execute_query("""
            SELECT ticker, score, signal, strength, explanation,
                   price_at_signal, created_at
            FROM signal_predictions
            ORDER BY created_at DESC
            LIMIT 50
        """, cursor_factory=RealDictCursor)

        for row in rows:
            if row.get('created_at'):
                row['created_at'] = row['created_at'].isoformat()

        return jsonify({
            "success": True,
            "count": len(rows),
            "signals": rows
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/score/<ticker>")
def api_score(ticker):
    err = _validate_ticker(ticker)
    if err:
        return jsonify({"error": err}), 400

    try:
        from psycopg2.extras import RealDictCursor
        cleaned = ticker.strip().upper()
        row = execute_query_one("""
            SELECT ticker, score, signal, strength, explanation,
                   price_at_signal, created_at
            FROM signal_predictions
            WHERE ticker = %s
            ORDER BY created_at DESC
            LIMIT 1
        """, (cleaned,), cursor_factory=RealDictCursor)

        if row:
            if row.get('created_at'):
                row['created_at'] = row['created_at'].isoformat()

            return jsonify({
                "success": True,
                "signal": row
            })
        else:
            return jsonify({
                "success": False,
                "message": f"No signal found for {ticker}"
            }), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/classify", methods=["POST"])
@limiter.limit("30 per minute")
def api_classify():
    try:
        data = request.get_json() or {}
        errors = _validate_classify_input(data)
        if errors:
            return jsonify({"error": "; ".join(errors)}), 400

        result = event_classifier.classify(
            data.get("title", ""),
            data.get("content", "")
        )

        return jsonify({
            "success": True,
            "classification": result
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/routes")
def api_routes():
    return jsonify({
        "routes": sorted([str(r) for r in app.url_map.iter_rules() if r.rule.startswith('/api')])
    })

@app.route("/api/analyze/<ticker>")
@limiter.limit("10 per minute")
def api_analyze(ticker):
    err = _validate_ticker(ticker)
    if err:
        return jsonify({"error": err}), 400

    if not model:
        return jsonify({"error": "Gemini not configured"}), 500

    try:
        ticker = ticker.strip().upper()

        response = model.generate_content(
            f"Analyze {ticker} stock. Give BUY/SELL/HOLD."
        )

        text = response.text

        recommendation = "HOLD"
        if "BUY" in text.upper():
            recommendation = "BUY"
        elif "SELL" in text.upper():
            recommendation = "SELL"

        return jsonify({
            "success": True,
            "ticker": ticker,
            "recommendation": recommendation,
            "analysis": text,
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============================================================
# ENDPOINTS CON FINNHUB + FALLBACK A DATOS SIMULADOS
# ============================================================

@app.route('/api/prices/<ticker>')
@limiter.limit("10 per minute")
def api_prices(ticker):
    """Obtiene datos de precios y NDI para un ticker específico.
    
    Intenta: Finnhub → Yahoo Finance → Datos simulados (fallback).
    """
    err = _validate_ticker(ticker)
    if err:
        return jsonify({'error': err}), 400
    
    ticker = ticker.strip().upper()
    
    # 1. Intentar con Finnhub
    result = get_stock_data_finnhub(ticker)
    if 'error' not in result:
        return jsonify(result)
    
    # 2. Si Finnhub falla, intentar con yfinance
    try:
        import yfinance as yf
        stock = yf.Ticker(ticker)
        hist = stock.history(period='6mo')
        if not hist.empty:
            # Procesar datos de yfinance
            current_price = hist['Close'].iloc[-1]
            prev_price = hist['Close'].iloc[-5] if len(hist) >= 5 else hist['Close'].iloc[0]
            
            if len(hist) > 1:
                daily_return = hist['Close'].pct_change().iloc[-1]
                sentiment = 0.5 + (daily_return * 0.5)
            else:
                sentiment = 0.5
            sentiment = max(0.1, min(0.9, sentiment))
            
            if len(hist) >= 20:
                momentum = (hist['Close'].iloc[-1] / hist['Close'].iloc[-20] - 1) * 100
            else:
                momentum = 0
            
            ndi = sentiment - (momentum / 100)
            ndi = max(-2.0, min(2.0, ndi))
            
            if ndi > 1.5:
                regime = "Overheating"
                regime_color = "red"
            elif ndi > 0.5:
                regime = "Watching"
                regime_color = "yellow"
            else:
                regime = "Aligned"
                regime_color = "green"
            
            price_history = []
            for i in range(max(0, len(hist) - 60), len(hist)):
                price_history.append({
                    'date': hist.index[i].strftime('%Y-%m-%d'),
                    'close': round(hist['Close'].iloc[i], 2)
                })
            
            return jsonify({
                'success': True,
                'ticker': ticker,
                'current_price': round(current_price, 2),
                'prev_price': round(prev_price, 2),
                'sentiment': round(sentiment, 3),
                'momentum': round(momentum, 2),
                'ndi': round(ndi, 3),
                'regime': regime,
                'regime_color': regime_color,
                'confidence': round(70 + (abs(ndi) * 15), 1),
                'recommendation': f"{ticker} shows {regime.lower()} divergence.",
                'price_history': price_history
            })
    except Exception as e:
        log_error(f"yfinance error for {ticker}: {str(e)}")
    
    # 3. Si todo falla, usar datos simulados
    log_info(f"Using mock data for {ticker}")
    return jsonify(generate_mock_data(ticker))

@app.route('/api/signals-live')
@limiter.limit("30 per minute")
def api_signals_live():
    """Obtiene señales en vivo para múltiples tickers."""
    tickers_param = request.args.get('tickers', 'NVDA,AAPL,MSFT,TSLA,GOOGL,META,AMD,AMZN,JPM,XOM,KO')
    tickers_list = [t.strip().upper() for t in tickers_param.split(',') if t.strip()]
    
    results = []
    for ticker in tickers_list:
        # Intentar con Finnhub primero
        data = get_stock_data_finnhub(ticker)
        if 'error' not in data:
            results.append(data)
        else:
            # Si Finnhub falla, intentar con yfinance
            data = get_ticker_data_sync(ticker)
            if 'error' not in data:
                results.append(data)
            else:
                # Si todo falla, usar mock
                results.append(generate_mock_data(ticker))
    
    return jsonify({
        'success': True,
        'count': len(results),
        'signals': results,
        'timestamp': datetime.now().isoformat()
    })

# ============================================================
# FRONTEND
# ============================================================

static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")

if not os.path.exists(static_dir):
    os.makedirs(static_dir, exist_ok=True)

@app.route("/")
def frontend_root():
    return send_from_directory(static_dir, "index.html")

@app.route("/<path:path>")
def frontend_catchall(path):
    if '.' in path and not path.startswith('api/'):
        file_path = os.path.join(static_dir, path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return send_from_directory(static_dir, path)
    
    return send_from_directory(static_dir, "index.html")

# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))

    print("\n" + "=" * 60)
    print("🚀 SIGNALIQ PRODUCTION SERVER")
    print("=" * 60)
    print(f"📍 Port: {port}")
    print(f"📁 Static dir: {static_dir}")
    print(f"🔧 Mode: {'REAL' if model else 'MOCK'}")
    print(f"📊 Yahoo Finance: {'ENABLED'}")
    print(f"📊 Finnhub: {'ENABLED' if os.environ.get('FINNHUB_API_KEY') else 'DISABLED'}")
    print(f"📋 API Routes: {len([r for r in app.url_map.iter_rules() if r.rule.startswith('/api')])}")
    print("=" * 60 + "\n")

    app.run(
        host="0.0.0.0",
        port=port
    )