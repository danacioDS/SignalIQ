#!/usr/bin/env python3
"""
Backtest para validar el NDI en SignalIQ.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.app.main import calculate_ndi
import json
from datetime import datetime

tickers = ['NVDA', 'AAPL', 'MSFT', 'TSLA', 'GOOGL', 'META']
results = []

print("=== BACKTEST NDI ===\n")
print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Tickers: {', '.join(tickers)}\n")

for ticker in tickers:
    try:
        result = calculate_ndi(ticker)
        if isinstance(result, dict):
            results.append({
                'ticker': ticker,
                'price': result.get('price', 0),
                'sentiment': result.get('sentiment', 0),
                'momentum': result.get('momentum', 0),
                'ndi': result.get('ndi', 0),
                'regime': result.get('regime', 'UNKNOWN'),
                'confidence': result.get('confidence', 0)
            })
            print(f"{ticker}:")
            print(f"  Price: ${result.get('price', 0):.2f}")
            print(f"  Sentiment: {result.get('sentiment', 0):.4f}")
            print(f"  Momentum: {result.get('momentum', 0):.4f}")
            print(f"  NDI: {result.get('ndi', 0):.4f}")
            print(f"  Regime: {result.get('regime', 'UNKNOWN')}")
            print()
    except Exception as e:
        print(f"{ticker}: ERROR - {e}")

# Guardar resultados
with open('backtest_results.json', 'w') as f:
    json.dump({
        'timestamp': datetime.now().isoformat(),
        'results': results
    }, f, indent=2)

print(f"\nResultados guardados en backtest_results.json")
