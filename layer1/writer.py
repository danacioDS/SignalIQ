import os
import logging
import uuid
import psycopg2
from psycopg2 import sql

logger = logging.getLogger(__name__)

def get_connection():
    """Read DATABASE_URL env var, return psycopg2 connection."""
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL environment variable not set")
    conn = psycopg2.connect(db_url)
    conn.autocommit = False
    return conn


def convert_numpy_types(value):
    """Convert numpy types to Python native types for PostgreSQL."""
    if value is None:
        return None
    # Check for numpy types
    type_name = type(value).__name__
    if type_name == 'float64':
        return float(value)
    elif type_name == 'int64':
        return int(value)
    elif type_name == 'ndarray':
        return value.tolist()
    return value


def write_price(conn, record: dict, ingestion_run_id: str):
    """Write a single price record. Returns inserted id or None on error."""
    try:
        with conn.cursor() as cur:
            # Convert numpy types to Python native
            ticker = convert_numpy_types(record.get("ticker"))
            vendor = convert_numpy_types(record.get("vendor"))
            date = convert_numpy_types(record.get("date"))
            open_price = convert_numpy_types(record.get("open"))
            high = convert_numpy_types(record.get("high"))
            low = convert_numpy_types(record.get("low"))
            close = convert_numpy_types(record.get("close"))
            adj_close = convert_numpy_types(record.get("adj_close"))
            volume = convert_numpy_types(record.get("volume"))
            
            cur.execute(
                """SELECT raw.insert_price_record(
                    %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    FALSE, NULL, %s
                )""",
                (ticker, vendor, date, open_price, high, low, close, adj_close, volume, ingestion_run_id)
            )
            result = cur.fetchone()[0]
            return result
    except psycopg2.UniqueViolation:
        conn.rollback()
        logger.warning("Duplicate price record for %s on %s", record.get("ticker"), record.get("date"))
        return None
    except Exception as e:
        conn.rollback()
        logger.error("DB error writing price for %s: %s", record.get("ticker"), e)
        return None


def write_headline(conn, source_id: int, record: dict, ingestion_run_id: str):
    """Write a single headline record. Returns inserted id or None on error."""
    try:
        with conn.cursor() as cur:
            headline = convert_numpy_types(record.get("headline"))
            article_url = convert_numpy_types(record.get("article_url"))
            published_at = convert_numpy_types(record.get("published_at"))
            author = convert_numpy_types(record.get("author"))
            content_snippet = convert_numpy_types(record.get("content_snippet"))
            
            cur.execute(
                """SELECT raw.insert_headline_record(
                    %s, %s, %s, %s, %s, %s, %s
                )""",
                (source_id, headline, article_url, published_at, author, content_snippet, ingestion_run_id)
            )
            result = cur.fetchone()[0]
            return result
    except psycopg2.UniqueViolation:
        # Rollback is not needed for news (no transaction)
        logger.warning("Duplicate headline for URL: %s", record.get("article_url"))
        return None
    except Exception as e:
        logger.error("DB error writing headline: %s", e)
        return None


def get_source_id(conn, source_name: str):
    """Get source ID from config.news_sources."""
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM config.news_sources WHERE name = %s AND is_active = TRUE",
                (source_name,)
            )
            result = cur.fetchone()
            return result[0] if result else None
    except Exception as e:
        logger.error("Error getting source_id for %s: %s", source_name, e)
        return None

# Add this debug version temporarily
def write_headline_debug(conn, source_id: int, record: dict, ingestion_run_id: str):
    """Debug version with extra logging."""
    logger.info("DEBUG: write_headline called for source_id=%s", source_id)
    logger.info("DEBUG: record keys=%s", record.keys())
    try:
        with conn.cursor() as cur:
            headline = record.get("headline")
            article_url = record.get("article_url")
            published_at = record.get("published_at")
            author = record.get("author")
            content_snippet = record.get("content_snippet")
            
            logger.info("DEBUG: headline=%s", headline[:50] if headline else None)
            
            cur.execute(
                """SELECT raw.insert_headline_record(
                    %s, %s, %s, %s, %s, %s, %s
                )""",
                (source_id, headline, article_url, published_at, author, content_snippet, ingestion_run_id)
            )
            result = cur.fetchone()[0]
            logger.info("DEBUG: insert result=%s", result)
            return result
    except Exception as e:
        logger.error("DEBUG: Exception in write_headline: %s", e)
        return None
