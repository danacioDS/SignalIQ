"""SignalIQ API"""

print("=" * 60)
print("SIGNALIQ BUILD 2026-06-07")
print("FILE:", __file__)
print("=" * 60)

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from datetime import datetime
import os
import psycopg2
import google.generativeai as genai

from app.scoring.signal_score import SignalIQScore
from app.classification.event_classifier import EventClassifier

app = Flask(__name__)
print("🚀🚀🚀 SIGNALIQ MAIN.PY LOADED 2026-06-07 🚀🚀🚀")
CORS(app)

# ============================================================
# CONFIG
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
        print(f"❌ Gemini error: {e}")
else:
    print("❌ Gemini key missing")

# ============================================================
# DIAGNOSTIC
# ============================================================

@app.route("/version")
def version():
    return jsonify({
        "service": "SignalIQ",
        "version": "2026-06-07",
        "commit": "FORCE-REDEPLOY",
        "frontend": "react-build-present"
    })

@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "service": "SignalIQ",
        "mode": "REAL" if model else "MOCK"
    })

@app.route("/debug-signaliq-2026")
def debug_signaliq():
    return jsonify({
        "message": "SIGNALIQ DEBUG ROUTE ACTIVE",
        "file": __file__
    })

@app.route("/routes")
def routes():
    return jsonify({
        "routes": sorted([
            str(rule)
            for rule in app.url_map.iter_rules()
        ])
    })

# ============================================================
# ANALYSIS
# ============================================================

@app.route("/analyze/<ticker>")
def analyze(ticker):

    if not model:
        return jsonify({
            "error": "Gemini not configured"
        }), 500

    try:
        ticker = ticker.upper()

        response = model.generate_content(
            f"Analyze {ticker} stock briefly. "
            "Give recommendation BUY/SELL/HOLD."
        )

        text = response.text

        recommendation = "HOLD"

        if "BUY" in text.upper():
            recommendation = "BUY"
        elif "SELL" in text.upper():
            recommendation = "SELL"

        return jsonify({
            "success": True,
            "analysis": {
                "ticker": ticker,
                "recommendation": recommendation,
                "full_analysis": text,
                "timestamp": datetime.now().isoformat()
            }
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============================================================
# SIGNAL SCORE
# ============================================================

@app.route("/score/<ticker>")
def score(ticker):

    try:
        news_item = {
            "title": f"{ticker} market update",
            "content": f"Recent developments for {ticker}",
            "ticker": ticker.upper(),
            "source": "bloomberg",
            "sentiment": "neutral"
        }

        result = signal_scorer.calculate(news_item)

        return jsonify({
            "success": True,
            "ticker": ticker.upper(),
            "signal_score": result
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============================================================
# CLASSIFIER
# ============================================================

@app.route("/classify", methods=["POST"])
def classify():

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

# ============================================================
# DATABASE
# ============================================================


#####

def get_db():
    import os
    import psycopg2
    import urllib.parse

    db_url = os.environ.get("DATABASE_URL")

    if not db_url:
        raise Exception("DATABASE_URL missing")

    # Normalize Render format
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    result = urllib.parse.urlparse(db_url)

    return psycopg2.connect(
        dbname=result.path.lstrip("/"),
        user=result.username,
        password=result.password,
        host=result.hostname,
        port=result.port or 5432,
        sslmode="require"
    )


#####

def stats():

    try:
        conn = get_db()
        cur = conn.cursor()

        cur.execute(
            "SELECT COUNT(*) FROM signal_predictions"
        )
        total = cur.fetchone()[0]

        cur.execute(
            "SELECT COUNT(*) FROM signal_predictions WHERE signal='BULLISH'"
        )
        bullish = cur.fetchone()[0]

        cur.execute(
            "SELECT AVG(score) FROM signal_predictions"
        )
        avg_score = cur.fetchone()[0] or 0

        cur.execute(
            "SELECT COUNT(DISTINCT ticker) FROM signal_predictions"
        )
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
def signals():

    try:
        conn = get_db()
        cur = conn.cursor()

        cur.execute("""
            SELECT
                ticker,
                score,
                signal,
                strength,
                explanation,
                price_at_signal,
                created_at
            FROM signal_predictions
            ORDER BY created_at DESC
            LIMIT 50
        """)

        rows = cur.fetchall()

        conn.close()

        return jsonify({
            "success": True,
            "count": len(rows),
            "signals": rows
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============================================================
# FRONTEND
# ============================================================

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def frontend(path):

    file_path = os.path.join(static_dir, path)

    if path and os.path.exists(file_path):
        return send_from_directory(static_dir, path)

    return send_from_directory(
        static_dir,
        "index.html"
    )

# ============================================================
# MAIN
# ============================================================

print("\nREGISTERED ROUTES:")
for rule in app.url_map.iter_rules():
    print(rule)
print()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))

    app.run(
        host="0.0.0.0",
        port=port
    )
