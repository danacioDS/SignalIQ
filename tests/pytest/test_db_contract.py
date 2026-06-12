"""
DB Contract Tests
Verify database can be built from scratch and migrations work.
Skip if DATABASE_URL not set (local dev).
"""

import pytest
import os
import subprocess
import psycopg2

@pytest.mark.integration
def test_migrations_idempotent():
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        pytest.skip("DATABASE_URL not set")
    result1 = subprocess.run(
        ['psql', db_url, '-f', 'data_storage/master_build.sql'],
        capture_output=True, text=True
    )
    result2 = subprocess.run(
        ['psql', db_url, '-f', 'data_storage/master_build.sql'],
        capture_output=True, text=True
    )
    assert result2.returncode == 0, f"Migration not idempotent: {result2.stderr}"

@pytest.mark.integration
def test_raw_functions_exist():
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        pytest.skip("DATABASE_URL not set")
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    cur.execute("""
        SELECT EXISTS (
            SELECT 1 FROM pg_proc
            WHERE proname = 'insert_price_record'
            AND pronamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'raw')
        )
    """)
    assert cur.fetchone()[0], "raw.insert_price_record() missing"
    cur.execute("""
        SELECT EXISTS (
            SELECT 1 FROM pg_proc
            WHERE proname = 'insert_headline_record'
            AND pronamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'raw')
        )
    """)
    assert cur.fetchone()[0], "raw.insert_headline_record() missing"
    conn.close()

@pytest.mark.integration
def test_schemas_exist():
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        pytest.skip("DATABASE_URL not set")
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    for schema in ['raw', 'config', 'layer4']:
        cur.execute("SELECT EXISTS(SELECT 1 FROM information_schema.schemata WHERE schema_name = %s)", (schema,))
        assert cur.fetchone()[0], f"Schema {schema} missing"
    conn.close()
