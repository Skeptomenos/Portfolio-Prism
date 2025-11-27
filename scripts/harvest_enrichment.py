#!/usr/bin/env python3
"""
Harvests validated enrichment data from the cache and adds it to the asset_universe.csv.
This allows the system to "learn" new securities permanently, reducing future API calls.
"""

import json
import csv
import os
import sys
from typing import Set

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.config import ASSET_UNIVERSE_PATH

CACHE_PATH = 'data/working/cache/enrichment_cache.json'

def load_universe_isins() -> Set[str]:
    """Loads existing ISINs from asset_universe.csv to prevent duplicates."""
    existing_isins = set()
    if os.path.exists(ASSET_UNIVERSE_PATH):
        with open(ASSET_UNIVERSE_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['ISIN']:
                    existing_isins.add(row['ISIN'])
    return existing_isins

def harvest_cache():
    if not os.path.exists(CACHE_PATH):
        print(f"❌ Cache file not found: {CACHE_PATH}")
        return

    print(f"📖 Loading cache from {CACHE_PATH}...")
    with open(CACHE_PATH, 'r', encoding='utf-8') as f:
        cache_data = json.load(f)

    existing_isins = load_universe_isins()
    print(f"ℹ️  Found {len(existing_isins)} existing ISINs in asset_universe.csv")

    new_entries = []
    
    for key, data in cache_data.items():
        isin = data.get('isin')
        
        # Validation checks
        if not isin or isin in ['N/A', 'UNKNOWN'] or isin.startswith('UNKNOWN_'):
            continue
            
        if isin in existing_isins:
            continue
            
        # Prepare new entry
        # Mapping:
        # ISIN -> isin
        # TR_Ticker -> raw_ticker (preferred) or ticker
        # Yahoo_Ticker -> ticker
        # Name -> name
        # Provider -> "" (Unknown source for general enrichment)
        # Asset_Class -> "Stock" (Safe assumption for underlying holdings, usually)
        
        tr_ticker = data.get('raw_ticker') or data.get('ticker')
        yahoo_ticker = data.get('ticker')
        name = data.get('name', 'Unknown')
        
        new_entry = {
            'ISIN': isin,
            'TR_Ticker': tr_ticker,
            'Yahoo_Ticker': yahoo_ticker,
            'Name': name,
            'Provider': '',
            'Asset_Class': 'Stock' # Defaulting to Stock as most enriched items are underlying equities
        }
        
        new_entries.append(new_entry)
        existing_isins.add(isin) # Prevent duplicates within the batch

    if not new_entries:
        print("✅ No new valid securities found to harvest.")
        return

    print(f"🌾 Harvesting {len(new_entries)} new securities...")

    # Append to CSV
    file_exists = os.path.exists(ASSET_UNIVERSE_PATH)
    fieldnames = ['ISIN', 'TR_Ticker', 'Yahoo_Ticker', 'Name', 'Provider', 'Asset_Class']
    
    with open(ASSET_UNIVERSE_PATH, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerows(new_entries)

    print(f"✅ Successfully added {len(new_entries)} entries to {ASSET_UNIVERSE_PATH}")

if __name__ == "__main__":
    harvest_cache()
