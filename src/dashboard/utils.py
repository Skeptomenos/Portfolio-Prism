import json
import pandas as pd
import streamlit as st
from pathlib import Path

# Constants
PROJECT_ROOT = Path(__file__).parent.parent.parent
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
CONFIG_DIR = PROJECT_ROOT / "config"

PIPELINE_HEALTH_PATH = OUTPUTS_DIR / "pipeline_health.json"

@st.cache_data
def load_pipeline_health() -> dict:
    """Load the pipeline health JSON file."""
    if not PIPELINE_HEALTH_PATH.exists():
        return {}
    
    try:
        with open(PIPELINE_HEALTH_PATH, "r") as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Failed to load pipeline health: {e}")
        return {}

@st.cache_data
def load_direct_holdings() -> pd.DataFrame:
    """Load direct holdings report."""
    path = OUTPUTS_DIR / "direct_holdings_report.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)

@st.cache_data
def load_holdings_breakdown() -> pd.DataFrame:
    """Load holdings breakdown report."""
    path = OUTPUTS_DIR / "holdings_breakdown.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)

@st.cache_data
def load_asset_universe() -> pd.DataFrame:
    """Load asset universe configuration."""
    path = CONFIG_DIR / "asset_universe.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)

@st.cache_data
def load_exposure_report() -> pd.DataFrame:
    """Load true exposure report."""
    path = OUTPUTS_DIR / "true_exposure_report.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)
