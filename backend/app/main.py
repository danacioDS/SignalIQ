"""SignalIQ API - Production Hardened"""

print("=" * 60)
print("SIGNALIQ BUILD 2026-06-12")
print("FILE:", __file__)
print("=" * 60)

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from datetime import datetime
import os
import google.generativeai as genai

from app.scoring.signal_score import SignalIQScore
from app.classification.event_classifier import EventClassifier
from app.db import init_pool, close_pool, execute_query, execute_query_one, get_connection, put_connection

# ============================================================
# STRUCTURED LOGGING (additive, prints preserved)
# ============================================================
import logging
import json

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

static_dir = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "static"
)

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

import re as _re

_TICKER_RE = _re.compile(r"^[A-Z0-9-]{1,10}$")
_MAX_TICKER_LEN = 10


def _validate_ticker(ticker: str) -> str | None:
    """Validate and normalise a ticker symbol.

    Returns the uppercased ticker on success, or an error message on failure.
    """
    if not ticker or not ticker.strip():
        return "Ticker symbol is required"
    cleaned = ticker.strip().upper()
    if len(cleaned) > _MAX_TICKER_LEN:
        return f"Ticker symbol too long (max {_MAX_TICKER_LEN} characters)"
    if not _TICKER_RE.match(cleaned):
        return "Ticker symbol must be 1-10 alphanumeric characters or hyphens"
    return None


def _validate_date_range(start_str: str | None, end_str: str | None) -> list[str]:
    """Validate an optional date range (start/end).

    Returns a list of error messages (empty when valid).
    """
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
        "version": "2026-06-12",
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
    """Endpoint para score individual de un ticker"""
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
# FRONTEND (VA AL FINAL, DESPUÉS DE TODAS LAS API ROUTES)
# ============================================================

@app.route("/")
def frontend_root():
    return send_from_directory(static_dir, "index.html")

@app.route("/<path:path>")
def frontend_catchall(path):
    """Sirve archivos estáticos o index.html para React routing"""
    file_path = os.path.join(static_dir, path)

    if os.path.exists(file_path) and os.path.isfile(file_path):
        return send_from_directory(static_dir, path)

    # Para rutas de React como /ticker/NVDA
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
    print("=" * 60 + "\n")

    app.run(
        host="0.0.0.0",
        port=port
    )