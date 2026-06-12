import argparse
import logging
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from layer1.collect_news import fetch_news
from layer1.collect_prices import fetch_prices
from layer1.writer import get_connection, get_source_id, write_headline, write_price

logger = logging.getLogger(__name__)

LOCK_DIR = Path("/tmp")
LINK_PREFIX = "signaliq_layer1"


def atomic_acquire_lock(lock_type: str) -> Path:
    lock_path = LOCK_DIR / f"{LINK_PREFIX}_{lock_type}.lock"
    try:
        fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(fd, str(os.getpid()).encode())
        os.close(fd)
        return lock_path
    except FileExistsError:
        logger.error("Another %s run already in progress (lock: %s)", lock_type, lock_path)
        raise FileExistsError(f"Another {lock_type} run already in progress")


def release_lock(lock_path: Path):
    try:
        lock_path.unlink()
    except FileNotFoundError:
        pass


def ensure_log_dir():
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    return log_dir / "ingestion.log"


LOG_FILE = None


def log_entry(
    entry_type: str,
    source: str,
    status: str,
    duration_ms: int,
    **details,
):
    global LOG_FILE
    if LOG_FILE is None:
        LOG_FILE = ensure_log_dir()

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    parts = [timestamp, entry_type, source, status]

    detail_strs = []
    for key, value in details.items():
        if isinstance(value, str) and " " in value:
            detail_strs.append(f'{key}="{value}"')
        else:
            detail_strs.append(f"{key}={value}")
    detail_strs.append(f"duration_ms={duration_ms}")

    parts.extend(detail_strs)
    line = " | ".join(parts)

    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

    logger.info(line)


def run_price_ingestion(conn, dry_run: bool = False) -> int:
    run_id = str(uuid.uuid4())
    start = time.perf_counter()

    log_entry("PRICE", "yahoo_finance", "START", 0, run_id=run_id)

    prices = fetch_prices()

    if dry_run:
        elapsed = int((time.perf_counter() - start) * 1000)
        log_entry("PRICE", "yahoo_finance", "SUCCESS", elapsed, records=len(prices), run_id=run_id)
        return len(prices)

    success_count = 0
    for record in prices:
        result = write_price(conn, record, run_id)
        if result is not None:
            success_count += 1

    elapsed = int((time.perf_counter() - start) * 1000)
    log_entry("PRICE", "yahoo_finance", "SUCCESS", elapsed, records=success_count, run_id=run_id)
    return success_count


def run_news_ingestion(
    conn,
    source_filter: Optional[str] = None,
    dry_run: bool = False,
) -> dict:
    run_id = str(uuid.uuid4())
    start = time.perf_counter()

    log_entry("NEWS", source_filter or "all", "START", 0, run_id=run_id)

    news = fetch_news(source_filter)
    results = {}

    for source_name, headlines in news.items():
        source_start = time.perf_counter()
        source_id = get_source_id(conn, source_name) if not dry_run else None

        if source_id is None and not dry_run:
            log_entry(
                "NEWS", source_name, "FAILED", int((time.perf_counter() - source_start) * 1000),
                error="unknown source",
            )
            results[source_name] = {"success": 0, "duplicates": 0, "skipped_empty": 0}
            continue

        success = 0
        duplicates = 0
        skipped_empty = 0

        if not dry_run:
            for headline in headlines:
                if not headline.get("headline"):
                    skipped_empty += 1
                    continue
                result = write_headline(conn, source_id, headline, run_id)
                if result is not None:
                    success += 1
                else:
                    duplicates += 1
        else:
            success = len(headlines)

        elapsed = int((time.perf_counter() - source_start) * 1000)
        log_entry(
            "NEWS", source_name, "SUCCESS", elapsed,
            records=success, duplicates=duplicates,
        )
        results[source_name] = {
            "success": success,
            "duplicates": duplicates,
            "skipped_empty": skipped_empty,
        }

    elapsed = int((time.perf_counter() - start) * 1000)
    log_entry("NEWS", source_filter or "all", "SUCCESS", elapsed, run_id=run_id)

    return results


def main():
    parser = argparse.ArgumentParser(description="SignalIQ Layer 1 Orchestrator")
    parser.add_argument("--type", choices=["prices", "news", "both"], default="both")
    parser.add_argument("--source", type=str, default=None)
    parser.add_argument("--dry-run", action="store_true", default=False)
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )

    if args.type in ("prices", "both"):
        lock_path = atomic_acquire_lock("prices")
        try:
            conn = get_connection()
            try:
                count = run_price_ingestion(conn, dry_run=args.dry_run)
                if not args.dry_run:
                    conn.commit()
                log_entry("PRICE", "yahoo_finance", "SUCCESS", 0, records=count)
            except Exception:
                if not args.dry_run:
                    conn.rollback()
                raise
            finally:
                conn.close()
        finally:
            release_lock(lock_path)

    if args.type in ("news", "both"):
        lock_path = atomic_acquire_lock("news")
        try:
            conn = get_connection()
            try:
                results = run_news_ingestion(conn, source_filter=args.source, dry_run=args.dry_run)
                if not args.dry_run:
                    conn.commit()          # <-- CORRECCIÓN AQUÍ
                for source_name, stats in results.items():
                    log_entry(
                        "NEWS", source_name, "SUCCESS", 0,
                        records=stats["success"], duplicates=stats["duplicates"],
                    )
            except Exception:
                logger.error("News ingestion failed")
                raise
            finally:
                conn.close()
        finally:
            release_lock(lock_path)


if __name__ == "__main__":
    main()
