"""SignalIQ API - Versión con diagnóstico"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import yfinance as yf
from datetime import datetime
import os
import sys
import google.generativeai as genai

app = Flask(__name__)
CORS(app)

# Diagnostic endpoint
@app.route('/debug/env', methods=['GET'])
def debug_env():
    keys_found = []
    for key in ['GEMINI_API_KEY', 'GEMINI_API_KEY_1', 'GEMINI_API_KEY_2', 'GEMINI_API_KEY_3']:
        value = os.environ.get(key)
        if value:
            keys_found.append(f"{key}=present (length: {len(value)})")
        else:
            keys_found.append(f"{key}=NOT SET")
    
    return jsonify({
        'environment_variables': keys_found,
        'has_gemini_key': any(os.environ.get(k) for k in ['GEMINI_API_KEY', 'GEMINI_API_KEY_1', 'GEMINI_API_KEY_2', 'GEMINI_API_KEY_3'])
    })

# Simple health check
@app.route('/health', methods=['GET'])
def health():
    api_key = os.environ.get('GEMINI_API_KEY') or os.environ.get('GEMINI_API_KEY_1')
    return jsonify({
        'status': 'ok',
        'has_api_key': bool(api_key),
        'mode': 'REAL' if api_key else 'MOCK'
    })

# Versión simplificada del análisis
@app.route('/analyze/<ticker>', methods=['GET'])
def analyze(ticker):
    # Intentar obtener API key de diferentes variables
    api_key = (os.environ.get('GEMINI_API_KEY') or 
               os.environ.get('GEMINI_API_KEY_1') or
               os.environ.get('GEMINI_API_KEY_2') or
               os.environ.get('GEMINI_API_KEY_3'))
    
    if not api_key:
        return jsonify({'error': 'No API keys available - Please configure GEMINI_API_KEY in Render environment variables'}), 500
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        ticker = ticker.upper()
        prompt = f"Analyze {ticker} stock. Give recommendation BUY/SELL/HOLD. Be brief (2 sentences)."
        
        response = model.generate_content(prompt)
        analysis = response.text
        
        # Extraer recomendación
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
                'recommendation': rec,
                'full_analysis': analysis,
                'timestamp': datetime.now().isoformat()
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/', methods=['GET'])
def root():
    return jsonify({'message': 'SignalIQ API', 'endpoints': ['/health', '/analyze/<ticker>', '/debug/env']})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
