import json
import logging
import sys
import time
from datetime import date, datetime, timezone

import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)

ASSETS = {
    "NVDA": "NVDA",
    "AAPL": "AAPL",
    "MSFT": "MSFT",
    "SPX": "^GSPC",
    "BTC-USD": "BTC-USD",
}

REQUEST_DELAY_SECONDS = 1


def fetch_asset_price(symbol: str, ticker: str) -> dict:
    """Fetch price using yfinance."""
    try:
        ticker_obj = yf.Ticker(symbol)
        data = ticker_obj.history(period="2d", interval="1d")
        
        if data.empty:
            logger.warning("No data returned for %s", ticker)
            return None
        
        latest = data.iloc[-1]
        # Convert timestamp to date object (not string)
        date_obj = latest.name.date()
        
        adj_close = latest.get("Close")
        if pd.isna(adj_close):
            logger.warning("Missing close price for %s", ticker)
            return None
        
        volume = int(latest["Volume"]) if not pd.isna(latest["Volume"]) else None
        
        return {
            "ticker": ticker,
            "vendor": "yahoo_finance",
            "date": date_obj,  # Date object, not string
            "open": float(round(latest["Open"], 4)),
            "high": float(round(latest["High"], 4)),
            "low": float(round(latest["Low"], 4)),
            "close": float(round(latest["Close"], 4)),
            "adj_close": float(round(adj_close, 4)),
            "volume": volume,
        }
    except Exception as e:
        logger.warning("Error fetching %s: %s", ticker, e)
        return None


def fetch_prices() -> list[dict]:
    results = []
    for ticker, symbol in ASSETS.items():
        record = fetch_asset_price(symbol, ticker)
        if record is not None:
            results.append(record)
        time.sleep(REQUEST_DELAY_SECONDS)
    
    if not results:
        logger.critical("All %d assets failed to fetch", len(ASSETS))
        sys.exit(1)
    
    return results


def main():
    dry_run = "--dry-run" in sys.argv

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )

    prices = fetch_prices()

    if not dry_run:
        # Print as JSON with date strings for readability
        output = []
        for p in prices:
            p_copy = p.copy()
            p_copy["date"] = p_copy["date"].isoformat()
            output.append(p_copy)
        print(json.dumps(output, indent=2))
    else:
        logger.info("Dry-run: fetched %d price records", len(prices))


if __name__ == "__main__":
    main()
