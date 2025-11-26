import json
import os
import requests
import time
import yfinance as yf
from dotenv import load_dotenv



from src.data.caching import load_from_cache, save_to_cache, get_cache_key
from src.config import ASSET_UNIVERSE_PATH
import pandas as pd

# Load environment variables from .env file
load_dotenv()

from typing import List, Dict, Optional, Any

# --- Constants ---
FINNHUB_API_KEY = os.getenv('FINNHUB_API_KEY')
FINNHUB_API_URL = 'https://finnhub.io/api/v1'

# --- Helper Functions ---

def fetch_from_yfinance(identifier: str) -> Optional[Dict[str, str]]:
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

def load_asset_universe() -> Dict[str, str]:
    """
    Loads the asset universe and returns a mapping of Ticker -> ISIN.
    """
    if not os.path.exists(ASSET_UNIVERSE_PATH):
        return {}
    try:
        df = pd.read_csv(ASSET_UNIVERSE_PATH)
        # Create mapping from Yahoo Ticker to ISIN
        # Ensure we drop NaNs
        mapping = df.dropna(subset=['Yahoo_Ticker', 'ISIN']).set_index('Yahoo_Ticker')['ISIN'].to_dict()
        return mapping
    except Exception as e:
        print(f"Warning: Failed to load asset universe: {e}")
        return {}

_UNIVERSE_MAPPING = None

def enrich_securities_bulk(
    securities_to_fetch: List[Dict[str, Any]], 
    force_refresh: bool = False
) -> List[Dict[str, Any]]:
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

    # Load Universe Mapping (Lazy Load)
    global _UNIVERSE_MAPPING
    if _UNIVERSE_MAPPING is None:
        _UNIVERSE_MAPPING = load_asset_universe()

    # Counter for progress feedback
    count = 0
    total = len(securities_to_fetch)
    print(f"  - Progress: ", end="", flush=True)

    for security in securities_to_fetch:
        identifier = security.get('ticker') or security.get('isin')
        if not identifier:
            continue
            
        # Filter out internal placeholders to prevent API noise
        if identifier.startswith('_') or 'NON_EQUITY' in identifier or 'CASH' in identifier:
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
        
        # 0. Check Asset Universe (Local Resolution)
        if identifier in _UNIVERSE_MAPPING:
            result['isin'] = _UNIVERSE_MAPPING[identifier]
            # If we have the ISIN, we might still want sector/geo from API, 
            # but at least we have the ID.
            print("L", end="", flush=True) # L for Local
        
        # Primary: Finnhub
        try:
            response = session.get(f"{FINNHUB_API_URL}/stock/profile2", params={'symbol': identifier})
            # response.raise_for_status() # Don't raise, just fall through to fallback
            if response.status_code == 200:
                profile_data = response.json()
                if profile_data:
                    # Update result but preserve ISIN if Finnhub misses it
                    finnhub_isin = profile_data.get('isin')
                    
                    result.update({
                        'ticker': profile_data.get('ticker', identifier),
                        'name': profile_data.get('name', 'N/A'),
                        'sector': profile_data.get('finnhubIndustry', 'Unknown'),
                        'geography': profile_data.get('country', 'Unknown')
                    })
                    
                    # Only overwrite ISIN if Finnhub provides a valid one
                    if finnhub_isin:
                        result['isin'] = finnhub_isin
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

def enrich_securities(
    securities: List[Dict[str, Any]], 
    force_refresh: bool = False
) -> List[Dict[str, Any]]:
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