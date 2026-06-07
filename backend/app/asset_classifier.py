"""Clasificador automático de activos usando Yahoo Finance"""

import yfinance as yf
import re

class AssetClassifier:
    """Clasifica automáticamente cualquier ticker usando Yahoo Finance"""
    
    @staticmethod
    def classify(ticker):
        """
        Clasifica un ticker automáticamente.
        Retorna: dict con type, name, y metadata
        """
        ticker_upper = ticker.upper()
        
        try:
            stock = yf.Ticker(ticker_upper)
            info = stock.info
            
            # Método 1: Usar quoteType de Yahoo Finance
            quote_type = info.get('quoteType', '')
            
            if quote_type == 'CRYPTOCURRENCY':
                return {
                    'type': 'crypto',
                    'name': info.get('longName', info.get('shortName', ticker_upper)),
                    'symbol': ticker_upper,
                    'method': 'yahoo_quote_type'
                }
            
            elif quote_type == 'CURRENCY':
                return {
                    'type': 'forex',
                    'name': info.get('longName', info.get('shortName', ticker_upper)),
                    'symbol': ticker_upper,
                    'method': 'yahoo_quote_type'
                }
            
            elif quote_type == 'ETF':
                return {
                    'type': 'etf',
                    'name': info.get('longName', info.get('shortName', ticker_upper)),
                    'sector': info.get('sector', 'ETF'),
                    'method': 'yahoo_quote_type'
                }
            
            elif quote_type == 'EQUITY':
                return {
                    'type': 'stock',
                    'name': info.get('longName', info.get('shortName', ticker_upper)),
                    'sector': info.get('sector', 'Unknown'),
                    'industry': info.get('industry', 'Unknown'),
                    'market': info.get('market', 'US'),
                    'method': 'yahoo_quote_type'
                }
            
            # Método 2: Inferir por patrones
            if ticker_upper.endswith('-USD') or ticker_upper.endswith('-USDT'):
                return {
                    'type': 'crypto',
                    'name': ticker_upper.replace('-USD', '').replace('-USDT', ''),
                    'symbol': ticker_upper,
                    'method': 'pattern'
                }
            
            # Método 3: Inferir por información disponible
            if info.get('regularMarketPrice') is not None:
                # Tiene precio de mercado, probablemente acción o ETF
                if info.get('yield') is not None:
                    return {
                        'type': 'etf',
                        'name': info.get('longName', ticker_upper),
                        'method': 'inference'
                    }
                else:
                    return {
                        'type': 'stock',
                        'name': info.get('longName', info.get('shortName', ticker_upper)),
                        'sector': info.get('sector', 'Unknown'),
                        'method': 'inference'
                    }
            
            # Método 4: Verificar si es par de divisas
            if re.match(r'^[A-Z]{3}[=]?[A-Z]{3}$', ticker_upper):
                return {
                    'type': 'forex',
                    'name': f"{ticker_upper[:3]}/{ticker_upper[-3:]}",
                    'symbol': ticker_upper,
                    'method': 'pattern_forex'
                }
            
            # Default: desconocido pero intentar como acción
            return {
                'type': 'unknown',
                'name': ticker_upper,
                'method': 'fallback'
            }
            
        except Exception as e:
            # Fallback por patrones cuando Yahoo Finance falla
            return AssetClassifier._fallback_classify(ticker_upper)
    
    @staticmethod
    def _fallback_classify(ticker):
        """Clasificación de respaldo sin API"""
        # Patrones para forex
        forex_major = ['USD', 'EUR', 'GBP', 'JPY', 'CHF', 'CAD', 'AUD', 'NZD']
        forex_latam = ['BOB', 'ARS', 'BRL', 'CLP', 'PEN', 'UYU', 'PYG', 'COP', 'MXN']
        
        if ticker in forex_major:
            return {'type': 'forex', 'name': f'{ticker} Currency', 'category': 'major', 'method': 'fallback'}
        
        if ticker in forex_latam:
            return {'type': 'forex', 'name': f'{ticker} Currency', 'category': 'latam', 'method': 'fallback'}
        
        # Patrones para crypto
        crypto = ['BTC', 'ETH', 'SOL', 'XRP', 'ADA', 'DOGE', 'MATIC', 'DOT', 'LINK', 'AVAX']
        if ticker in crypto:
            return {'type': 'crypto', 'name': ticker, 'method': 'fallback'}
        
        # Default como acción
        return {'type': 'stock', 'name': ticker, 'method': 'fallback'}

# Instancia global
classifier = AssetClassifier()
classifier = AssetClassifier()
