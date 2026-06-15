#!/usr/bin/env python3
"""Valida poder predictivo del NDI"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

import pandas as pd
import numpy as np
from app.db import init_pool, get_connection

def fetch_data(conn, days_forward=5):
    query = f"""
    WITH ndi AS (
        SELECT signal_date, ticker, ndi as ndi_score
        FROM ndi_signals
        WHERE ndi IS NOT NULL AND signal_date >= '2024-01-01'
        LIMIT 10000
    ),
    prices AS (
        SELECT ticker, price_date as date, close as close_adj
        FROM prices
        WHERE close IS NOT NULL
    )
    SELECT 
        n.signal_date as date,
        n.ticker,
        n.ndi_score,
        p.close_adj as price,
        LEAD(p.close_adj, {days_forward}) OVER (
            PARTITION BY n.ticker ORDER BY n.signal_date
        ) as future_price
    FROM ndi n
    JOIN prices p ON p.ticker = n.ticker AND p.date = n.signal_date
    """
    with conn.cursor() as cur:
        cur.execute(query)
        cols = [d[0] for d in cur.description]
        df = pd.DataFrame(cur.fetchall(), columns=cols)
    df['forward_return'] = (df['future_price'] - df['price']) / df['price']
    return df.dropna()

def main():
    init_pool()
    conn = get_connection()
    
    for days in [1, 5, 20]:
        df = fetch_data(conn, days)
        if len(df) < 100:
            print(f"Skip {days}d: solo {len(df)} registros")
            continue
        
        corr = df['ndi_score'].corr(df['forward_return'])
        
        extreme = df[abs(df['ndi_score']) > 2]
        if len(extreme) > 0:
            correct = ((extreme['ndi_score'] > 0) & (extreme['forward_return'] > 0)) | \
                      ((extreme['ndi_score'] < 0) & (extreme['forward_return'] < 0))
            accuracy = correct.mean()
        else:
            accuracy = None
        
        df['position'] = 0
        df.loc[df['ndi_score'] > 1, 'position'] = 1
        df.loc[df['ndi_score'] < -1, 'position'] = -1
        df['strat_return'] = df['position'].shift(1) * df['forward_return']
        sharpe = df['strat_return'].mean() / df['strat_return'].std() * (252 ** 0.5) if df['strat_return'].std() > 0 else 0
        
        print(f"\n{days} días:")
        print(f"  Correlación: {corr:.3f}")
        if accuracy:
            print(f"  Precisión (|NDI|>2): {accuracy:.1%}")
        print(f"  Sharpe ratio: {sharpe:.2f}")
    
    conn.close()

if __name__ == "__main__":
    main()
