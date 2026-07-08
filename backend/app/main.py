"""
SignalIQ API - Con noticias reales
"""
import os
import logging
from datetime import datetime, timezone
from flask import Flask, jsonify, request
from flask_cors import CORS
import yfinance as yf
import numpy as np

# Importación directa (layers ahora está en app/)
from layers.layer4_measurement import calculate_narrative_divergence_index
from layers.layer3_sentiment import Layer3Sentiment
from layers.layer3_momentum import Layer3Momentum
from news_pipeline import process_news_for_ticker

app = Flask(__name__)
CORS(app, origins=[
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://signaliq-zeta-ten.vercel.app",
    "https://signaliq-zeta.vercel.app",
    "https://signaliq-l8mi.onrender.com"
])

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicializar Layer 3
sentiment_engine = Layer3Sentiment()
momentum_engine = Layer3Momentum()

# ============================================================
# FUNCIONES DE ANÁLISIS
# ============================================================

def classify_regime(ndi):
    if ndi > 2.0:
        return {'regime': 'EXTREME OVERHEATING', 'color': 'red', 'label': 'SELL'}
    elif ndi > 1.5:
        return {'regime': 'OVERHEATING', 'color': 'orange', 'label': 'REDUCE'}
    elif ndi > 0.5:
        return {'regime': 'WATCHING', 'color': 'orange', 'label': 'MONITOR'}
    elif ndi > -0.5:
        return {'regime': 'NEUTRAL', 'color': 'yellow', 'label': 'HOLD'}
    elif ndi > -1.5:
        return {'regime': 'ALIGNED', 'color': 'green', 'label': 'BUY'}
    elif ndi > -2.0:
        return {'regime': 'STRONG UNDERVALUED', 'color': 'green', 'label': 'STRONG BUY'}
    else:
        return {'regime': 'CAPITULATION', 'color': 'blue', 'label': 'ACCUMULATE'}

def calculate_sentiment_zscore(news_sentiment):
    """
    Calcula el z-score del sentimiento basado en noticias.
    Usa valores históricos simulados para la demostración.
    """
    if news_sentiment is None:
        return 0.0
    
    # Por ahora, usamos una transformación simple
    # En producción, esto vendría de Layer 3
    return float(news_sentiment)

def calculate_momentum_zscore(price_history):
    """
    Calcula el z-score del momentum basado en precios históricos.
    """
    if not price_history or len(price_history) < 2:
        return 0.0
    
    # Calcular retornos diarios
    returns = []
    for i in range(1, len(price_history)):
        if price_history[i-1] != 0:
            returns.append((price_history[i] - price_history[i-1]) / price_history[i-1])
    
    if not returns:
        return 0.0
    
    # Calcular z-score del último retorno
    last_return = returns[-1]
    mean_return = np.mean(returns)
    std_return = np.std(returns) if np.std(returns) > 0 else 1.0
    
    return (last_return - mean_return) / std_return

# ============================================================
# RUTAS
# ============================================================

@app.route('/')
def root():
    return jsonify({
        'name': 'SignalIQ API',
        'version': '2026-07-07',
        'status': 'operational',
        'mode': 'yfinance_with_news'
    })

@app.route('/health')
@app.route('/api/health')
def health():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'mode': 'yfinance_with_news'
    })

@app.route('/api/ticker/analysis/<ticker>')
def ticker_analysis(ticker):
    try:
        ticker = ticker.upper()
        logger.info(f"📊 Analizando {ticker}")
        
        # 1. Obtener noticias REALES (SIEMPRE)
        news_data = process_news_for_ticker(ticker)
        news_items = []
        for h, s in zip(news_data['headlines'], news_data['scores']):
            news_items.append({
                'headline': h,
                'sentiment': s,
                'source': 'RSS Feed'
            })
        
        # 2. Intentar obtener precio (yfinance)
        price_data = {
            'available': False,
            'price': None,
            'hist': []
        }
        
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="60d")
            if not hist.empty:
                price_data['available'] = True
                price_data['price'] = hist['Close'].iloc[-1]
                price_data['hist'] = hist['Close'].tolist()
                logger.info(f"✅ Precio obtenido para {ticker}: {price_data['price']}")
        except Exception as e:
            logger.warning(f"⚠️ Error al obtener precio para {ticker}: {str(e)}")
        
        # 3. Calcular z-scores usando Layer 3
        sentiment_zscore = calculate_sentiment_zscore(news_data['sentiment'])
        momentum_zscore = calculate_momentum_zscore(price_data['hist']) if price_data['available'] else 0.0
        
        # 4. Calcular NDI (Layer 4)
        ndi = calculate_narrative_divergence_index(sentiment_zscore, momentum_zscore)
        if ndi is None:
            ndi = 0.0
            logger.warning(f"⚠️ NDI calculado como None para {ticker}, usando 0.0")
        
        regime = classify_regime(ndi)
        
        # 5. Obtener información de la empresa (si está disponible)
        company_name = ticker
        sector = 'Unknown'
        industry = 'Unknown'
        try:
            if price_data['available']:
                info = yf.Ticker(ticker).info
                company_name = info.get('longName', info.get('shortName', ticker))
                sector = info.get('sector', 'Unknown')
                industry = info.get('industry', 'Unknown')
        except:
            pass
        
        # 6. Construir respuesta
        response = {
            'ticker': ticker,
            'companyName': company_name,
            'sector': sector,
            'industry': industry,
            'price_unavailable': not price_data['available'],
            'ndi': round(ndi, 3),
            'statusLabel': regime['regime'],
            'statusColor': regime['color'],
            'updatedAt': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S'),
            'price': price_data['price'] if price_data['available'] else None,
            'quantitativeMetrics': {
                'sentiment': round(sentiment_zscore, 3),
                'momentum': round(momentum_zscore, 3),
                'divergence': round(ndi, 3),
                'sourcesCount': len(news_data['headlines'])
            },
            'narrativeBreakdown': {
                'consensusPercentage': 74,
                'consensusLabel': 'Alto',
                'intensityPercentage': 52,
                'intensityLabel': 'Moderada',
                'dispersionValue': 0.22,
                'dispersionLabel': 'Baja',
                'mediaBias': {
                    'centerBizPercentage': 60,
                    'leftPercentage': 20,
                    'rightPercentage': 20
                }
            },
            'narrativeExhaustion': {
                'level': 'BAJA',
                'conditionsObserved': 0,
                'totalConditions': 3,
                'conditionsDetails': [],
                'disclaimer': 'Feature en fase beta.',
                'isBeta': True
            },
            'aiInterpretation': f"{ticker}: NDI {ndi:.3f} - {regime['regime']}. {news_data['count']} noticias procesadas con sentimiento {news_data['sentiment']:.3f}.",
            'newsSummary': {
                'items': news_items,
                'positiveCount': sum(1 for s in news_data['scores'] if s > 0.1),
                'negativeCount': sum(1 for s in news_data['scores'] if s < -0.1),
                'averageSentiment': news_data['sentiment']
            },
            'relativeContext': {
                'sectorName': sector,
                'comparison': {
                    'tickerSentiment': round(sentiment_zscore, 3),
                    'sectorSentiment': 0,
                    'sentimentDifference': 0,
                    'sentimentLabel': '🟢 en línea con el sector',
                    'tickerConsensus': 50,
                    'sectorConsensus': 50,
                    'consensusDifference': 0,
                    'consensusLabel': '🟢 en línea con el sector',
                    'tickerExhaustion': 'BAJA',
                    'sectorExhaustion': 'BAJA',
                    'exhaustionLabel': '🟢 en línea con el sector'
                },
                'sectorRanking': [
                    {'rank': 1, 'ticker': ticker, 'companyName': company_name,
                     'ndi': round(ndi, 3), 'regimeLabel': regime['label'], 'regimeColor': regime['color']}
                ],
                'insight': f"{ticker}: NDI {ndi:.3f} - {regime['regime']}. Sentimiento de noticias: {news_data['sentiment']:.3f}"
            }
        }
        
        # 7. Si no hay precio, agregar mensaje adicional
        if not price_data['available']:
            response['message'] = "Precio no disponible temporalmente, pero las noticias se muestran correctamente."
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"❌ Error en ticker_analysis: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/tickers')
def get_tickers():
    return jsonify({
        'tickers': ['NVDA', 'AAPL', 'MSFT', 'TSLA', 'GOOGL', 'META', 'AMD', 'AMZN', 'JPM', 'KO'],
        'count': 10
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"🚀 SignalIQ API en puerto {port}")
    logger.info("📊 Usando yfinance + noticias reales")
    app.run(host='0.0.0.0', port=port, debug=False)