import psycopg2
import pandas as pd

conn = psycopg2.connect("dbname=signaliq")

# Consulta corregida: usa price_date en lugar de date
df = pd.read_sql("""
    SELECT 
        p.ticker,
        p.price_date as date,
        p.close,
        s.ndi,
        s.regime,
        s.signal_state,
        s.confidence
    FROM prices p
    LEFT JOIN layer4.signals s ON p.ticker = s.ticker AND p.price_date = s.signal_date
    WHERE p.ticker IN ('NVDA', 'AAPL', 'MSFT', 'TSLA')
    ORDER BY p.ticker, p.price_date
""", conn)

print(f"✅ Datos cargados: {len(df)} filas")
print(f"\n📊 Tickers disponibles: {df['ticker'].unique()}")
print(f"\n📅 Rango de fechas: {df['date'].min()} a {df['date'].max()}")
print(f"\n🔍 Señales NDI no nulas: {df['ndi'].notna().sum()}")

if df['ndi'].notna().sum() > 0:
    print("\n📈 Últimas señales:")
    print(df[df['ndi'].notna()].tail(10).to_string())

conn.close()
