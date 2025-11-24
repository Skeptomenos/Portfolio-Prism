# phases/active/holdings_fetcher.py
import os
import json
import pandas as pd
from datetime import datetime

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.adapters.vaneck import VanEckAdapter
from src.adapters.ishares import ISharesAdapter
from src.adapters.xtrackers import XtrackersAdapter
from src.adapters.amundi import AmundiAdapter
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

class AdapterNotImplementedError(Exception):
    """Raised when an adapter key exists in config but no class is implemented."""
    pass

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

    def _log_feature_request(self, provider_key, isin):
        """Appends a feature request to the BACKLOG.md file."""
        backlog_path = os.path.join(project_root, 'docs', 'BACKLOG.md')
        try:
            # Read existing content to check for duplicates
            existing_content = ""
            if os.path.exists(backlog_path):
                with open(backlog_path, 'r') as f:
                    existing_content = f.read()
            
            request_line = f"- [ ] Create adapter for provider: '{provider_key}'"
            
            if request_line not in existing_content:
                with open(backlog_path, 'a') as f:
                    f.write(f"\n{request_line} (Triggered by ISIN: {isin} on {datetime.now().strftime('%Y-%m-%d')})")
                logger.info(f"Added feature request for '{provider_key}' to BACKLOG.md")
        except Exception as e:
            logger.error(f"Failed to write to backlog: {e}")

    def get_adapter(self, isin: str):
        """
        Returns an instantiated adapter for a given ISIN.
        
        Args:
            isin: The ISIN of the ETF.
            
        Returns:
            An instantiated adapter object or None if no adapter is found.
        
        Raises:
            AdapterNotImplementedError: If the provider is known but not implemented.
        """
        adapter_key = self._isin_to_key.get(isin)
        
        if not adapter_key or adapter_key == "ignore":
            return None
        
        AdapterClass = self._key_to_class.get(adapter_key)
        if not AdapterClass:
            logger.warning(f"Adapter key '{adapter_key}' for ISIN {isin} is not implemented yet.")
            self._log_feature_request(adapter_key, isin)
            raise AdapterNotImplementedError(f"Provider '{adapter_key}' is not supported yet.")

        try:
            # Handle adapters that require special instantiation (e.g., with ISIN)
            if AdapterClass is VanEckAdapter:
                return AdapterClass(isin=isin)
            return AdapterClass()
        except Exception as e:
            logger.error(f"Failed to instantiate adapter {AdapterClass.__name__} for ISIN {isin}: {e}")
            return None
