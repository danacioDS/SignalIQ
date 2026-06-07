"""SignalIQ API - Versión que usa GEMINI_API_KEY_1/2/3"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import os
import google.generativeai as genai

app = Flask(__name__)
CORS(app)

def get_api_key():
    """Obtener la primera API key disponible"""
    for key_name in ['GEMINI_API_KEY_1', 'GEMINI_API_KEY_2', 'GEMINI_API_KEY_3', 'GEMINI_API_KEY']:
        key = os.environ.get(key_name)
        if key:
            return key
    return None

# Inicializar Gemini
api_key = get_api_key()
model = None

if api_key:
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash')
        # Probar conexión
        model.generate_content("OK", generation_config={'max_output_tokens': 1})
        print("✅ Gemini initialized successfully")
    except Exception as e:
        print(f"❌ Gemini initialization error: {e}")
else:
    print("❌ No API keys found in environment")

@app.route('/debug/env', methods=['GET'])
def debug_env():
    """Endpoint de diagnóstico"""
    keys_found = []
    for key in ['GEMINI_API_KEY', 'GEMINI_API_KEY_1', 'GEMINI_API_KEY_2', 'GEMINI_API_KEY_3']:
        value = os.environ.get(key)
        if value:
            keys_found.append(f"{key}=present (length: {len(value)})")
        else:
            keys_found.append(f"{key}=NOT SET")
    
    return jsonify({
        'environment_variables': keys_found,
        'has_gemini_key': model is not None,
        'mode': 'REAL' if model else 'MOCK'
    })

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'ok',
        'service': 'SignalIQ',
        'mode': 'REAL' if model else 'MOCK',
        'has_api_key': api_key is not None
    })

@app.route('/analyze/<ticker>', methods=['GET'])
def analyze(ticker):
    if not model:
        return jsonify({'error': 'No API key available - Please check environment variables'}), 500
    
    try:
        ticker = ticker.upper()
        prompt = f"Analyze {ticker} stock. Give recommendation BUY/SELL/HOLD. Be brief (2-3 sentences)."
        
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
    return jsonify({
        'message': 'SignalIQ API',
        'endpoints': ['/health', '/analyze/<ticker>', '/debug/env']
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    print("🚀 Starting SignalIQ API...")
    print(f"🔑 Gemini initialized: {model is not None}")
    app.run(host='0.0.0.0', port=port, debug=False)
