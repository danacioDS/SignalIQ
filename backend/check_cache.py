#!/usr/bin/env python
"""
Verificar estado del caché
"""
import requests
import json

TICKERS = ['AAPL', 'MSFT', 'NVDA', 'TSLA', 'JPM']

def check_cache():
    print("🔍 Verificando caché...")
    print("-" * 50)
    
    for ticker in TICKERS:
        try:
            url = f"https://signaliq-api.onrender.com/api/ticker/{ticker}"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                cache = data.get('cache', {})
                price = data.get('price', 'N/A')
                
                # Contar cuántos items están en caché
                cached_items = sum(1 for v in cache.values() if v)
                total_items = len(cache)
                
                status = "🟢" if cached_items > 0 else "🔴"
                print(f"{status} {ticker}: ${price} | Caché: {cached_items}/{total_items}")
            else:
                print(f"❌ {ticker}: Error {response.status_code}")
                
        except Exception as e:
            print(f"❌ {ticker}: {str(e)}")
    
    print("-" * 50)

if __name__ == "__main__":
    check_cache()