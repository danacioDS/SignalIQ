import hashlib
import logging
import re
import sys
import time
import unicodedata
import urllib.parse
from typing import Optional

import feedparser
import requests

from layer1.http_client import fetch_with_retry

logger = logging.getLogger(__name__)

SOURCES = {
    "reuters": "http://feeds.reuters.com/reuters/businessNews",
    "ap": "https://apnews.com/business.rss",
    "yahoo_general": "https://finance.yahoo.com/news/rssindex",
    "yahoo_ticker": "https://finance.yahoo.com/rss/headline?s={TICKER}",
    "cnbc": "https://www.cnbc.com/id/100003114/device/rss/rss.html",
    "marketwatch": "http://feeds.marketwatch.com/marketwatch/topstories/",
}

RSS_TIMEOUT = 15
RSS_RETRY_DELAY = 5
RSS_MAX_ATTEMPTS = 2


def extract_all_query_params(url: str) -> Optional[dict]:
    parsed = urllib.parse.urlparse(url)
    params = urllib.parse.parse_qsl(parsed.query)
    return dict(params) if params else None


def normalize_url_for_hash(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    normalized = urllib.parse.urlunparse((
        parsed.scheme.lower(),
        parsed.hostname.lower() if parsed.hostname else parsed.netloc.lower(),
        parsed.path,
        parsed.params,
        parsed.query,
        parsed.fragment,
    ))
    return normalized


def normalize_headline(text: str) -> str:
    text = text.strip()
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r'\s+', ' ', text)
    return text.lower()


def generate_headline_hash(headline: str) -> str:
    normalized = normalize_headline(headline)
    return hashlib.sha256(normalized.encode()).hexdigest()


def generate_url_hash(url: str) -> str:
    normalized = normalize_url_for_hash(url)
    return hashlib.sha256(normalized.encode()).hexdigest()


def extract_headline_from_entry(entry, source_name: str, url: str) -> Optional[dict]:
    raw_title = entry.get("title", "")
    headline = re.sub(r'\s+', ' ', raw_title.strip())
    if not headline:
        return None

    article_url = entry.get("link", "").strip()

    author = None
    authors = entry.get("authors")
    if authors and isinstance(authors, list) and len(authors) > 0:
        first = authors[0].get("name") if isinstance(authors[0], dict) else None
        if first:
            author = first.strip()
    if not author:
        entry_author = entry.get("author")
        if entry_author:
            author = entry_author.strip() if isinstance(entry_author, str) else entry_author[0].strip() if entry_author else None

    published_at = None
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        published_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", entry.published_parsed)

    content_snippet = None
    description = entry.get("description", "")
    if description:
        stripped = re.sub(r'<[^>]+>', '', description).strip()
        content_snippet = stripped[:500] if stripped else None

    url_param_value = None
    params = extract_all_query_params(article_url or url)
    if params and "s" in params:
        url_param_value = params["s"]

    return {
        "source": source_name,
        "headline": headline,
        "article_url": article_url or None,
        "published_at": published_at,
        "author": author,
        "content_snippet": content_snippet,
        "url_param_value": url_param_value,
        "headline_hash": generate_headline_hash(headline),
        "url_hash": generate_url_hash(article_url or url),
    }


def fetch_feed(source_name: str, url: str) -> Optional[list[dict]]:
    resp = fetch_with_retry(
        url,
        timeout=RSS_TIMEOUT,
        retry_delay=RSS_RETRY_DELAY,
        max_attempts=RSS_MAX_ATTEMPTS,
    )
    if resp is None:
        logger.error("FEED_FAILED | source=%s | error=all retries exhausted", source_name)
        return None

    feed = feedparser.parse(resp.content)

    if feed.bozo and not feed.entries:
        logger.warning("BOZO_DETECTED | source=%s | retry=1", source_name)
        resp2 = fetch_with_retry(
            url,
            timeout=RSS_TIMEOUT,
            retry_delay=RSS_RETRY_DELAY,
            max_attempts=RSS_MAX_ATTEMPTS,
        )
        if resp2 is not None:
            feed = feedparser.parse(resp2.content)

    if not feed.entries:
        logger.warning("FEED_EMPTY | source=%s", source_name)
        return []

    headlines = []
    empty_count = 0
    for entry in feed.entries:
        result = extract_headline_from_entry(entry, source_name, url)
        if result is None:
            empty_count += 1
        else:
            headlines.append(result)

    if empty_count > 0:
        logger.warning(
            "SKIPPED_EMPTY_HEADLINE | source=%s | count=%d", source_name, empty_count
        )

    return headlines


def fetch_news(source_filter: Optional[str] = None) -> dict[str, list[dict]]:
    sources_to_fetch = (
        {source_filter: SOURCES[source_filter]}
        if source_filter and source_filter in SOURCES
        else SOURCES
    )

    result = {}
    for source_name, url in sources_to_fetch.items():
        try:
            headlines = fetch_feed(source_name, url)
            if headlines is not None:
                result[source_name] = headlines
            else:
                logger.warning("Skipping %s after failed fetch", source_name)
        except Exception as e:
            logger.error("FEED_FAILED | source=%s | error=%s", source_name, str(e))

    if not result:
        logger.critical("All %d feeds failed to fetch", len(sources_to_fetch))
        raise Exception(f"All {len(sources_to_fetch)} feeds failed")

    return result


def main():
    dry_run = "--dry-run" in sys.argv
    source_filter = None

    for i, arg in enumerate(sys.argv[1:]):
        if arg == "--source" and i + 1 < len(sys.argv[1:]):
            source_filter = sys.argv[i + 2]

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )

    news = fetch_news(source_filter)

    if not dry_run:
        import json
        all_headlines = []
        for source_name, headlines in news.items():
            all_headlines.extend(headlines)
        print(json.dumps(all_headlines, indent=2))
    else:
        total = sum(len(h) for h in news.values())
        logger.info("Dry-run: fetched %d headlines from %d sources", total, len(news))


if __name__ == "__main__":
    main()
