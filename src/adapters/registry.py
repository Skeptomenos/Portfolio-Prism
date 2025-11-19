# phases/active/holdings_fetcher.py
import os
import json
import sys
import pandas as pd

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.adapters.vaneck import VanEckAdapter
from src.adapters.ishares import ISharesAdapter
from src.adapters.xtrackers import XtrackersAdapter
from src.adapters.amundi import AmundiAdapter
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

class AdapterRegistry:
    """
    A single point of responsibility for selecting and instantiating the correct adapter.
    This class implements the Factory pattern for our adapters.
    """
    def __init__(self, config_path=os.path.join(project_root, 'config', 'adapter_registry.json')):
        self._isin_to_key = self._load_config(config_path)
        self._key_to_class = {
            "ishares": ISharesAdapter,
            "vaneck": VanEckAdapter,
            "amundi": AmundiAdapter,
            "xtrackers": XtrackersAdapter
        }
        logger.info("AdapterRegistry initialized.")

    def _load_config(self, path):
        """Loads the ISIN-to-adapter mapping from the JSON config."""
        logger.info(f"Loading adapter configuration from: {path}")
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Adapter config file not found at {path}. Registry will be empty.")
            return {}
        except json.JSONDecodeError:
            logger.error(f"Error decoding JSON from adapter config file at {path}.")
            return {}

    def get_adapter(self, isin: str):
        """
        Returns an instantiated adapter for a given ISIN.
        
        Args:
            isin: The ISIN of the ETF.
            
        Returns:
            An instantiated adapter object or None if no adapter is found.
        """
        adapter_key = self._isin_to_key.get(isin)
        if not adapter_key:
            logger.warning(f"No adapter key found for ISIN {isin} in the registry.")
            return None
        
        AdapterClass = self._key_to_class.get(adapter_key)
        if not AdapterClass:
            logger.error(f"Adapter key '{adapter_key}' for ISIN {isin} is not mapped to a valid class.")
            return None

        try:
            # Handle adapters that require special instantiation (e.g., with ISIN)
            if AdapterClass is VanEckAdapter:
                return AdapterClass(isin=isin)
            return AdapterClass()
        except Exception as e:
            logger.error(f"Failed to instantiate adapter {AdapterClass.__name__} for ISIN {isin}: {e}")
            return None