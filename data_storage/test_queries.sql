-- SignalIQ Test Queries
-- Validates Layer 2 schema and data integrity
-- Usage: psql -d signaliq -f test_queries.sql

\echo '=== Schema Verification ==='

SELECT table_name, table_type
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;

\echo '=== Latest prices per ticker ==='

SELECT DISTINCT ON (ticker)
    ticker,
    price_date,
    close,
    source
FROM prices
ORDER BY ticker, price_date DESC;

\echo '=== Recent headlines per ticker ==='

SELECT DISTINCT ON (ticker)
    ticker,
    headline_date,
    LEFT(title, 60) AS title_preview,
    source
FROM headlines
ORDER BY ticker, headline_date DESC;

\echo '=== Latest NDI signals ==='

SELECT DISTINCT ON (ticker)
    ticker,
    signal_date,
    ndi,
    regime,
    confidence
FROM ndi_signals
ORDER BY ticker, signal_date DESC;

\echo '=== Row counts ==='

SELECT 'prices' AS table_name, COUNT(*) AS row_count FROM prices
UNION ALL
SELECT 'headlines', COUNT(*) FROM headlines
UNION ALL
SELECT 'ndi_signals', COUNT(*) FROM ndi_signals
ORDER BY table_name;

\echo '=== Validation complete ==='
