"""SignalIQ API - Versión Simplificada"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import yfinance as yf
from datetime import datetime
import os

from asset_classifier import classifier
from llm_provider import provider

app = Flask(__name__)
CORS(app)

def calculate_ndi(ticker):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="5d")
        if hist.empty:
            return 0.5
        current = hist['Close'].iloc[-1]
        prev = hist['Close'].iloc[0]
        change = (current - prev) / prev
        if change > 0.02:
            return 0.3
        elif change < -0.02:
            return 0.7
        return 0.5
    except:
        return 0.5

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'ok',
        'service': 'SignalIQ',
        'mode': 'REAL' if provider.model else 'MOCK'
    })

@app.route('/analyze/<ticker>', methods=['GET'])
def analyze(ticker):
    try:
        ticker = ticker.upper()
        asset_info = classifier.classify(ticker)
        asset_type = asset_info.get('type', 'unknown')
        asset_name = asset_info.get('name', ticker)
        
        ndi = calculate_ndi(ticker)
        
        prompt = f"""Analyze {ticker} ({asset_name}) - Type: {asset_type}
NDI Score: {ndi} (0.3=BUY, 0.7=SELL)
Provide: 1) Interpretation 2) Recommendation (BUY/SELL/HOLD) 3) Key risks"""
        
        analysis = provider.generate(prompt)
        
        if "BUY" in analysis.upper():
            rec = "BUY"
        elif "SELL" in analysis.upper():
            rec = "SELL"
        else:
            rec = "HOLD"
        
        return jsonify({
            'success': True,
            'analysis': {
                'ticker': ticker,
                'asset_type': asset_type,
                'asset_name': asset_name,
                'recommendation': rec,
                'full_analysis': analysis,
                'timestamp': datetime.now().isoformat()
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
