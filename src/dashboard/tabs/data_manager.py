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
    
    # Statistics
    st.subheader("📊 Universe Statistics")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Assets", len(universe_df))
    
    if "Asset_Class" in universe_df.columns:
        asset_counts = universe_df["Asset_Class"].value_counts()
        col2.metric("Asset Types", len(asset_counts))
        col3.metric("Most Common", asset_counts.index[0] if not asset_counts.empty else "N/A")
    
    st.divider()
    
    # Filters
    st.subheader("🔍 Filters")
    
    filter_col1, filter_col2, filter_col3 = st.columns(3)
    
    with filter_col1:
        search_term = st.text_input(
            "Search by Name or ISIN",
            placeholder="e.g., Apple or US0378331005",
            help="Case-insensitive search"
        )
    
    with filter_col2:
        asset_types = ["All"] + sorted(universe_df["Asset_Class"].dropna().unique().tolist()) if "Asset_Class" in universe_df.columns else ["All"]
        selected_type = st.selectbox("Asset Type", asset_types)
    
    with filter_col3:
        provider_options = ["All"] + sorted(universe_df["Provider"].dropna().unique().tolist()) if "Provider" in universe_df.columns else ["All"]
        selected_provider = st.selectbox("Provider", provider_options)
    
    # Apply filters
    filtered_df = universe_df.copy()
    
    if search_term:
        mask = (
            filtered_df["Name"].str.contains(search_term, case=False, na=False) |
            filtered_df["ISIN"].str.contains(search_term, case=False, na=False)
        )
        filtered_df = filtered_df[mask]
    
    if selected_type != "All":
        filtered_df = filtered_df[filtered_df["Asset_Class"] == selected_type]
    
    if selected_provider != "All":
        filtered_df = filtered_df[filtered_df["Provider"] == selected_provider]
    
    # Show filter results
    if len(filtered_df) < len(universe_df):
        st.caption(f"Showing {len(filtered_df)} of {len(universe_df)} assets")
    
    st.divider()
    
    st.subheader("Asset Universe Editor")
    st.caption(f"Editing: `{UNIVERSE_PATH}`")
    
    # Display editor with filtered data
    edited_df = st.data_editor(
        filtered_df,
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
            "Provider": st.column_config.TextColumn("Provider", width="medium"),
        },
        use_container_width=True,
        hide_index=True,
        key="universe_editor"
    )
    
    st.divider()
    
    # Save button
    col1, col2, col3 = st.columns([1, 2, 2])
    with col1:
        if st.button("💾 Save Changes", type="primary"):
            # Merge edited filtered data back into full dataset
            if len(filtered_df) < len(universe_df):
                # User edited a filtered view, need to merge back
                # Update only the rows that were visible
                for idx in edited_df.index:
                    universe_df.loc[idx] = edited_df.loc[idx]
                final_df = universe_df
            else:
                # User edited full dataset
                final_df = edited_df
            
            if save_universe(final_df):
                # Clear pending fix after successful save
                if "pending_fix" in st.session_state:
                    st.session_state.pending_fix = None
    
    with col2:
        st.caption("Changes will be backed up automatically before saving.")
    
    with col3:
        if st.button("🔄 Reset Filters"):
            st.rerun()
