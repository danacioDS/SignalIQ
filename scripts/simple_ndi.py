#!/usr/bin/env python3
"""Versión simplificada de NDI Signal Generation"""

import psycopg2
from datetime import datetime, timedelta
import numpy as np

def calculate_returns(prices):
    """Calcular retornos diarios"""
    returns = []
    for i in range(1, len(prices)):
        ret = (prices[i][1] - prices[i-1][1]) / prices[i-1][1]
        returns.append((prices[i][0], ret))
    return returns

def main():
    print("=" * 60)
    print("SignalIQ - NDI Signal Generator (Versión Simplificada)")
    print("=" * 60)
    
    # Conectar a BD
    conn = psycopg2.connect("dbname=signaliq host=/var/run/postgresql")
    cur = conn.cursor()
    
    # Obtener tickers con datos
    cur.execute("""
        SELECT ticker, COUNT(*) as cnt, MIN(date), MAX(date)
        FROM raw.prices
        GROUP BY ticker
        HAVING COUNT(*) >= 5
        ORDER BY ticker
    """)
    
    tickers = cur.fetchall()
    print(f"\n📊 Tickers con datos: {len(tickers)}")
    
    for ticker, count, min_date, max_date in tickers:
        print(f"\n{'='*50}")
        print(f"📈 Analizando {ticker}")
        print(f"   Días: {count} ({min_date} a {max_date})")
        
        # Obtener precios
        cur.execute("""
            SELECT date, adj_close
            FROM raw.prices
            WHERE ticker = %s
            ORDER BY date
        """, (ticker,))
        
        prices = cur.fetchall()
        
        # Calcular retornos
        returns = calculate_returns(prices)
        
        if len(returns) >= 2:
            # Estadísticas
            recent_returns = [r[1] for r in returns[-5:]]
            avg_return = np.mean(recent_returns)
            volatility = np.std(recent_returns)
            
            # Obtener noticias relacionadas
            cur.execute("""
                SELECT headline, published_at
                FROM raw.news_headlines
                WHERE headline ILIKE %s
                ORDER BY published_at DESC
                LIMIT 3
            """, (f'%{ticker}%',))
            
            news = cur.fetchall()
            
            # Generar señal NDI simplificada
            print(f"\n   📊 Estadísticas (últimos 5 días):")
            print(f"      Retorno promedio: {avg_return*100:.2f}%")
            print(f"      Volatilidad: {volatility*100:.2f}%")
            
            if len(news) > 0:
                print(f"\n   📰 Noticias relacionadas: {len(news)}")
                for headline, date in news[:2]:
                    print(f"      - {headline[:60]}...")
            else:
                print(f"\n   📰 Sin noticias específicas para {ticker}")
            
            # Señal simple
            if avg_return > 0.02:
                signal = "🟢 BULLISH"
                confidence = min(0.9, avg_return * 10)
            elif avg_return < -0.02:
                signal = "🔴 BEARISH"
                confidence = min(0.9, abs(avg_return) * 10)
            else:
                signal = "⚪ NEUTRAL"
                confidence = 0.5
            
            print(f"\n   🎯 SEÑAL NDI: {signal}")
            print(f"   📊 Confianza: {confidence:.1%}")
            print(f"   💰 Precio actual: ${prices[-1][1]:.2f}")
            
            if len(returns) >= 2:
                last_return = returns[-1][1]
                print(f"   📈 Último movimiento: {last_return*100:+.2f}%")
    
    conn.close()
    print("\n" + "=" * 60)
    print("✅ Análisis completado")

if __name__ == "__main__":
    main()
