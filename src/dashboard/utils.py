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


def get_isin_name_mapping(breakdown_df: pd.DataFrame) -> dict:
    """
    Build mapping of ISIN -> canonical name.

    Priority for canonical name:
    1. Name from asset_universe.csv (if ISIN exists there)
    2. Most frequent name in breakdown data for that ISIN

    Args:
        breakdown_df: Holdings breakdown DataFrame with child_isin, child_name columns

    Returns:
        dict[str, str]: {isin: canonical_name}
    """
    if breakdown_df.empty:
        return {}

    # Load asset universe for canonical names
    universe_df = load_asset_universe()
    universe_names = {}
    if (
        not universe_df.empty
        and "ISIN" in universe_df.columns
        and "Name" in universe_df.columns
    ):
        universe_names = (
            universe_df.dropna(subset=["ISIN", "Name"])
            .drop_duplicates(subset=["ISIN"], keep="first")
            .set_index("ISIN")["Name"]
            .to_dict()
        )

    # Get unique ISINs from breakdown
    isin_to_name = {}

    for isin in breakdown_df["child_isin"].dropna().unique():
        isin_str = str(isin)

        # Priority 1: Use name from asset_universe if available
        if isin_str in universe_names:
            isin_to_name[isin_str] = universe_names[isin_str]
            continue

        # Priority 2: Use most frequent name in breakdown data
        names_for_isin = breakdown_df[breakdown_df["child_isin"] == isin]["child_name"]
        if not names_for_isin.empty:
            # Get most common name
            most_common = names_for_isin.mode()
            if len(most_common) > 0:
                isin_to_name[isin_str] = most_common.iloc[0]
            else:
                isin_to_name[isin_str] = names_for_isin.iloc[0]

    return isin_to_name
