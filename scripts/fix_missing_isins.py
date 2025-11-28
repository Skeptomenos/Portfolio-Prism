#!/usr/bin/env python3
"""
Script to fix missing ISINs in the enrichment cache and asset universe.

This script:
1. Identifies securities with N/A ISIN but valid sector/geography in cache
2. Attempts to resolve ISINs using Finnhub and Wikidata
3. Updates the cache with resolved ISINs
4. Adds successfully resolved securities to asset_universe.csv
"""

import json
import os
import sys
import time
import requests
import pandas as pd
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data.enrichment import fetch_isin_from_wikidata
from src.config import ASSET_UNIVERSE_PATH

load_dotenv()

FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")
FINNHUB_API_URL = "https://finnhub.io/api/v1"
ENRICHMENT_CACHE_FILE = "data/working/cache/enrichment_cache.json"


def load_cache():
    """Load the enrichment cache."""
    if not os.path.exists(ENRICHMENT_CACHE_FILE):
        return {}
    with open(ENRICHMENT_CACHE_FILE, "r") as f:
        return json.load(f)


def save_cache(cache):
    """Save the enrichment cache."""
    with open(ENRICHMENT_CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)


def find_problematic_entries(cache):
    """Find entries with N/A ISIN but valid sector/geography."""
    problematic = []
    for key, data in cache.items():
        if (
            data.get("isin") == "N/A"
            and data.get("sector") != "Unknown"
            and data.get("geography") != "Unknown"
        ):
            problematic.append((key, data))
    return problematic


def fetch_isin_from_finnhub(ticker: str) -> str:
    """Fetch ISIN from Finnhub API."""
    if not FINNHUB_API_KEY:
        return None

    try:
        response = requests.get(
            f"{FINNHUB_API_URL}/stock/profile2",
            params={"symbol": ticker},
            headers={"X-Finnhub-Token": FINNHUB_API_KEY},
            timeout=10,
        )
        if response.status_code == 200:
            data = response.json()
            if data and data.get("isin"):
                return data["isin"]
    except Exception as e:
        print(f"  Finnhub error for {ticker}: {e}")
    return None


def resolve_isin(ticker: str, name: str) -> str:
    """Try to resolve ISIN using multiple sources."""
    # Try Finnhub first
    isin = fetch_isin_from_finnhub(ticker)
    if isin:
        print(f"  ✓ {ticker}: {isin} [Finnhub]")
        return isin

    # Rate limit for Finnhub
    time.sleep(1.1)

    # Try Wikidata
    isin = fetch_isin_from_wikidata(name, raw_ticker=ticker, yahoo_ticker=ticker)
    if isin:
        print(f"  ✓ {ticker}: {isin} [Wikidata]")
        return isin

    print(f"  ✗ {ticker}: No ISIN found")
    return None


def update_asset_universe(resolved_securities: list):
    """Add resolved securities to asset_universe.csv."""
    if not resolved_securities:
        print("\nNo securities to add to asset universe.")
        return

    # Load existing universe
    if os.path.exists(ASSET_UNIVERSE_PATH):
        df = pd.read_csv(ASSET_UNIVERSE_PATH)
    else:
        df = pd.DataFrame(
            columns=[
                "ISIN",
                "TR_Ticker",
                "Yahoo_Ticker",
                "Name",
                "Provider",
                "Asset_Class",
            ]
        )

    # Get existing ISINs and tickers
    existing_isins = set(df["ISIN"].dropna().tolist())
    existing_tickers = set(df["Yahoo_Ticker"].dropna().tolist())

    # Add new entries
    new_entries = []
    for sec in resolved_securities:
        if sec["isin"] not in existing_isins and sec["ticker"] not in existing_tickers:
            new_entries.append(
                {
                    "ISIN": sec["isin"],
                    "TR_Ticker": sec["ticker"],
                    "Yahoo_Ticker": sec["ticker"],
                    "Name": sec["name"],
                    "Provider": "",
                    "Asset_Class": "Stock",
                }
            )

    if new_entries:
        new_df = pd.DataFrame(new_entries)
        df = pd.concat([df, new_df], ignore_index=True)
        df.to_csv(ASSET_UNIVERSE_PATH, index=False)
        print(f"\n✓ Added {len(new_entries)} new securities to asset_universe.csv")
    else:
        print("\nNo new securities to add (all already exist).")


def main():
    print("=" * 60)
    print("ISIN Resolution Script")
    print("=" * 60)

    # Load cache
    cache = load_cache()
    print(f"\nLoaded cache with {len(cache)} entries")

    # Find problematic entries
    problematic = find_problematic_entries(cache)
    print(f"Found {len(problematic)} entries with N/A ISIN but valid sector/geography")

    if not problematic:
        print("No problematic entries found. Exiting.")
        return

    # Resolve ISINs
    print("\n" + "-" * 60)
    print("Resolving ISINs...")
    print("-" * 60)

    resolved = []
    failed = []

    for i, (ticker, data) in enumerate(problematic):
        print(
            f"\n[{i + 1}/{len(problematic)}] {ticker} ({data.get('name', 'Unknown')})"
        )

        isin = resolve_isin(ticker, data.get("name", ""))

        if isin:
            # Update cache
            cache[ticker]["isin"] = isin
            resolved.append(
                {
                    "ticker": ticker,
                    "isin": isin,
                    "name": data.get("name", "Unknown"),
                    "sector": data.get("sector"),
                    "geography": data.get("geography"),
                }
            )
        else:
            failed.append(ticker)

    # Save updated cache
    save_cache(cache)
    print("\n✓ Updated cache saved")

    # Update asset universe
    update_asset_universe(resolved)

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total processed: {len(problematic)}")
    print(f"Successfully resolved: {len(resolved)}")
    print(f"Failed to resolve: {len(failed)}")

    if failed:
        print(f"\nFailed tickers: {', '.join(failed[:20])}")
        if len(failed) > 20:
            print(f"  ... and {len(failed) - 20} more")


if __name__ == "__main__":
    main()
