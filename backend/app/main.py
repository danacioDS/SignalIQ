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
import numpy as np

from app.db import init_pool, close_pool, execute_query, execute_query_one, get_connection, put_connection
from app.llm_service import llm_service
import psycopg2.extras

from app.scoring.signal_score import SignalIQScore
from app.classification.event_classifier import EventClassifier

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

CORS(app, 
     origins=[
         "https://signaliq-zeta-ten.vercel.app",
         "https://signaliq-zeta.vercel.app",
         "http://localhost:3000",
         "http://localhost:5173",
         "https://signaliq-api.onrender.com"
     ],
     methods=["GET", "POST", "OPTIONS", "PUT", "DELETE"],
     allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
     expose_headers=["Content-Type", "X-Total-Count"],
     supports_credentials=True,
     max_age=600)

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

api_key = os.environ.get('GOOGLE_API_KEY')
model = None

if api_key:
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.0-flash")
        print("✅ Gemini initialized with GOOGLE_API_KEY")
    except Exception as e:
        log_error(f"Gemini error: {e}")
else:
    print("❌ GOOGLE_API_KEY not found in environment")

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
    ndi_map = {
        'NVDA': 0.738, 'AAPL': 0.522, 'MSFT': 0.668, 'TSLA': 0.532,
        'GOOGL': 0.485, 'META': 0.612, 'AMZN': 0.445, 'AMD': 0.558,
        'KO': 0.212, 'JPM': 0.378,
    }
    return ndi_map.get(ticker, 0.45)

# ============================================================
# PRICES (CORREGIDO - FÓRMULA CANÓNICA)
# ============================================================

@app.route('/api/prices/<ticker>')
@limiter.limit("10 per minute")
def api_prices(ticker):
    err = _validate_ticker(ticker)
    if err:
        return jsonify({'error': err}), 400
    
    ticker = ticker.strip().upper()
    
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
            rows.reverse()
            closes = [float(row[1]) for row in rows]
            current_price = closes[-1]
            prev_price = closes[-5] if len(closes) >= 5 else closes[0]
            
            # ============================================================
            # ✅ NDI CANÓNICO: sentiment_zscore - momentum_zscore
            # ============================================================
            
            # 1. Calcular sentiment_zscore (z-score de retornos diarios)
            daily_returns = []
            for i in range(1, len(closes)):
                if closes[i-1] > 0:
                    daily_returns.append((closes[i] - closes[i-1]) / closes[i-1])
            
            if len(daily_returns) >= 2:
                mean_ret = np.mean(daily_returns)
                std_ret = np.std(daily_returns)
                sentiment_zscore = (daily_returns[-1] - mean_ret) / std_ret if std_ret > 0 else 0
            else:
                sentiment_zscore = 0
            
            # 2. Calcular momentum_zscore (z-score de retorno a 20 días)
            if len(closes) >= 20:
                momentum_returns = []
                for i in range(20, len(closes)):
                    if closes[i-20] > 0:
                        momentum_returns.append((closes[i] / closes[i-20] - 1))
                if len(momentum_returns) >= 2:
                    mean_mom = np.mean(momentum_returns)
                    std_mom = np.std(momentum_returns)
                    momentum_zscore = (momentum_returns[-1] - mean_mom) / std_mom if std_mom > 0 else 0
                else:
                    momentum_zscore = 0
            else:
                momentum_zscore = 0
            
            # 3. ✅ NDI = sentiment_zscore - momentum_zscore
            ndi = sentiment_zscore - momentum_zscore
            ndi = max(-3.0, min(3.0, ndi))
            
            # 4. Clasificar régimen (7 niveles, igual que frontend)
            if ndi > 2.0:
                regime = "Extreme Overheating"
                regime_color = "red"
                regime_code = "EXTREME_OVERHEATING"
                recommendation = "SELL"
            elif ndi > 1.5:
                regime = "Overheating"
                regime_color = "orange"
                regime_code = "OVERHEATING"
                recommendation = "REDUCE"
            elif ndi > 0.5:
                regime = "Watching"
                regime_color = "yellow"
                regime_code = "WATCHING"
                recommendation = "MONITOR"
            elif ndi > -0.5:
                regime = "Stable"
                regime_color = "green"
                regime_code = "STABLE"
                recommendation = "HOLD"
            elif ndi > -1.5:
                regime = "Aligned"
                regime_color = "green"
                regime_code = "ALIGNED"
                recommendation = "HOLD"
            elif ndi > -2.0:
                regime = "Strong Undervalued"
                regime_color = "blue"
                regime_code = "STRONG_UNDERVALUED"
                recommendation = "BUY"
            else:
                regime = "Extreme Undervalued"
                regime_color = "darkblue"
                regime_code = "EXTREME_UNDERVALUED"
                recommendation = "ACCUMULATE"
            
            # 5. Confianza (inverted-U)
            abs_ndi = abs(ndi)
            if abs_ndi <= 0.8:
                confidence = 50 + (abs_ndi / 0.8) * 40
            elif abs_ndi <= 2.0:
                confidence = 90 - ((abs_ndi - 0.8) / 1.2) * 40
            else:
                confidence = 50
            confidence = max(10, min(95, confidence))
            
            # 6. Construir price_history
            price_history = []
            for row in rows:
                price_history.append({
                    'date': row[0].strftime('%Y-%m-%d'),
                    'close': float(row[1])
                })
            
            return jsonify({
                'success': True,
                'ticker': ticker,
                'current_price': round(current_price, 2),
                'prev_price': round(prev_price, 2),
                'sentiment_zscore': round(sentiment_zscore, 3),
                'momentum_zscore': round(momentum_zscore, 3),
                'sentiment': round(sentiment_zscore, 3),  # Backward compatibility
                'momentum': round(momentum_zscore, 3),     # Backward compatibility
                'ndi': round(ndi, 3),
                'regime': regime,
                'regime_code': regime_code,
                'regime_color': regime_color,
                'confidence': round(confidence, 1),
                'recommendation': recommendation,
                'recommendation_text': f"{ticker} shows {regime.lower()} divergence (NDI: {ndi:.3f}).",
                'price_history': price_history,
                'source': 'database',
                'formula': 'sentiment_zscore - momentum_zscore'
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
        "mode": "REAL",
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

# ============================================================
# ANALYZE (SIN AUTENTICACIÓN)
# ============================================================

@app.route("/api/analyze/<ticker>")
@limiter.limit("10 per minute")
def api_analyze(ticker):
    err = _validate_ticker(ticker)
    if err:
        return jsonify({"error": err}), 400

    ticker = ticker.strip().upper()
    
    conn = None
    ndi = get_consistent_ndi(ticker)
    confidence = None
    
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT ndi, confidence
            FROM layer4.signals 
            WHERE ticker = %s 
            ORDER BY signal_date DESC 
            LIMIT 1
        """, (ticker,))
        row = cur.fetchone()
        if row:
            ndi = float(row[0])
            confidence = float(row[1]) if row[1] else None
    except Exception as e:
        log_error(f"DB error for {ticker}: {e}")
    finally:
        if conn:
            put_connection(conn)
    
    analysis = None
    provider = None
    
    try:
        analysis = llm_service.analyze_ticker(ticker, ndi, None, None)
        provider = "groq"
        log_info(f"✅ Análisis generado para {ticker}")
    except Exception as e:
        log_error(f"Error generando análisis para {ticker}: {e}")
        if ndi > 0.7:
            analysis = f"{ticker} shows overheating divergence (NDI: +{ndi:.3f}). Recommendation: Reduce exposure. Risk: High."
        elif ndi > 0.3:
            analysis = f"{ticker} exhibits accumulation divergence (NDI: +{ndi:.3f}). Recommendation: Hold with caution. Risk: Moderate."
        else:
            analysis = f"{ticker} is in aligned regime (NDI: +{ndi:.3f}). Recommendation: Hold. Risk: Low."
        provider = "fallback"
    
    if ndi > 1.5:
        regime = "Overheating"
        regime_color = "red"
    elif ndi > 0.7:
        regime = "Watching"
        regime_color = "yellow"
    elif ndi > 0.3:
        regime = "Accumulation"
        regime_color = "blue"
    else:
        regime = "Aligned"
        regime_color = "green"
    
    recommendation = "HOLD"
    if analysis:
        upper = analysis.upper()
        if "BUY" in upper and "SELL" not in upper:
            recommendation = "BUY"
        elif "SELL" in upper and "BUY" not in upper:
            recommendation = "SELL"
    
    return jsonify({
        "success": True,
        "ticker": ticker,
        "ndi": round(ndi, 3) if ndi else None,
        "regime": regime,
        "regime_color": regime_color,
        "confidence": round(confidence, 1) if confidence else None,
        "recommendation": recommendation,
        "analysis": analysis,
        "provider": provider,
        "timestamp": datetime.now().isoformat()
    })

# ============================================================
# ANALYZE-LLM
# ============================================================

@app.route('/api/analyze-llm/<ticker>')
@limiter.limit("10 per minute")
def api_analyze_llm(ticker):
    err = _validate_ticker(ticker)
    if err:
        return jsonify({'error': err, 'type': 'validation'}), 400
    
    ticker = ticker.strip().upper()
    
    conn = None
    ndi = get_consistent_ndi(ticker)
    
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT ndi
            FROM layer4.signals 
            WHERE ticker = %s 
            ORDER BY signal_date DESC 
            LIMIT 1
        """, (ticker,))
        row = cur.fetchone()
        if row:
            ndi = float(row[0])
    except Exception as e:
        log_error(f"DB error for {ticker}: {e}")
    finally:
        if conn:
            put_connection(conn)
    
    analysis = None
    provider = None
    
    try:
        analysis = llm_service.analyze_ticker(ticker, ndi, None, None)
        provider = "groq"
    except Exception as e:
        log_error(f"Groq error: {e}")
        analysis = f"NDI: {ndi:.3f}. {ticker} in watching regime."
        provider = "fallback"
    
    if ndi > 1.5:
        regime = "Overheating Divergence"
        regime_color = "red"
    elif ndi > 0.7:
        regime = "Watching"
        regime_color = "yellow"
    elif ndi > 0.3:
        regime = "Accumulation Divergence"
        regime_color = "blue"
    else:
        regime = "Aligned"
        regime_color = "green"
    
    return jsonify({
        'success': True,
        'ticker': ticker,
        'ndi': round(ndi, 3) if ndi else None,
        'regime': regime,
        'regime_color': regime_color,
        'confidence': round(0.5 + abs(ndi) * 0.5, 2) if ndi else 0.5,
        'analysis': analysis,
        'provider': provider
    })

# ============================================================
# SIGNALS-LIVE (CORREGIDO - FÓRMULA CANÓNICA)
# ============================================================

@app.route('/api/signals-live')
@limiter.limit("30 per minute")
def api_signals_live():
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
                    rows.reverse()
                    closes = [float(row[1]) for row in rows]
                    current_price = closes[-1]
                    
                    # ============================================================
                    # ✅ NDI CANÓNICO: sentiment_zscore - momentum_zscore
                    # ============================================================
                    
                    # 1. Calcular sentiment_zscore (z-score de retornos diarios)
                    daily_returns = []
                    for i in range(1, len(closes)):
                        if closes[i-1] > 0:
                            daily_returns.append((closes[i] - closes[i-1]) / closes[i-1])
                    
                    if len(daily_returns) >= 2:
                        mean_ret = np.mean(daily_returns)
                        std_ret = np.std(daily_returns)
                        sentiment_zscore = (daily_returns[-1] - mean_ret) / std_ret if std_ret > 0 else 0
                    else:
                        sentiment_zscore = 0
                    
                    # 2. Calcular momentum_zscore (z-score de retorno a 20 días)
                    if len(closes) >= 20:
                        momentum_returns = []
                        for i in range(20, len(closes)):
                            if closes[i-20] > 0:
                                momentum_returns.append((closes[i] / closes[i-20] - 1))
                        if len(momentum_returns) >= 2:
                            mean_mom = np.mean(momentum_returns)
                            std_mom = np.std(momentum_returns)
                            momentum_zscore = (momentum_returns[-1] - mean_mom) / std_mom if std_mom > 0 else 0
                        else:
                            momentum_zscore = 0
                    else:
                        momentum_zscore = 0
                    
                    # 3. ✅ NDI = sentiment_zscore - momentum_zscore
                    ndi = sentiment_zscore - momentum_zscore
                    
                    # 4. Limitar a rango razonable
                    ndi = max(-3.0, min(3.0, ndi))
                    
                    # 5. Clasificar régimen (usando los mismos thresholds que el frontend)
                    if ndi > 2.0:
                        regime = "Extreme Overheating"
                        color = "red"
                    elif ndi > 1.5:
                        regime = "Overheating"
                        color = "orange"
                    elif ndi > 0.5:
                        regime = "Watching"
                        color = "yellow"
                    elif ndi > -0.5:
                        regime = "Stable"
                        color = "green"
                    elif ndi > -1.5:
                        regime = "Aligned"
                        color = "green"
                    elif ndi > -2.0:
                        regime = "Strong Undervalued"
                        color = "blue"
                    else:
                        regime = "Extreme Undervalued"
                        color = "darkblue"
                    
                    # 6. Calcular confianza (inverted-U)
                    abs_ndi = abs(ndi)
                    if abs_ndi <= 0.8:
                        confidence = 50 + (abs_ndi / 0.8) * 40
                    elif abs_ndi <= 2.0:
                        confidence = 90 - ((abs_ndi - 0.8) / 1.2) * 40
                    else:
                        confidence = 50
                    confidence = max(10, min(95, confidence))
                    
                    results.append({
                        'ticker': ticker,
                        'current_price': round(current_price, 2),
                        'ndi': round(ndi, 3),
                        'sentiment_zscore': round(sentiment_zscore, 3),
                        'momentum_zscore': round(momentum_zscore, 3),
                        'regime': regime,
                        'color': color,
                        'confidence': round(confidence, 1),
                        'source': 'database',
                        'formula': 'sentiment_zscore - momentum_zscore'  # ✅ Documentar
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
        'source': 'database',
        'formula': 'sentiment_zscore - momentum_zscore'  # ✅ Documentar
    })

# ============================================================
# SIGNALS-INTEL
# ============================================================

@app.route('/api/signals-intel')
@limiter.limit("30 per minute")
def api_signals_intel():
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

        events = row['events'] if row['events'] else []
        narrative = row['narrative'] if row['narrative'] else []
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
    print(f"🔧 Mode: REAL")
    print(f"📊 Fuente principal: yfinance")
    print(f"📋 API Routes: {len([r for r in app.url_map.iter_rules() if r.rule.startswith('/api')])}")
    print("=" * 60 + "\n")

    import atexit
    atexit.register(close_pool)
    app.run(
        host="0.0.0.0",
        port=port
    )
