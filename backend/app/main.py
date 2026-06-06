"""SignalIQ API - Clasificación Automática de Activos"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
import yfinance as yf
from datetime import datetime
import os
import sys

# Agregar el directorio actual al path para poder importar módulos locales
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importar módulos locales usando importación absoluta
from asset_classifier import classifier

app = Flask(__name__)
CORS(app)

# Configuración Gemini
API_KEYS = [
    {'key': 'GEMINI_API_KEY_REDACTED', 'name': 'Proyecto_1'},
    {'key': 'GEMINI_API_KEY_REDACTED', 'name': 'Proyecto_2'},
    {'key': 'GEMINI_API_KEY_REDACTED', 'name': 'SignalIQ_03'},
]

MODEL_NAME = 'gemini-2.0-flash'
current_key_index = 0
model = None

def init_gemini(key_index):
    global model, current_key_index
    try:
        genai.configure(api_key=API_KEYS[key_index]['key'])
        test_model = genai.GenerativeModel(MODEL_NAME)
        test_model.generate_content("OK", generation_config={'max_output_tokens': 1})
        model = test_model
        current_key_index = key_index
        print(f"✅ Conectado con {API_KEYS[key_index]['name']}")
        return True
    except Exception as e:
        print(f"❌ Error: {str(e)[:80]}")
        return False

def get_available_key():
    for i in range(len(API_KEYS)):
        if init_gemini(i):
            return True
    return False

get_available_key()

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

def get_prompt(asset_info, ticker, ndi):
    asset_type = asset_info.get('type', 'unknown')
    name = asset_info.get('name', ticker)
    
    prompts = {
        'stock': f"""You are a stock analyst. Analyze {ticker} ({name}):

NDI Score: {ndi} (>0.7=SELL, <0.3=BUY)

Provide:
1. NDI interpretation
2. Market sentiment
3. Recommendation (BUY/SELL/HOLD)
4. Key risks

Be professional and concise.""",
        
        'crypto': f"""You are a crypto analyst. Analyze {ticker} ({name}):

NDI Score: {ndi} (>0.7=SELL, <0.3=BUY)

Provide:
1. NDI interpretation
2. Crypto market sentiment
3. Recommendation (BUY/SELL/HOLD)
4. Key risks (volatility, regulation)""",
        
        'forex': f"""You are a forex analyst. Analyze {ticker} ({name}):

NDI Score: {ndi} (>0.7=SELL, <0.3=BUY)

Provide:
1. NDI interpretation for this currency
2. Macroeconomic sentiment
3. Recommendation (BUY/SELL/HOLD)
4. Key risks (central banks, geopolitics)""",
        
        'unknown': f"""Analyze {ticker}:

NDI Score: {ndi} (>0.7=SELL, <0.3=BUY)

Provide analysis and recommendation (BUY/SELL/HOLD)."""
    }
    
    return prompts.get(asset_type, prompts['unknown'])

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'ok',
        'service': 'SignalIQ',
        'active_key': API_KEYS[current_key_index]['name'] if model else 'MOCK',
        'keys_available': len(API_KEYS),
        'mode': 'REAL' if model else 'MOCK'
    })

@app.route('/analyze/<ticker>', methods=['GET'])
def analyze(ticker):
    global model, current_key_index
    
    if not model:
        return jsonify({'error': 'No API keys available'}), 429
    
    try:
        ticker = ticker.upper()
        
        # CLASIFICACIÓN AUTOMÁTICA
        asset_info = classifier.classify(ticker)
        asset_type = asset_info.get('type', 'unknown')
        asset_name = asset_info.get('name', ticker)
        
        print(f"📊 Analizando {ticker}... (Tipo: {asset_type})")
        
        ndi = calculate_ndi(ticker)
        prompt = get_prompt(asset_info, ticker, ndi)
        
        response = model.generate_content(prompt)
        analysis = response.text
        
        if "BUY" in analysis.upper() and "SELL" not in analysis.upper():
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
                'confidence': 0.90,
                'signal_strength': "STRONG" if ndi > 0.7 else "MODERATE",
                'full_analysis': analysis,
                'ndi_calculated': ndi,
                'key_used': API_KEYS[current_key_index]['name'],
                'timestamp': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg:
            next_key = (current_key_index + 1) % len(API_KEYS)
            if init_gemini(next_key):
                return analyze(ticker)
        return jsonify({'error': error_msg}), 500

@app.route('/', methods=['GET'])
def root():
    return jsonify({'message': 'SignalIQ API', 'endpoints': ['/health', '/analyze/<ticker>']})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("=" * 60)
    print("🚀 SignalIQ API - Clasificación Automática")
    print("=" * 60)
    app.run(host='0.0.0.0', port=port, debug=False)
