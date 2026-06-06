"""Backtest con simulación mejorada"""

import numpy as np
import pandas as pd
from backtest_engine import NDI_Backtest

def generate_realistic_data(days=500):
    """Genera datos más realistas"""
    np.random.seed(42)
    dates = pd.date_range(end='2025-06-05', periods=days, freq='D')
    tickers = ['NVDA', 'AAPL', 'MSFT']
    
    data = []
    for ticker in tickers:
        # Parámetros específicos por ticker
        if ticker == 'NVDA':
            mu, sigma = 0.0012, 0.025  # Mayor crecimiento
        elif ticker == 'AAPL':
            mu, sigma = 0.0006, 0.018
        else:
            mu, sigma = 0.0008, 0.020
        
        price = 100
        ndi = 0
        
        for d in dates:
            # Precio GBM
            price *= np.exp(np.random.normal(mu - sigma**2/2, sigma))
            
            # NDI mean-reverting con ruido
            ndi = 0.95 * ndi + np.random.normal(0, 0.3)
            ndi = np.clip(ndi, -2.5, 2.5)
            
            # Confianza
            if abs(ndi) > 1.2:
                conf = np.random.choice(['High', 'Medium'], p=[0.4, 0.6])
            elif abs(ndi) > 0.5:
                conf = 'Medium'
            else:
                conf = 'Low'
            
            data.append({'date': d, 'ticker': ticker, 'close': price, 'ndi': ndi, 'confidence': conf})
    
    return pd.DataFrame(data)

# Ejecutar
df = generate_realistic_data(500)
print(f"📊 Datos generados: {len(df)} filas")

for th in [1.0, 1.2, 1.5, 1.8, 2.0]:
    bt = NDI_Backtest(threshold=th, hold_days=5)
    res = bt.run_backtest(df)
    if 'error' not in res:
        print(f"Th={th}: Ret={res['total_return']:.2%}, Sharpe={res['sharpe_ratio']:.2f}, Trades={res['num_trades']}")
