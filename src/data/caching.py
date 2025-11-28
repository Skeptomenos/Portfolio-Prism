# phases/shared/caching.py
import os
import json
import pandas as pd
from functools import wraps
from datetime import datetime, timedelta
from src.utils.logging_config import get_logger
from src.utils.metrics import tracker

logger = get_logger(__name__)

CACHE_DIR = "data/working/cache/adapter_cache"
os.makedirs(CACHE_DIR, exist_ok=True)

ENRICHMENT_CACHE_FILE = "data/working/cache/enrichment_cache.json"


def get_cache_key(identifier: str) -> str:
    """Generates a standardized cache key."""
    return str(identifier).upper().strip()


def _load_json_cache():
    """Helper to load the entire JSON cache."""
    if not os.path.exists(ENRICHMENT_CACHE_FILE):
        return {}
    try:
        with open(ENRICHMENT_CACHE_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        logger.error(
            f"Corrupt cache file at {ENRICHMENT_CACHE_FILE}. Returning empty cache."
        )
        return {}


def _save_json_cache(cache_data):
    """Helper to save the entire JSON cache."""
    os.makedirs(os.path.dirname(ENRICHMENT_CACHE_FILE), exist_ok=True)
    with open(ENRICHMENT_CACHE_FILE, "w") as f:
        json.dump(cache_data, f, indent=2)


def load_from_cache(key: str):
    """Retrieves a value from the JSON cache."""
    cache = _load_json_cache()
    return cache.get(key)


def save_to_cache(key: str, data: dict):
    """Saves a key-value pair to the JSON cache."""
    cache = _load_json_cache()
    cache[key] = data
    _save_json_cache(cache)


def cache_adapter_data(ttl_hours: int = 24):
    """
    A decorator to cache the DataFrame returned by an adapter's fetch_holdings method.

    The cache is considered "fresh" if the file is less than ttl_hours old.
    It saves the DataFrame to a CSV file named after the ISIN and the adapter class.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(self, isin: str, *args, **kwargs):
            class_name = self.__class__.__name__
            cache_file = os.path.join(CACHE_DIR, f"{isin}_{class_name}.csv")

            # Check if a fresh cache file exists
            if os.path.exists(cache_file):
                modified_time = datetime.fromtimestamp(os.path.getmtime(cache_file))
                if datetime.now() - modified_time < timedelta(hours=ttl_hours):
                    logger.info(
                        f"Loading fresh data for {isin} from cache: {cache_file}"
                    )
                    tracker.increment_system_metric("cache_hits")
                    return pd.read_csv(cache_file)

            # If no fresh cache, run the original function
            logger.info(
                f"No fresh cache for {isin}. Fetching live data using {class_name}."
            )
            tracker.increment_system_metric("api_calls_providers")
            result_df = func(self, isin, *args, **kwargs)

            # Save the new result to cache, but only if it's valid (not empty)
            if not result_df.empty:
                logger.info(f"Saving new data for {isin} to cache: {cache_file}")
                result_df.to_csv(cache_file, index=False)
            else:
                logger.warning(
                    f"Adapter {class_name} returned an empty DataFrame for {isin}. Not caching."
                )

            return result_df

        return wrapper

    return decorator
