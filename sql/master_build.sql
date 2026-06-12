-- SignalIQ Master Build
-- Executes all schema migrations in dependency order
-- Usage: psql -d signaliq -f master_build.sql

\echo '=== SignalIQ Master Build ==='
\echo 'Building Layer 2 schema...'

\i 001_create_layer2_schema.sql

\echo '=== Build complete ==='
