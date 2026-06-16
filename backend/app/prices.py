import yfinance as yf
from flask import Blueprint, jsonify, request
import logging
from datetime import datetime, timedelta

prices_bp = Blueprint('prices', __name__)
logger = logging.getLogger(__name__)

@routing_bp.route('/api/prices/<ticker>', methods=['GET'])
def get_ticker_data(ticker):
    """
    Obtiene datos de Yahoo Finance para un ticker específico.
    """
    try:
        ticker = ticker.upper()
        period = request.args.get('period', '6mo')
        interval = request.args.get('interval', '1d')
        
        logger.info(f"Fetching data for {ticker} - period: {period}, interval: {interval}")
        
        # Obtener datos de Yahoo Finance
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period, interval=interval)
        
        if hist.empty:
            return jsonify({
                'error': f'No data found for ticker: {ticker}',
                'ticker': ticker
            }), 404
        
        # Calcular NDI (simplificado para demo)
        # En producción, esto vendría de la base de datos
        current_price = hist['Close'].iloc[-1]
        prev_price = hist['Close'].iloc[-5] if len(hist) >= 5 else hist['Close'].iloc[0]
        
        # Sentimiento simulado (en producción vendría de Layer 3)
        sentiment = 0.5 + (hist['Close'].pct_change().iloc[-1] * 0.5)
        sentiment = max(0.1, min(0.9, sentiment))
        
        # Momentum (20 días)
        if len(hist) >= 20:
            momentum = (hist['Close'].iloc[-1] / hist['Close'].iloc[-20] - 1) * 100
        else:
            momentum = (hist['Close'].iloc[-1] / hist['Close'].iloc[0] - 1) * 100
        
        # NDI simplificado
        ndi = sentiment - (momentum / 100)
        ndi = max(-2.0, min(2.0, ndi))
        
        # Determinar régimen
        if ndi > 1.5:
            regime = "Overheating"
            color = "red"
        elif ndi > 0.5:
            regime = "Watching"
            color = "yellow"
        else:
            regime = "Aligned"
            color = "green"
        
        return jsonify({
            'ticker': ticker,
            'current_price': round(current_price, 2),
            'prev_price': round(prev_price, 2),
            'sentiment': round(sentiment, 3),
            'momentum': round(momentum, 2),
            'ndi': round(ndi, 3),
            'regime': regime,
            'color': color,
            'confidence': round(70 + (abs(ndi) * 15), 1),
            'recommendation': f"{ticker} shows {regime.lower()} divergence. ",
            'price_history': [
                {
                    'date': date.strftime('%Y-%m-%d'),
                    'close': round(close, 2)
                } for date, close in zip(hist.index[-30:], hist['Close'].iloc[-30:])
            ]
        })
        
    except Exception as e:
        logger.error(f"Error fetching data for {ticker}: {str(e)}")
        return jsonify({
            'error': str(e),
            'ticker': ticker
        }), 500

@routing_bp.route('/api/signals', methods=['GET'])
def get_signals():
    """
    Obtiene señales para múltiples tickers.
    """
    tickers = request.args.get('tickers', 'NVDA,AAPL,MSFT,TSLA,GOOGL,META,AMD,AMZN,JPM,XOM,KO')
    tickers_list = tickers.split(',')
    
    results = []
    for ticker in tickers_list:
        try:
            data = get_ticker_data_sync(ticker)
            results.append(data)
        except Exception as e:
            logger.error(f"Error getting data for {ticker}: {str(e)}")
    
    return jsonify(results)

def get_ticker_data_sync(ticker):
    """Versión síncrona para múltiples tickers."""
    ticker = ticker.upper()
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period='6mo')
        
        if hist.empty:
            return {'ticker': ticker, 'error': 'No data found'}
        
        current_price = hist['Close'].iloc[-1]
        
        # Sentimiento simulado
        sentiment = 0.5 + (hist['Close'].pct_change().iloc[-1] * 0.5)
        sentiment = max(0.1, min(0.9, sentiment))
        
        # Momentum
        if len(hist) >= 20:
            momentum = (hist['Close'].iloc[-1] / hist['Close'].iloc[-20] - 1) * 100
        else:
            momentum = (hist['Close'].iloc[-1] / hist['Close'].iloc[0] - 1) * 100
        
        ndi = sentiment - (momentum / 100)
        ndi = max(-2.0, min(2.0, ndi))
        
        # Régimen
        if ndi > 1.5:
            regime = "Overheating"
            color = "red"
        elif ndi > 0.5:
            regime = "Watching"
            color = "yellow"
        else:
            regime = "Aligned"
            color = "green"
        
        return {
            'ticker': ticker,
            'current_price': round(current_price, 2),
            'sentiment': round(sentiment, 3),
            'momentum': round(momentum, 2),
            'ndi': round(ndi, 3),
            'regime': regime,
            'color': color,
        }
    except Exception as e:
        return {'ticker': ticker, 'error': str(e)}