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
import psycopg2
import psycopg2.extras
import urllib.parse
import google.generativeai as genai

from app.scoring.signal_score import SignalIQScore
from app.classification.event_classifier import EventClassifier

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
        log_error(f"Gemini error: {e}", module="gemini")
else:
    print("❌ Gemini key missing")

# ============================================================
# DB CONNECTION (CONTRACT FIX)
# ============================================================

def get_db():
    db_url = os.environ.get("DATABASE_URL")

    if not db_url:
        raise Exception("DATABASE_URL missing")

    # Limpiar espacios y saltos de línea
    db_url = db_url.strip()

    # Render compatibility
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    print(f"DB URL (clean): {db_url[:50]}...")

    return psycopg2.connect(
        db_url,
        sslmode="require"
    )

print("DATABASE_URL RAW:", repr(os.environ.get("DATABASE_URL")))

# ============================================================
# API ROUTES (TODAS VAN PRIMERO)
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
        conn = get_db()
        cur = conn.cursor()

        cur.execute("SELECT COUNT(*) FROM signal_predictions")
        total = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM signal_predictions WHERE signal='BULLISH'")
        bullish = cur.fetchone()[0]

        cur.execute("SELECT AVG(score) FROM signal_predictions")
        avg_score = cur.fetchone()[0] or 0

        cur.execute("SELECT COUNT(DISTINCT ticker) FROM signal_predictions")
        tickers = cur.fetchone()[0]

        conn.close()

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
        conn = get_db()
        # CRÍTICO: RealDictCursor para devolver objetos, no arrays
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cur.execute("""
            SELECT ticker, score, signal, strength, explanation,
                   price_at_signal, created_at
            FROM signal_predictions
            ORDER BY created_at DESC
            LIMIT 50
        """)

        rows = cur.fetchall()
        conn.close()

        # Convertir fechas a string ISO para JSON
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
    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cur.execute("""
            SELECT ticker, score, signal, strength, explanation,
                   price_at_signal, created_at
            FROM signal_predictions
            WHERE ticker = %s
            ORDER BY created_at DESC
            LIMIT 1
        """, (ticker.upper(),))

        row = cur.fetchone()
        conn.close()

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
    if not model:
        return jsonify({"error": "Gemini not configured"}), 500

    try:
        ticker = ticker.upper()

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