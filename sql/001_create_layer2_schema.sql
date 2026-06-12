-- Layer 2: Data Storage Schema
-- PostgreSQL schema for SignalIQ persistent storage

BEGIN;

-- Prices table (Layer 1 output)
CREATE TABLE IF NOT EXISTS prices (
    id BIGSERIAL PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    price_date DATE NOT NULL,
    open NUMERIC(14, 4),
    high NUMERIC(14, 4),
    low NUMERIC(14, 4),
    close NUMERIC(14, 4) NOT NULL,
    volume BIGINT,
    source VARCHAR(32) DEFAULT 'yahoo',
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (ticker, price_date, source)
);

-- Headlines table (Layer 1 output) with SHA256 dedup
CREATE TABLE IF NOT EXISTS headlines (
    id BIGSERIAL PRIMARY KEY,
    sha256_hash BYTEA NOT NULL UNIQUE,
    ticker VARCHAR(10) NOT NULL,
    headline_date DATE NOT NULL,
    title TEXT NOT NULL,
    summary TEXT,
    source VARCHAR(64),
    url TEXT,
    author VARCHAR(128),
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_headlines_ticker_date ON headlines (ticker, headline_date);
CREATE INDEX IF NOT EXISTS idx_headlines_sha256 ON headlines (sha256_hash);

-- NDI signals table (Layer 4 output)
CREATE TABLE IF NOT EXISTS ndi_signals (
    id BIGSERIAL PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    signal_date DATE NOT NULL,
    ndi NUMERIC(8, 4),
    ndi_delta NUMERIC(8, 4),
    ndi_trend VARCHAR(32),
    regime VARCHAR(64),
    signal_state VARCHAR(32),
    confidence VARCHAR(32),
    price_modifier VARCHAR(32),
    persistence_days INTEGER DEFAULT 0,
    risk_level VARCHAR(32),
    attention TEXT,
    narrative_score NUMERIC(8, 4),
    momentum_score NUMERIC(8, 4),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (ticker, signal_date)
);

CREATE INDEX IF NOT EXISTS idx_ndi_signals_ticker_date ON ndi_signals (ticker, signal_date);

COMMIT;
