-- SignalIQ Rollback
-- Drops all Layer 2 tables
-- Usage: psql -d signaliq -f rollback.sql

\echo '=== SignalIQ Rollback ==='

DROP TABLE IF EXISTS ndi_signals CASCADE;
DROP TABLE IF EXISTS headlines CASCADE;
DROP TABLE IF EXISTS prices CASCADE;

\echo '=== Rollback complete ==='
