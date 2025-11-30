#!/usr/bin/env python3
"""
Test the sophisticated Wikidata ISIN lookup with real data from iShares adapter.
"""

import sys

sys.path.insert(0, "/Users/davidhelmus/Repos/portfolio-master/POC")

from src.data.enrichment import enrich_securities
import logging

logging.basicConfig(level=logging.INFO, format="%(message)s")

# Simulate holdings from iShares (with raw_ticker preserved)
test_holdings = [
    {
        "raw_ticker": "AAPL",
        "ticker": "AAPL",
        "name": "APPLE INC",
        "weight_percentage": 5.05,
    },
    {
        "raw_ticker": "MSFT",
        "ticker": "MSFT",
        "name": "MICROSOFT CORP",
        "weight_percentage": 4.14,
    },
    {
        "raw_ticker": "ALV",
        "ticker": "ALV.DE",  # Yahoo format with suffix
        "name": "ALLIANZ SE",
        "weight_percentage": 1.2,
    },
]

print("=" * 60)
print("Testing Sophisticated Wikidata ISIN Lookup")
print("=" * 60)

enriched = enrich_securities(test_holdings)

print("\n" + "=" * 60)
print("Results:")
print("=" * 60)

for item in enriched:
    print(f"\nCompany: {item['name']}")
    print(f"  Raw Ticker: {item.get('raw_ticker', 'N/A')}")
    print(f"  Yahoo Ticker: {item['ticker']}")
    print(f"  ISIN: {item['isin']}")
    print(f"  Sector: {item.get('sector', 'Unknown')}")
    print(f"  Geography: {item.get('geography', 'Unknown')}")
