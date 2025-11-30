import streamlit as st
import pandas as pd
import shutil
from datetime import datetime
from pathlib import Path
from src.dashboard.utils import load_asset_universe

# Constants
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
UNIVERSE_PATH = CONFIG_DIR / "asset_universe.csv"

def save_universe(df: pd.DataFrame) -> bool:
    """Save the asset universe with backup and validation."""
    
    # Backup first
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = CONFIG_DIR / f"asset_universe.csv.bak.{timestamp}"
    
    try:
        if UNIVERSE_PATH.exists():
            shutil.copy(UNIVERSE_PATH, backup_path)
            st.success(f"✅ Backup created: {backup_path.name}")
        
        # Validation
        errors = []
        
        # Check for duplicate ISINs
        dupes = df[df["ISIN"].duplicated(keep=False)]
        if not dupes.empty:
            errors.append(f"⚠️ Duplicate ISINs found: {dupes['ISIN'].unique().tolist()}")
        
        # Check for empty ISINs
        empty_isins = df[df["ISIN"].isna() | (df["ISIN"] == "")]
        if not empty_isins.empty:
            errors.append(f"⚠️ {len(empty_isins)} rows have empty ISINs")
        
        # Display warnings but don't block
        if errors:
            for error in errors:
                st.warning(error)
        
        # Save
        df.to_csv(UNIVERSE_PATH, index=False)
        st.success("✅ Saved successfully!")
        
        # Clear cache to reload fresh data
        st.cache_data.clear()
        
        return True
        
    except Exception as e:
        st.error(f"❌ Failed to save: {e}")
        return False

def render():
    st.header("🛠️ Data Manager")
    
    # Check for pending fix from Health tab
    if "pending_fix" in st.session_state and st.session_state.pending_fix:
        fix = st.session_state.pending_fix
        st.info(f"💡 **Fix Request:** Add ISIN for `{fix.get('ticker')}` — {fix.get('fix_hint')}")
        
        if st.button("Clear Fix Request"):
            st.session_state.pending_fix = None
            st.rerun()
    
    st.divider()
    
    # Load current universe
    universe_df = load_asset_universe()
    
    if universe_df.empty:
        st.error("Asset universe file not found or empty.")
        return
    
    st.subheader("Asset Universe Editor")
    st.caption(f"Editing: `{UNIVERSE_PATH}`")
    
    # Display editor
    edited_df = st.data_editor(
        universe_df,
        num_rows="dynamic",
        column_config={
            "ISIN": st.column_config.TextColumn("ISIN", required=True, width="medium"),
            "Name": st.column_config.TextColumn("Name", width="large"),
            "Yahoo_Ticker": st.column_config.TextColumn("Ticker", width="medium"),
            "Asset_Class": st.column_config.SelectboxColumn(
                "Type", 
                options=["Stock", "ETF", "Bond", "Commodity"],
                width="small"
            ),
        },
        use_container_width=True,
        hide_index=True,
        key="universe_editor"
    )
    
    st.divider()
    
    # Save button
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("💾 Save Changes", type="primary"):
            if save_universe(edited_df):
                # Clear pending fix after successful save
                if "pending_fix" in st.session_state:
                    st.session_state.pending_fix = None
    
    with col2:
        st.caption("Changes will be backed up automatically before saving.")
