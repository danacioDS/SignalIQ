"""Layer 3 entity resolution — ticker lookup via URL params and hardcoded aliases."""

import re

HARDCODED_ALIASES = {
    "NVDA": ["nvidia", "nvda", "nvidia corp"],
    "AAPL": ["apple", "aapl", "apple inc"],
    "MSFT": ["microsoft", "msft", "microsoft corp"],
}


def normalize_headline(text: str) -> str:
    return re.sub(r" +", " ", text.lower().strip())


class EntityResolver:

    def __init__(self, min_alias_length: int = 3):
        self._ticker_to_aliases: dict[str, list[str]] = {}
        self._alias_to_ticker: dict[str, str] = {}

        for ticker, aliases in HARDCODED_ALIASES.items():
            filtered = [a for a in aliases if len(a) >= min_alias_length]
            self._ticker_to_aliases[ticker] = filtered
            for alias in filtered:
                self._alias_to_ticker[alias] = ticker

    def resolve_by_url_param(self, url_param: str | None) -> str | None:
        if url_param is not None and url_param in self._ticker_to_aliases:
            return url_param
        return None

    def resolve_by_alias(self, normalized_headline: str) -> set[str]:
        matched: set[str] = set()
        for alias, ticker in self._alias_to_ticker.items():
            pattern = rf"(?<!\w){re.escape(alias.lower())}(?!\w)"
            if re.search(pattern, normalized_headline, re.IGNORECASE):
                matched.add(ticker)
        return matched

    def resolve(self, normalized_headline: str, url_param: str | None = None) -> list[str]:
        by_param = self.resolve_by_url_param(url_param)
        if by_param is not None:
            return [by_param]
        return sorted(self.resolve_by_alias(normalized_headline))

    def get_all_tickers(self) -> list[str]:
        return sorted(self._ticker_to_aliases)


if __name__ == "__main__":
    resolver = EntityResolver(min_alias_length=3)

    print("=== EntityResolver Demo ===\n")

    print("resolve_by_url_param('AAPL') →", resolver.resolve_by_url_param("AAPL"))
    print("resolve_by_url_param('UNKNOWN') →", resolver.resolve_by_url_param("UNKNOWN"))
    print()

    samples = [
        "apple stock rises on strong earnings",
        "microsoft and nvidia announce partnership",
        "google parent alphabet beats estimates",
    ]

    for text in samples:
        norm = normalize_headline(text)
        tickers = resolver.resolve_by_alias(norm)
        print(f"  headline: {text}")
        print(f"  norm:     {norm}")
        print(f"  tickers:  {tickers}\n")

    print("All known tickers:", resolver.get_all_tickers())
