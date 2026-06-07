-- 1. Noticias originales con deduplicación
CREATE TABLE IF NOT EXISTS news_articles (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT,
    source VARCHAR(100),
    url TEXT UNIQUE,
    content_hash VARCHAR(64) UNIQUE,
    published_at TIMESTAMP,
    raw_data JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 2. Configuración del score
CREATE TABLE IF NOT EXISTS score_configs (
    id SERIAL PRIMARY KEY,
    version VARCHAR(20) NOT NULL UNIQUE,
    config JSONB NOT NULL,
    is_active BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 3. Predicciones
CREATE TABLE IF NOT EXISTS signal_predictions (
    id SERIAL PRIMARY KEY,
    news_article_id INTEGER REFERENCES news_articles(id),
    score_config_id INTEGER REFERENCES score_configs(id),
    ticker VARCHAR(10) NOT NULL,
    score FLOAT NOT NULL,
    confidence FLOAT,
    signal VARCHAR(20),
    strength VARCHAR(20),
    sentiment_score FLOAT,
    relevance_score FLOAT,
    source_quality_score FLOAT,
    event_type_score FLOAT,
    event_type VARCHAR(50),
    event_confidence FLOAT,
    explanation TEXT,
    price_at_signal FLOAT,
    price_1d FLOAT,
    price_3d FLOAT,
    price_7d FLOAT,
    movement_1d FLOAT,
    movement_3d FLOAT,
    movement_7d FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_news_hash ON news_articles(content_hash);
CREATE INDEX IF NOT EXISTS idx_predictions_ticker ON signal_predictions(ticker);
CREATE INDEX IF NOT EXISTS idx_predictions_score ON signal_predictions(score);
CREATE INDEX IF NOT EXISTS idx_predictions_created ON signal_predictions(created_at);

-- Insertar configuración inicial (v1.0)
INSERT INTO score_configs (version, config, is_active) 
VALUES ('v1.0', '{"sentiment_weight": 0.35, "relevance_weight": 0.25, "source_weight": 0.20, "event_weight": 0.20}', true)
ON CONFLICT (version) DO NOTHING;
