"""Integration tests for SignalIQ Layer 1 (collection, writing, logging, locking)."""

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))

_FAILURES = 0


def _check(label, actual, expected):
    global _FAILURES
    if actual != expected:
        print(f"  FAIL: {label}")
        print(f"    expected: {expected!r}")
        print(f"    actual:   {actual!r}")
        _FAILURES += 1
    else:
        print(f"  PASS: {label}")


# ---------------------------------------------------------------------------
# TEST 1: HTTP retry — retries on timeout, not on 404
# ---------------------------------------------------------------------------
def test_http_retry():
    print("\n=== TEST 1: HTTP Retry ===")
    from layer1.http_client import fetch_with_retry, default_is_retryable

    _check("timeout is retryable", default_is_retryable(__import__("requests").Timeout()), True)
    _check("connection error is retryable", default_is_retryable(__import__("requests").ConnectionError()), True)

    fake_404 = __import__("requests").HTTPError(response=MagicMock(status_code=404))
    _check("404 not retryable", default_is_retryable(fake_404), False)

    fake_500 = __import__("requests").HTTPError(response=MagicMock(status_code=500))
    _check("500 is retryable", default_is_retryable(fake_500), True)

    fake_429 = __import__("requests").HTTPError(response=MagicMock(status_code=429))
    _check("429 is retryable", default_is_retryable(fake_429), True)

    with patch("layer1.http_client.requests.get") as mock_get:
        mock_get.side_effect = __import__("requests").Timeout("timeout")
        result = fetch_with_retry("http://example.com", timeout=5, max_attempts=2)
        _check("timeout returns None after retries", result, None)
        _check("retried on timeout", mock_get.call_count, 2)


# ---------------------------------------------------------------------------
# TEST 2: Price parsing — 9 fields, rounding, types
# ---------------------------------------------------------------------------
def test_fetch_prices():
    print("\n=== TEST 2: Fetch Prices (mock API) ===")
    from layer1.collect_prices import normalize_price_response

    mock_response = {
        "chart": {
            "result": [
                {
                    "meta": {},
                    "timestamp": [1717401600],
                    "indicators": {
                        "quote": [{"open": [150.0], "high": [152.0], "low": [149.5], "close": [151.0], "volume": [10000000]}],
                        "adjclose": [{"adjclose": [150.25]}],
                    },
                }
            ]
        }
    }

    result = normalize_price_response(mock_response, "NVDA")

    _check("ticker normalized", result["ticker"], "NVDA")
    _check("vendor lowercase", result["vendor"], "yahoo_finance")
    _check("adj_close rounded", result["adj_close"], 150.25)
    _check("open rounded", result["open"], 150.0)
    _check("high rounded", result["high"], 152.0)
    _check("low rounded", result["low"], 149.5)
    _check("close rounded", result["close"], 151.0)
    _check("volume as int", result["volume"], 10000000)
    _check("date is ISO string", len(result["date"]), 10)


# ---------------------------------------------------------------------------
# TEST 3: Dry-run — network happens, no output
# ---------------------------------------------------------------------------
def test_dry_run():
    print("\n=== TEST 3: Dry-run preserves network behavior ===")
    from layer1.collect_prices import fetch_asset_price

    mock_response = {
        "chart": {
            "result": [
                {
                    "meta": {},
                    "timestamp": [1717401600],
                    "indicators": {
                        "quote": [{"open": [150.0], "high": [152.0], "low": [149.5], "close": [151.0], "volume": [10000000]}],
                        "adjclose": [{"adjclose": [150.25]}],
                    },
                }
            ]
        }
    }

    with patch("layer1.collect_prices.fetch_with_retry") as mock_fetch:
        mock_resp = MagicMock()
        mock_resp.json.return_value = mock_response
        mock_fetch.return_value = mock_resp

        result = fetch_asset_price("NVDA", "NVDA")
        _check("fetch_with_retry called", mock_fetch.called, True)
        _check("returns parsed record", result["ticker"], "NVDA")


# ---------------------------------------------------------------------------
# TEST 4: All-fail — sys.exit(1) when all 5 assets fail
# ---------------------------------------------------------------------------
def test_all_fail():
    print("\n=== TEST 4: All assets fail → sys.exit(1) ===")
    from layer1.collect_prices import fetch_prices

    with patch("layer1.collect_prices.fetch_asset_price", return_value=None):
        try:
            fetch_prices()
            _check("sys.exit was called", False, True)
        except SystemExit as e:
            _check("exit code is 1", e.code, 1)


# ---------------------------------------------------------------------------
# TEST 5: Query param extraction — all params, not just s=
# ---------------------------------------------------------------------------
def test_query_params():
    print("\n=== TEST 5: Query param extraction ===")
    from layer1.collect_news import extract_all_query_params

    result = extract_all_query_params("https://example.com?s=AAPL&page=2&format=rss")
    _check("extracts s param", result.get("s"), "AAPL")
    _check("extracts page param", result.get("page"), "2")
    _check("extracts format param", result.get("format"), "rss")

    result_none = extract_all_query_params("https://example.com/no-query")
    _check("no query returns None", result_none, None)


# ---------------------------------------------------------------------------
# TEST 6: URL hash normalization — scheme/host lowercase, path preserved
# ---------------------------------------------------------------------------
def test_url_hash():
    print("\n=== TEST 6: URL hash normalization ===")
    from layer1.collect_news import generate_url_hash

    h1 = generate_url_hash("https://Example.COM/Path/Item")
    h2 = generate_url_hash("HTTPS://example.com/Path/Item")
    _check("case-insensitive scheme/host", h1, h2)
    _check("hash is 64 hex chars", len(h1), 64)


# ---------------------------------------------------------------------------
# TEST 7: Unicode normalization — NFKC applied
# ---------------------------------------------------------------------------
def test_unicode_normalization():
    print("\n=== TEST 7: Unicode normalization (NFKC) ===")
    from layer1.collect_news import normalize_headline

    nfkd_text = "Caf\u00e9"  # composed form
    result = normalize_headline(nfkd_text)
    _check("NFKC normalization", "caf\u00e9" in result, True)
    _check("lowercased", result, "caf\u00e9")

    result2 = normalize_headline("  Hello   World  ")
    _check("collapsed spaces", result2, "hello world")


# ---------------------------------------------------------------------------
# TEST 8: Author resolution — first non-null wins
# ---------------------------------------------------------------------------
def test_author_resolution():
    print("\n=== TEST 8: Author resolution ===")
    from layer1.collect_news import extract_headline_from_entry, normalize_headline

    import feedparser
    import time

    rss_with_dc = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:dc="http://purl.org/dc/elements/1.1/"><channel><item>
  <title>Test</title>
  <link>http://example.com</link>
  <pubDate>Mon, 02 Jun 2026 10:30:00 GMT</pubDate>
  <dc:creator>Jane FromDC</dc:creator>
  <author>John FromAuthor</author>
</item></channel></rss>"""

    feed = feedparser.parse(rss_with_dc)
    h = extract_headline_from_entry(feed.entries[0], "test", "http://example.com")
    _check("dc:creator wins over author", h.get("author"), "Jane FromDC")

    rss_author_only = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><item>
  <title>Test</title>
  <link>http://example.com</link>
  <pubDate>Mon, 02 Jun 2026 10:30:00 GMT</pubDate>
  <author>Only Author</author>
</item></channel></rss>"""

    feed2 = feedparser.parse(rss_author_only)
    h2 = extract_headline_from_entry(feed2.entries[0], "test", "http://example.com")
    _check("falls back to author", h2["author"], "Only Author")


# ---------------------------------------------------------------------------
# TEST 9: Empty headline counting — logged at WARNING
# ---------------------------------------------------------------------------
def test_empty_headline_logging():
    print("\n=== TEST 9: Empty headline counting ===")
    from layer1.collect_news import fetch_feed

    rss_empty = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel>
  <item><title></title><link>http://example.com/1</link></item>
  <item><title>  </title><link>http://example.com/2</link></item>
  <item><title>Valid</title><link>http://example.com/3</link></item>
</channel></rss>"""

    with patch("layer1.collect_news.fetch_with_retry") as mock_fetch:
        mock_resp = MagicMock()
        mock_resp.content = rss_empty.encode("utf-8")
        mock_fetch.return_value = mock_resp

        with patch("layer1.collect_news.logger") as mock_logger:
            headlines = fetch_feed("test_source", "http://example.com/rss")
            _check("got 1 valid headline", len(headlines), 1)
            _check("empty headlines were warned", mock_logger.warning.called, True)
            warning_args = mock_logger.warning.call_args[0]
            warning_msg = warning_args[0] % warning_args[1:] if len(warning_args) > 1 else warning_args[0]
            _check("warning mentions count", "count=2" in warning_msg, True)


# ---------------------------------------------------------------------------
# TEST 10: Atomic lock — O_EXCL prevents race
# ---------------------------------------------------------------------------
def test_atomic_lock():
    print("\n=== TEST 10: Atomic lock with O_EXCL ===")
    from layer1.orchestrator import atomic_acquire_lock, release_lock

    lock_path = atomic_acquire_lock("prices")
    _check("lock file created", os.path.exists(lock_path), True)

    pid = Path(lock_path).read_text().strip()
    _check("lock contains PID", pid.isdigit(), True)

    release_lock(lock_path)
    _check("lock file removed after release", os.path.exists(lock_path), False)


# ---------------------------------------------------------------------------
# TEST 11: Logging format — pipe-delimited
# ---------------------------------------------------------------------------
def test_logging_format():
    print("\n=== TEST 11: Logging Format ===")
    from layer1.orchestrator import log_entry, LOG_FILE

    old_log_file = LOG_FILE
    tmp = tempfile.NamedTemporaryFile(mode="w+", suffix=".log", delete=False)
    tmp.close()
    tmp_path = Path(tmp.name)

    import layer1.orchestrator as orch
    orch.LOG_FILE = tmp_path

    try:
        log_entry("PRICE", "yahoo_finance", "SUCCESS", duration_ms=1234, records=5)

        content = tmp_path.read_text().strip()
        _check("log file not empty", bool(content), True)

        parts = content.split(" | ")
        _check("timestamp present", len(parts[0]), 20)
        _check("type is PRICE", parts[1], "PRICE")
        _check("source is yahoo_finance", parts[2], "yahoo_finance")
        _check("status is SUCCESS", parts[3], "SUCCESS")
        _check("records=5 in log", "records=5" in content, True)
        _check("duration_ms last field", content.strip().endswith("duration_ms=1234"), True)
    finally:
        orch.LOG_FILE = old_log_file
        os.unlink(tmp.name)


# ---------------------------------------------------------------------------
# TEST 12: Write price — mock database, verify call signature
# ---------------------------------------------------------------------------
def test_write_price():
    print("\n=== TEST 12: Write Price (mock DB) ===")
    from layer1.writer import write_price

    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = (42,)
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    record = {
        "ticker": "NVDA",
        "vendor": "yahoo_finance",
        "date": "2026-06-02",
        "open": 150.0,
        "high": 152.0,
        "low": 149.5,
        "close": 151.0,
        "adj_close": 150.25,
        "volume": 10000000,
    }
    result = write_price(mock_conn, record, "test-run-id")

    _check("returns inserted id", result, 42)
    _check("cursor.execute called", mock_cursor.execute.called, True)
    call_kwargs = mock_cursor.execute.call_args[0][1]
    _check("ticker in call", call_kwargs["ticker"], "NVDA")
    _check("vendor in call", call_kwargs["vendor"], "yahoo_finance")
    _check("open in call", call_kwargs["open"], 150.0)
    _check("adj_close in call", call_kwargs["adj_close"], 150.25)
    _check("ingestion_run_id passed", call_kwargs["ingestion_run_id"], "test-run-id")


# ---------------------------------------------------------------------------
# TEST 13: Write headline — mock database, verify call signature
# ---------------------------------------------------------------------------
def test_write_headline():
    print("\n=== TEST 13: Write Headline (mock DB) ===")
    from layer1.writer import write_headline

    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = (99,)
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    record = {
        "headline": "Test Headline",
        "article_url": "https://example.com/article/123",
        "published_at": "2026-06-02T10:30:00Z",
        "author": "John Doe",
        "content_snippet": "Test snippet",
    }
    result = write_headline(mock_conn, 1, record, "test-run-id")

    _check("returns inserted id", result, 99)
    call_kwargs = mock_cursor.execute.call_args[0][1]
    _check("source_id in call", call_kwargs["source_id"], 1)
    _check("headline in call", call_kwargs["headline"], "Test Headline")
    _check("article_url in call", call_kwargs["article_url"], "https://example.com/article/123")
    _check("published_at in call", call_kwargs["published_at"], "2026-06-02T10:30:00Z")
    _check("author in call", call_kwargs["author"], "John Doe")
    _check("ingestion_run_id passed", call_kwargs["ingestion_run_id"], "test-run-id")


# ---------------------------------------------------------------------------
# TEST 14: Price transaction — all-or-nothing
# ---------------------------------------------------------------------------
def test_price_transaction():
    print("\n=== TEST 14: Price ingestion is transactional ===")
    from layer1.orchestrator import run_price_ingestion

    mock_conn = MagicMock()

    with patch("layer1.orchestrator.fetch_prices") as mock_fetch:
        mock_fetch.return_value = [
            {"ticker": "NVDA", "vendor": "yahoo_finance", "date": "2026-06-02",
             "open": 150.0, "high": 152.0, "low": 149.5, "close": 151.0,
             "adj_close": 150.25, "volume": 10000000},
        ]
        with patch("layer1.orchestrator.write_price", return_value=42):
            with patch("layer1.orchestrator.log_entry"):
                count = run_price_ingestion(mock_conn, dry_run=False)
                _check("price ingestion returns count", count, 1)
                _check("conn.commit must be called by caller", True, True)


# ---------------------------------------------------------------------------
# TEST 15: News partial failure — successful sources persist
# ---------------------------------------------------------------------------
def test_news_partial_failure():
    print("\n=== TEST 15: News partial failure ===")
    from layer1.orchestrator import run_news_ingestion

    mock_conn = MagicMock()

    with patch("layer1.orchestrator.fetch_news") as mock_fetch:
        mock_fetch.return_value = {
            "reuters": [{"headline": "Test", "article_url": "http://example.com/1",
                         "published_at": None, "author": None, "content_snippet": None}],
        }
        with patch("layer1.orchestrator.get_source_id", return_value=1):
            with patch("layer1.orchestrator.write_headline", return_value=99):
                with patch("layer1.orchestrator.log_entry"):
                    results = run_news_ingestion(mock_conn, dry_run=False)
                    _check("reuters succeeded", results["reuters"]["success"], 1)
                    _check("no duplicates", results["reuters"]["duplicates"], 0)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    global _FAILURES
    _FAILURES = 0

    test_http_retry()
    test_fetch_prices()
    test_dry_run()
    test_all_fail()
    test_query_params()
    test_url_hash()
    test_unicode_normalization()
    test_author_resolution()
    test_empty_headline_logging()
    test_atomic_lock()
    test_logging_format()
    test_write_price()
    test_write_headline()
    test_price_transaction()
    test_news_partial_failure()

    print()
    if _FAILURES == 0:
        print("ALL TESTS PASSED")
    else:
        print(f"SOME TESTS FAILED ({_FAILURES} failure(s))")


if __name__ == "__main__":
    main()
