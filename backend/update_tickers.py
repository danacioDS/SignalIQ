import os
import sys
sys.path.append('.')

# Configurar entorno
os.environ.setdefault('DATABASE_URL', 'postgresql://daniel@localhost:5432/signaliq')

from app.db import get_connection, put_connection, init_pool

def add_tickers():
    """Agregar nuevos tickers a la tabla monitored_assets"""
    # Inicializar pool
    init_pool()
    
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        # Crear schema config si no existe
        cur.execute("CREATE SCHEMA IF NOT EXISTS config")
        
        # Crear tabla si no existe
        cur.execute("""
            CREATE TABLE IF NOT EXISTS config.monitored_assets (
                ticker VARCHAR(10) PRIMARY KEY,
                name VARCHAR(100),
                sector VARCHAR(50),
                active BOOLEAN DEFAULT true,
                added_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # Lista de nuevos tickers
        new_tickers = [
            ('GOOGL', 'Alphabet Inc.', 'Technology'),
            ('META', 'Meta Platforms Inc.', 'Technology'),
            ('AMZN', 'Amazon.com Inc.', 'Consumer Cyclical'),
            ('AMD', 'Advanced Micro Devices', 'Technology'),
            ('KO', 'Coca-Cola Co.', 'Consumer Defensive'),
            ('JPM', 'JPMorgan Chase & Co.', 'Financial')
        ]
        
        # Insertar tickers
        for ticker, name, sector in new_tickers:
            cur.execute("""
                INSERT INTO config.monitored_assets (ticker, name, sector, active)
                VALUES (%s, %s, %s, true)
                ON CONFLICT (ticker) DO UPDATE SET
                    name = EXCLUDED.name,
                    sector = EXCLUDED.sector,
                    active = true
            """, (ticker, name, sector))
            print(f"✅ {ticker} - {name}")
        
        conn.commit()
        
        # Mostrar total
        cur.execute("SELECT COUNT(*) FROM config.monitored_assets WHERE active = true")
        total = cur.fetchone()[0]
        print(f"\n📊 Total tickers activos: {total}")
        
    except Exception as e:
        print(f"Error: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            put_connection(conn)

if __name__ == "__main__":
    add_tickers()
