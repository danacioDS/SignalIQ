#!/usr/bin/env python
"""
Precargar caché para todos los tickers
Ejecutar: python preload_cache.py
"""
import requests
import time
import json

TICKERS = ['AAPL', 'MSFT', 'NVDA', 'GOOGL', 'META', 'AMD', 'AMZN', 'TSLA', 'JPM', 'KO']
API_URL = "https://signaliq-api.onrender.com/api/ticker/"

def preload():
    print("🔄 Precargando caché...")
    
    for ticker in TICKERS:
        try:
            url = f"{API_URL}{ticker}"
            start = time.time()
            response = requests.get(url, timeout=15)
            elapsed = (time.time() - start) * 1000
            
            if response.status_code == 200:
                data = response.json()
                cached = data.get('cache', {})
                print(f"✅ {ticker}: {elapsed:.0f}ms | cache: {cached}")
            else:
                print(f"❌ {ticker}: Error {response.status_code}")
            
            time.sleep(0.3)
            
        except Exception as e:
            print(f"❌ {ticker}: {str(e)}")
    
    print("✅ Precarga completada")

if __name__ == "__main__":
    preload()