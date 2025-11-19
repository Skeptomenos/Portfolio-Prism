import json
import os
import requests
import time
from dotenv import load_dotenv

# Add project root to path to allow absolute imports
import sys
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.data.caching import load_from_cache, save_to_cache, get_cache_key

# Load environment variables from .env file
load_dotenv()

# --- Constants ---
FINNHUB_API_KEY = os.getenv('FINNHUB_API_KEY')
FINNHUB_API_URL = 'https://finnhub.io/api/v1'

# --- Helper Functions ---

def enrich_securities_bulk(securities_to_fetch, force_refresh=False):
    """
    Enriches a list of securities with metadata from Finnhub, using a robust caching layer.
    
    Args:
        securities_to_fetch (list): A list of security dictionaries to enrich.
        force_refresh (bool): If True, bypasses the cache and fetches fresh data.

    Returns:
        list: A list of enriched security dictionaries.
    """
    enriched_results = []
    session = requests.Session()
    session.headers.update({'X-Finnhub-Token': FINNHUB_API_KEY})

    # Counter for progress feedback
    count = 0
    total = len(securities_to_fetch)
    print(f"  - Progress: ", end="", flush=True)

    for security in securities_to_fetch:
        identifier = security.get('ticker') or security.get('isin')
        if not identifier:
            continue

        cache_key = get_cache_key(identifier)
        
        # 1. Check cache first
        if not force_refresh:
            cached_data = load_from_cache(cache_key)
            if cached_data:
                enriched_results.append(cached_data)
                # Visual feedback for cache hit
                print(".", end="", flush=True)
                count += 1
                continue

        # 2. If not in cache or force_refresh is True, call the API
        try:
            response = session.get(f"{FINNHUB_API_URL}/stock/profile2", params={'symbol': identifier})
            response.raise_for_status()
            profile_data = response.json()

            if profile_data:
                result = {
                    'ticker': profile_data.get('ticker', identifier),
                    'isin': profile_data.get('isin', 'N/A'),
                    'name': profile_data.get('name', 'N/A'),
                    'sector': profile_data.get('finnhubIndustry', 'Unknown'),
                    'geography': profile_data.get('country', 'Unknown')
                }
            else:
                result = {
                    'ticker': identifier, 'isin': 'N/A', 'name': 'Not Found',
                    'sector': 'Unknown', 'geography': 'Unknown'
                }
            
            # 3. Save to cache and append to results
            save_to_cache(cache_key, result)
            enriched_results.append(result)

            # Rate Limiting: Finnhub Free Tier is 60 calls/min (~1 call/sec)
            # We sleep for 1.1s to be safe.
            time.sleep(1.1)
            # Visual feedback for API hit
            print("*", end="", flush=True)

        except requests.exceptions.RequestException as e:
            # ... (Error handling) ...
            enriched_results.append({
                'ticker': identifier, 'isin': 'N/A', 'name': 'API Error',
                'sector': 'Unknown', 'geography': 'Unknown'
            })
            # Sleep even on error
            time.sleep(1.1)
            print("x", end="", flush=True)

        count += 1
            
    print(" Done.")
    return enriched_results

# --- Main Function ---

def enrich_securities(securities, force_refresh=False):
    """
    Enriches a list of securities with metadata by calling the bulk enrichment function.
    The caching logic is now handled within the bulk function itself.
    
    Args:
        securities (list): A list of security dictionaries to enrich.
        force_refresh (bool): If True, bypasses the cache.

    Returns:
        list: A list of enriched security dictionaries.
    """
    print(f"  - Enriching metadata for {len(securities)} securities...")
    enriched_data = enrich_securities_bulk(securities, force_refresh=force_refresh)
    print(f"  - Enrichment complete.")
    return enriched_data