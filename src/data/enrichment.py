import json
import os
import requests
import time
import yfinance as yf
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

def fetch_from_yfinance(identifier):
    """
    Attempts to fetch metadata from YFinance using the identifier (ISIN or Ticker).
    Returns a dictionary with 'sector', 'geography', and 'name' or None if failed.
    """
    try:
        ticker = yf.Ticker(identifier)
        info = ticker.info
        # Check if we actually got valid data (YFinance sometimes returns empty info dicts)
        if info and ('sector' in info or 'country' in info):
            return {
                'name': info.get('longName') or info.get('shortName') or 'N/A',
                'sector': info.get('sector', 'Unknown'),
                'geography': info.get('country', 'Unknown')
            }
    except Exception:
        pass
    return None

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
                # Simple validation: if cached data is "Unknown", treat as cache miss to try fallback
                if cached_data.get('sector') != 'Unknown' and cached_data.get('geography') != 'Unknown':
                    enriched_results.append(cached_data)
                    # Visual feedback for cache hit
                    print(".", end="", flush=True)
                    count += 1
                    continue

        # 2. If not in cache or force_refresh is True, call the API
        result = {
            'ticker': identifier, 'isin': 'N/A', 'name': 'Not Found',
            'sector': 'Unknown', 'geography': 'Unknown'
        }
        
        # Primary: Finnhub
        try:
            response = session.get(f"{FINNHUB_API_URL}/stock/profile2", params={'symbol': identifier})
            # response.raise_for_status() # Don't raise, just fall through to fallback
            if response.status_code == 200:
                profile_data = response.json()
                if profile_data:
                    result = {
                        'ticker': profile_data.get('ticker', identifier),
                        'isin': profile_data.get('isin', 'N/A'),
                        'name': profile_data.get('name', 'N/A'),
                        'sector': profile_data.get('finnhubIndustry', 'Unknown'),
                        'geography': profile_data.get('country', 'Unknown')
                    }
                    # Visual feedback for API hit
                    print("F", end="", flush=True) # F for Finnhub
                else:
                    # Finnhub returned empty, try fallback
                    pass
            
            # Rate Limiting: Finnhub Free Tier is 60 calls/min (~1 call/sec)
            time.sleep(1.1)

        except requests.exceptions.RequestException:
            print("x", end="", flush=True)

        # Fallback: YFinance (if Finnhub failed or returned Unknown)
        if result['sector'] == 'Unknown' or result['geography'] == 'Unknown':
            yf_data = fetch_from_yfinance(identifier)
            if yf_data:
                result.update(yf_data)
                print("Y", end="", flush=True) # Y for YFinance

        # 3. Save to cache and append to results
        save_to_cache(cache_key, result)
        enriched_results.append(result)
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