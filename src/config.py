import os
from pathlib import Path

# Base project directory (2 levels up from src/config.py)
PROJECT_ROOT = Path(__file__).parent.parent.resolve()

# Proxy configuration (for Docker distribution)
# When set, API calls route through the proxy instead of direct calls
PROXY_URL = os.getenv("PROXY_URL")  # e.g., https://portfolio-api.helmus.me
PROXY_API_KEY = os.getenv("PROXY_API_KEY")

# Data Directories
DATA_DIR = PROJECT_ROOT / "data"
INPUTS_DIR = DATA_DIR / "inputs"
MANUAL_INPUTS_DIR = INPUTS_DIR / "manual_holdings"
WORKING_DIR = DATA_DIR / "working"
RAW_DOWNLOADS_DIR = WORKING_DIR / "raw_downloads"
CONFIG_DIR = PROJECT_ROOT / "config"

# File Paths
ASSET_UNIVERSE_PATH = CONFIG_DIR / "asset_universe.csv"

# Output Directories
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
REPORTS_DIR = OUTPUTS_DIR  # For now, reports go to root of outputs

# File Paths
TRUE_EXPOSURE_REPORT = REPORTS_DIR / "true_exposure_report.csv"
HOLDINGS_BREAKDOWN_PATH = OUTPUTS_DIR / "holdings_breakdown.csv"
TRADES_FILE = OUTPUTS_DIR / "trades.csv"
POSITIONS_FILE = OUTPUTS_DIR / "positions_with_prices.csv"

# Ensure directories exist
for directory in [
    DATA_DIR,
    INPUTS_DIR,
    MANUAL_INPUTS_DIR,
    WORKING_DIR,
    RAW_DOWNLOADS_DIR,
    OUTPUTS_DIR,
]:
    directory.mkdir(parents=True, exist_ok=True)
