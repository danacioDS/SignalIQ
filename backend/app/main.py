"""SignalIQ API - Production (Sin Mocks)"""

print("=" * 60)
print("SIGNALIQ API - PRODUCTION")
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

from app.db import init_pool, close_pool, execute_query, execute_query_one, get_connection, put_connection
from app.llm_service import llm_service
import psycopg2.extras

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

# ============================================================
# CORS - CONFIGURACIÓN COMPLETA PARA PRODUCCIÓN
# ============================================================

# Configuración específica para Vercel
CORS(app, 
     origins=[
         "https://signaliq-zeta-ten.vercel.app",
         "https://signaliq-zeta.vercel.app",
         "http://localhost:3000",
         "http://localhost:5173"
     ],
     methods=["GET", "POST", "OPTIONS", "PUT", "DELETE"],
     allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
     expose_headers=["Content-Type", "X-Total-Count"],
     supports_credentials=True,
     max_age=600)  # Cache preflight por 10 minutos


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
# NDI CONSISTENTE (FALLBACK PARA BD)
# ============================================================

def get_consistent_ndi(ticker: str) -> float:
    """NDI consistente por ticker (fallback cuando no hay datos en BD)"""
    ndi_map = {
        'NVDA': 0.738, 'AAPL': 0.522, 'MSFT': 0.668, 'TSLA': 0.532,
        'GOOGL': 0.485, 'META': 0.612, 'AMZN': 0.445, 'AMD': 0.558,
        'KO': 0.212, 'JPM': 0.378,
    }
    return ndi_map.get(ticker, 0.45)

# ============================================================
# PRICES (CON YFINANCE, SIN FINNHUB)
# ============================================================

@app.route('/api/prices/<ticker>')
@limiter.limit("10 per minute")
def api_prices(ticker):
    """Obtiene datos de precios desde la base de datos (Layer 2)"""
    err = _validate_ticker(ticker)
    if err:
        return jsonify({'error': err}), 400
    
    ticker = ticker.strip().upper()
    
    # Intentar obtener datos de la base de datos
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT price_date, close 
            FROM prices 
            WHERE ticker = %s 
            ORDER BY price_date DESC 
            LIMIT 60
        """, (ticker,))
        rows = cur.fetchall()
        
        if rows:
            # Invertir para obtener orden cronológico
            rows.reverse()
            
            price_history = []
            closes = []
            for row in rows:
                price_history.append({
                    'date': row[0].strftime('%Y-%m-%d'),
                    'close': float(row[1])
                })
                closes.append(float(row[1]))
            
            current_price = closes[-1]
            prev_price = closes[-5] if len(closes) >= 5 else closes[0]
            
            # Calcular NDI
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
                'price_history': price_history,
                'source': 'database'
            })
        else:
            return jsonify({
                'error': f'No data found for {ticker} in database',
                'ticker': ticker,
                'suggestion': 'Run ingestion to load data'
            }), 404
            
    except Exception as e:
        log_error(f"Database error for {ticker}: {str(e)}")
        return jsonify({
            'error': str(e),
            'ticker': ticker
        }), 500
    finally:
        if conn:
            put_connection(conn)

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
        "version": "2026-06-17",
        "build": "yfinance_only"
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
        response = model.generate_content(f"Analyze {ticker} stock. Give BUY/SELL/HOLD.")
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
# ENDPOINT ANALYZE-LLM (GROQ + IA REAL)
# ============================================================

@app.route('/api/analyze-llm/<ticker>')
@limiter.limit("10 per minute")
def api_analyze_llm(ticker):
    """Analiza un ticker con IA (Groq) y devuelve NDI + análisis"""
    err = _validate_ticker(ticker)
    if err:
        return jsonify({'error': err, 'type': 'validation'}), 400
    
    ticker = ticker.strip().upper()
    
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT ndi, sentiment_zscore, momentum_zscore 
            FROM layer4.signals 
            WHERE ticker = %s 
            ORDER BY signal_date DESC 
            LIMIT 1
        """, (ticker,))
        row = cur.fetchone()
        
        if row:
            ndi = float(row[0])
            sentiment = float(row[1]) if row[1] else None
            momentum = float(row[2]) if row[2] else None
        else:
            ndi = get_consistent_ndi(ticker)
            sentiment = None
            momentum = None
    except Exception as e:
        log_error(f"DB error for {ticker}: {e}")
        ndi = get_consistent_ndi(ticker)
        sentiment = None
        momentum = None
    finally:
        if conn:
            put_connection(conn)
    
    try:
        analysis = llm_service.analyze_ticker(ticker, ndi, sentiment, momentum)
    except Exception as e:
        log_error(f"Groq error for {ticker}: {e}")
        analysis = f"⚠️ [FALLBACK] {ticker} shows NDI: +{ndi:.3f}. Analysis unavailable due to LLM error."
    
    if ndi > 0.7:
        regime = "Overheating Divergence"
        regime_color = "red"
    elif ndi > 0.3:
        regime = "Accumulation Divergence"
        regime_color = "yellow"
    else:
        regime = "Aligned"
        regime_color = "green"
    
    return jsonify({
        'success': True,
        'ticker': ticker,
        'ndi': round(ndi, 3),
        'regime': regime,
        'regime_color': regime_color,
        'sentiment': round(sentiment, 2) if sentiment else None,
        'momentum': round(momentum, 2) if momentum else None,
        'confidence': round(0.5 + abs(ndi) * 0.5, 2) if ndi else 0.5,
        'analysis': analysis
    })

# ============================================================
# SIGNALS-LIVE (CON YFINANCE - SIN API KEY)
# ============================================================

@app.route('/api/signals-live')
@limiter.limit("30 per minute")
def api_signals_live():
    """Obtiene señales en vivo desde la base de datos"""
    tickers_param = request.args.get('tickers', 'NVDA,AAPL,MSFT,TSLA,GOOGL,META,AMD,AMZN,JPM,KO')
    tickers_list = [t.strip().upper() for t in tickers_param.split(',') if t.strip()]
    
    results = []
    errors = []
    
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        for ticker in tickers_list:
            try:
                cur.execute("""
                    SELECT price_date, close 
                    FROM prices 
                    WHERE ticker = %s 
                    ORDER BY price_date DESC 
                    LIMIT 60
                """, (ticker,))
                rows = cur.fetchall()
                
                if rows:
                    # Invertir para orden cronológico
                    rows.reverse()
                    closes = [float(row[1]) for row in rows]
                    current_price = closes[-1]
                    
                    # Calcular NDI
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
                    
                    if ndi > 0.7:
                        regime = "Overheating"
                        color = "red"
                    elif ndi > 0.3:
                        regime = "Watching"
                        color = "yellow"
                    else:
                        regime = "Aligned"
                        color = "green"
                    
                    results.append({
                        'ticker': ticker,
                        'current_price': round(current_price, 2),
                        'ndi': round(ndi, 3),
                        'regime': regime,
                        'color': color,
                        'confidence': round(70 + (abs(ndi) * 15), 1),
                        'source': 'database'
                    })
                else:
                    errors.append(f"No data found for {ticker}")
            except Exception as e:
                errors.append(f"Error for {ticker}: {str(e)}")
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            put_connection(conn)
    
    return jsonify({
        'success': True,
        'count': len(results),
        'signals': results,
        'errors': errors if errors else None,
        'timestamp': datetime.now().isoformat(),
        'source': 'database'
    })
# ============================================================
# ENDPOINT SIGNALS-INTEL (EVENTS + NARRATIVE)
# ============================================================

@app.route('/api/signals-intel')
@limiter.limit("30 per minute")
def api_signals_intel():
    """Obtiene EVENTS + NARRATIVE desde intel_signals."""
    ticker = request.args.get('ticker', '').strip().upper()
    if not ticker:
        return jsonify({'error': 'Ticker parameter is required'}), 400

    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT ticker, ndi, events, narrative, created_at
            FROM intel_signals
            WHERE ticker = %s
            ORDER BY created_at DESC
            LIMIT 1
        """, (ticker,))
        row = cur.fetchone()

        if not row:
            return jsonify({
                'success': False,
                'error': f'No intelligence data found for {ticker}'
            }), 404

        # Parsear JSONB
        events = row['events'] if row['events'] else []
        narrative = row['narrative'] if row['narrative'] else []

        # Extraer solo labels de eventos
        event_labels = [e.get('label', '') for e in events if e.get('label')]

        return jsonify({
            'success': True,
            'ticker': row['ticker'],
            'ndi': float(row['ndi']) if row['ndi'] else None,
            'events': event_labels,
            'narrative': narrative,
            'timestamp': row['created_at'].isoformat() if row['created_at'] else None
        })

    except Exception as e:
        log_error(f"Intel error for {ticker}: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            put_connection(conn)

# ============================================================
# FRONTEND
# ============================================================

static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")

if not os.path.exists(static_dir):
    os.makedirs(static_dir, exist_ok=True)

@app.route("/")
def root():
    return jsonify({
        "service": "SignalIQ API",
        "status": "online",
        "version": "2026-06-17",
        "documentation": "/api/health",
        "endpoints": [
            "/api/health",
            "/api/version",
            "/api/prices/<ticker>",
            "/api/signals-live",
            "/api/analyze-llm/<ticker>"
        ]
    })

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
    print(f"📊 Fuente principal: yfinance (sin API key)")
    print(f"📋 API Routes: {len([r for r in app.url_map.iter_rules() if r.rule.startswith('/api')])}")
    print("=" * 60 + "\n")

    import atexit
    atexit.register(close_pool)
    app.run(
        host="0.0.0.0",
        port=port
    )
