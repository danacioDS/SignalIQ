#!/usr/bin/env python3
"""Genera señales NDI desde datos reales y guarda en BD"""

import sys
import os
from pathlib import Path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.app.db import init_pool, get_connection
from layers.layer3_orchestrator import Layer3Orchestrator
from layers.layer4_orchestrator import process_batch
from layers.layer4_persistence import PersistenceTracker
from datetime import date, timedelta

def save_to_db(conn, ticker, signal_date, ndi, state, confidence=None, regime=None):
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO ndi_signals (ticker, signal_date, ndi, signal_state, confidence, regime)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (ticker, signal_date) DO UPDATE SET
                ndi = EXCLUDED.ndi,
                signal_state = EXCLUDED.signal_state,
                confidence = EXCLUDED.confidence,
                regime = EXCLUDED.regime
        """, (ticker, signal_date, ndi, state, confidence, regime))
    conn.commit()

def main():
    print("Inicializando...")
    init_pool()
    conn = get_connection()
    
    # Obtener tickers
    with conn.cursor() as cur:
        cur.execute("SELECT DISTINCT ticker FROM prices ORDER BY ticker")
        tickers = [row[0] for row in cur.fetchall()]
    print(f"Tickers: {tickers}")
    
    # Obtener rango de fechas
    with conn.cursor() as cur:
        cur.execute("SELECT MIN(price_date), MAX(price_date) FROM prices")
        row = cur.fetchone()
        min_date, max_date = row[0], row[1]
    print(f"Fechas: {min_date} a {max_date}")
    
    # Limpiar tabla antes de generar
    with conn.cursor() as cur:
        cur.execute("TRUNCATE ndi_signals")
    conn.commit()
    
    # Cargar precios
    print("Cargando precios...")
    orch = Layer3Orchestrator()
    
    with conn.cursor() as cur:
        cur.execute("SELECT ticker, price_date, close FROM prices ORDER BY ticker, price_date")
        count = 0
        for ticker, price_date, close in cur.fetchall():
            orch.process_price(ticker, price_date, float(close))
            count += 1
    print(f"Cargados {count} precios")
    
    # Procesar por día
    tracker_file = Path("/tmp/signaliq_tracker.json")
    if tracker_file.exists():
        tracker_file.unlink()
    
    current = min_date
    end_date = max_date
    day_count = 0
    signal_count = 0
    
    while current <= end_date:
        l3_output = orch.finalize_day(current)
        
        l4_input = {}
        for ticker in tickers:
            if ticker in l3_output and current.isoformat() in l3_output[ticker]:
                inner = l3_output[ticker][current.isoformat()]
                # Obtener price_history
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT close FROM prices 
                        WHERE ticker = %s AND price_date <= %s 
                        ORDER BY price_date DESC LIMIT 20
                    """, (ticker, current))
                    price_history = [float(row[0]) for row in cur.fetchall()][::-1]
                
                if price_history:
                    l4_input[ticker] = {
                        'sentiment_zscore': inner.get('sentiment_zscore'),
                        'momentum_zscore': inner.get('momentum_zscore'),
                        'price_history': price_history
                    }
        
        if l4_input:
            tracker = PersistenceTracker(state_file=tracker_file)
            results = process_batch(l4_input, tracker, current.isoformat())
            tracker.save()
            
            # Guardar en BD
            for ticker, result in results.items():
                if result.get('ndi') is not None:
                    save_to_db(
                        conn,
                        ticker,
                        current,
                        result.get('ndi'),
                        result.get('signal_state', 'UNKNOWN'),
                        result.get('confidence'),
                        result.get('regime')
                    )
                    signal_count += 1
            
            day_count += 1
            if day_count % 10 == 0:
                print(f"Procesado {current}, señales: {len(results)}")
        
        current += timedelta(days=1)
    
    print(f"✅ Completado: {day_count} días procesados")
    print(f"Señales NDI guardadas: {signal_count}")
    
    # Verificar
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM ndi_signals")
        final_count = cur.fetchone()[0]
        print(f"Total en BD: {final_count}")
    
    conn.close()

if __name__ == "__main__":
    main()
