"""SignalIQ API - Production"""

import os
import json
import logging
from datetime import datetime, timezone
from flask import Flask, request, jsonify, g
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from app.auth import require_api_key
from app.db import init_pool, close_pool, get_connection, put_connection
from app.market_intelligence import market_intel_bp

app = Flask(__name__)
app.register_blueprint(market_intel_bp, url_prefix='/api/market-intelligence')

CORS(app)

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()})

@app.route("/api/version")
def version():
    return jsonify({"service": "SignalIQ", "version": "2026-07-07"})

@app.route("/api/routes")
def routes():
    return jsonify({"routes": [str(r) for r in app.url_map.iter_rules() if r.rule.startswith('/api')]})

@app.route("/api/prices/<ticker>")
@require_api_key
def prices(ticker):
    return jsonify({"ticker": ticker, "message": "Prices endpoint working"})

@app.route("/api/signals-live")
@require_api_key
def signals_live():
    return jsonify({"message": "Signals live endpoint working"})

@app.route("/api/analyze/<ticker>")
@require_api_key
def analyze(ticker):
    return jsonify({"ticker": ticker, "message": "Analyze endpoint working"})

@app.route("/api/classify", methods=["POST"])
@require_api_key
def classify():
    data = request.get_json() or {}
    return jsonify({"message": "Classify endpoint working", "data": data})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=True)
