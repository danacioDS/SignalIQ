-- Migration 002: Fix missing schema (raw functions + config tables)
-- writer.py expects raw.insert_price_record() and raw.insert_headline_record()

BEGIN;

CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS config;
CREATE SCHEMA IF NOT EXISTS layer4;

-- Wrapper for write_price() call: raw.insert_price_record(ticker, vendor, date, open, high, low, close, adj_close, volume, FALSE, NULL, ingestion_run_id)
CREATE OR REPLACE FUNCTION raw.insert_price_record(
    p_ticker TEXT,
    p_vendor TEXT,
    p_date DATE,
    p_open NUMERIC,
    p_high NUMERIC,
    p_low NUMERIC,
    p_close NUMERIC,
    p_adj_close NUMERIC,
    p_volume NUMERIC,
    p_is_correction BOOLEAN,
    p_correction_id BIGINT,
    p_ingestion_run_id TEXT
) RETURNS VOID AS $$
BEGIN
    INSERT INTO public.prices (ticker, source, price_date, open, high, low, close, volume)
    VALUES (p_ticker, p_vendor, p_date, p_open, p_high, p_low, p_close, p_volume)
    ON CONFLICT (ticker, price_date, source) DO NOTHING;
END;
$$ LANGUAGE plpgsql;

-- Wrapper for write_headline() call: raw.insert_headline_record(source_id, headline, article_url, published_at, author, content_snippet, ingestion_run_id)
CREATE OR REPLACE FUNCTION raw.insert_headline_record(
    p_source_id INT,
    p_headline TEXT,
    p_url TEXT,
    p_published_at TIMESTAMP,
    p_author TEXT,
    p_content_snippet TEXT,
    p_ingestion_run_id TEXT
) RETURNS VOID AS $$
DECLARE
    v_source_name TEXT;
BEGIN
    SELECT source_name INTO v_source_name FROM config.news_sources WHERE id = p_source_id;
    INSERT INTO public.headlines (ticker, headline_date, title, summary, source, url, author)
    VALUES ('UNKNOWN', p_published_at::DATE, p_headline, p_content_snippet, COALESCE(v_source_name, 'rss'), p_url, p_author)
    ON CONFLICT (url) DO NOTHING;
END;
$$ LANGUAGE plpgsql;

-- Views for compatibility
CREATE OR REPLACE VIEW raw.prices AS SELECT * FROM public.prices;
CREATE OR REPLACE VIEW raw.news_headlines AS SELECT * FROM public.headlines;

-- config.news_sources table (required by get_source_id())
CREATE TABLE IF NOT EXISTS config.news_sources (
    id SERIAL PRIMARY KEY,
    source_name VARCHAR(100) UNIQUE NOT NULL,
    feed_url TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

INSERT INTO config.news_sources (source_name, feed_url) VALUES
    ('reuters', 'http://feeds.reuters.com/reuters/businessNews'),
    ('ap', 'http://hosted2.ap.org/atom/APDEFAULT/3d281c11a6144e37a6f192db3e22611e'),
    ('yahoo_general', 'https://finance.yahoo.com/news/rssindex'),
    ('yahoo_ticker', 'https://finance.yahoo.com/rss/headline'),
    ('cnbc', 'https://www.cnbc.com/id/100003114/device/rss/rss.html'),
    ('marketwatch', 'http://feeds.marketwatch.com/marketwatch/topstories')
ON CONFLICT (source_name) DO NOTHING;

COMMIT;
