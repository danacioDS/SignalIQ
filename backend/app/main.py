"""SignalIQ API - Con SignalIQ Score Integrado"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import os
import google.generativeai as genai
from app.scoring.signal_score import SignalIQScore
from app.classification.event_classifier import EventClassifier

app = Flask(__name__)
CORS(app)

# Inicializar SignalIQ Score
signal_scorer = SignalIQScore()
event_classifier = EventClassifier()

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
        print("✅ Gemini initialized successfully")
    except Exception as e:
        print(f"❌ Gemini initialization error: {e}")
else:
    print("❌ No API keys found in environment")

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'ok',
        'service': 'SignalIQ',
        'mode': 'REAL' if model else 'MOCK',
        'features': ['analysis', 'signal_score', 'event_classification']
    })

@app.route('/analyze/<ticker>', methods=['GET'])
def analyze(ticker):
    """Análisis original con Gemini"""
    if not model:
        return jsonify({'error': 'Gemini not configured'}), 500
    
    try:
        ticker = ticker.upper()
        prompt = f"Analyze {ticker} stock briefly. Give recommendation BUY/SELL/HOLD in 2 sentences."
        
        response = model.generate_content(prompt)
        analysis = response.text
        
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

@app.route('/score/<ticker>', methods=['GET'])
def get_signal_score(ticker):
    """Nuevo endpoint: SignalIQ Score con explicación"""
    try:
        ticker = ticker.upper()
        
        # Por ahora, usamos datos de ejemplo
        # En producción, esto vendría de noticias reales
        news_item = {
            'title': f'{ticker} market update',
            'content': f'Recent developments for {ticker} show positive momentum',
            'ticker': ticker,
            'source': 'bloomberg',
            'sentiment': 'neutral'
        }
        
        # Calcular SignalIQ Score
        score_result = signal_scorer.calculate(news_item)
        
        return jsonify({
            'success': True,
            'ticker': ticker,
            'timestamp': datetime.now().isoformat(),
            'signal_score': score_result
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/classify', methods=['POST'])
def classify_news():
    """Clasificar evento de una noticia"""
    try:
        data = request.get_json()
        title = data.get('title', '')
        content = data.get('content', '')
        
        result = event_classifier.classify(title, content)
        
        return jsonify({
            'success': True,
            'classification': result
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
        'mode': 'REAL' if model else 'MOCK',
        'signal_score_version': signal_scorer.VERSION
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

@app.route('/api/stats', methods=['GET'])
def get_api_stats():
    """Get system statistics from database"""
    import psycopg2
    
    try:
        db_url = os.environ.get('DATABASE_URL')
        if not db_url:
            return jsonify({'error': 'Database not configured'}), 500
        
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        cur.execute("SELECT COUNT(*) FROM signal_predictions")
        total_signals = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM signal_predictions WHERE signal = 'BULLISH'")
        bullish = cur.fetchone()[0]
        
        cur.execute("SELECT AVG(score) FROM signal_predictions WHERE score IS NOT NULL")
        avg_score = cur.fetchone()[0] or 0
        
        cur.execute("SELECT COUNT(DISTINCT ticker) FROM signal_predictions")
        active_tickers = cur.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'success': True,
            'total_signals': total_signals,
            'bullish_signals': bullish,
            'average_score': round(float(avg_score), 1),
            'active_tickers': active_tickers
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/signals', methods=['GET'])
def get_api_signals():
    """Get all signals from database"""
    import psycopg2
    
    try:
        db_url = os.environ.get('DATABASE_URL')
        if not db_url:
            return jsonify({'error': 'Database not configured'}), 500
        
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        cur.execute("""
            SELECT ticker, score, signal, strength, explanation, 
                   price_at_signal, created_at
            FROM signal_predictions
            ORDER BY created_at DESC
            LIMIT 50
        """)
        
        signals = []
        for row in cur.fetchall():
            signals.append({
                'ticker': row[0],
                'score': row[1],
                'signal': row[2],
                'strength': row[3],
                'explanation': row[4],
                'price_at_signal': row[5],
                'timestamp': row[6].isoformat() if row[6] else None
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'count': len(signals),
            'signals': signals
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
