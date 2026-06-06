# scripts/run_backtest_real.py
import psycopg2
import pandas as pd
from backtest_engine import NDI_Backtest

conn = psycopg2.connect("dbname=signaliq host=/var/run/postgresql")
# Cargar precios + NDI (de Layer 4)
df = pd.read_sql("""
    SELECT p.date, p.ticker, p.adj_close as close, 
           COALESCE(s.ndi, 0) as ndi,
           COALESCE(s.confidence, 'Low') as confidence
    FROM raw.prices p
    LEFT JOIN layer4.signals s ON p.ticker = s.ticker AND p.date = s.date
    ORDER BY p.date
""", conn)
conn.close()

bt = NDI_Backtest(threshold=1.5, hold_days=5)
results = bt.run_backtest(df)
print(results)