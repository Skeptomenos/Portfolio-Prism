import streamlit as st
import pandas as pd
from src.dashboard.utils import load_direct_holdings, load_holdings_breakdown

def render_etf_explorer(direct_df: pd.DataFrame, breakdown_df: pd.DataFrame):
    """Render the 'What's inside this ETF?' view."""
    st.subheader("📦 ETF Explorer")
    
    # Filter for ETFs only
    etf_options = direct_df[direct_df["asset_type"] == "ETF"].sort_values("name")
    
    if etf_options.empty:
        st.warning("No ETFs found in direct holdings.")
        return

    # Select ETF
    selected_name = st.selectbox(
        "Select ETF to Inspect",
        etf_options["name"].tolist(),
        index=0
    )
    
    # Get ISIN for selected ETF
    etf_isin = etf_options[etf_options["name"] == selected_name]["isin"].iloc[0]
    
    # Filter breakdown for this parent
    holdings = breakdown_df[breakdown_df["parent_isin"] == etf_isin].copy()
    
    if holdings.empty:
        st.info(f"No holdings found for {selected_name} ({etf_isin}).")
        return

    # Summary Stats
    col1, col2, col3 = st.columns(3)
    col1.metric("Holdings Count", len(holdings))
    col2.metric("Total Value in Portfolio", f"€{holdings['value_eur'].sum():,.2f}")
    
    # Safe mode extraction
    sector_mode = holdings["sector"].mode()
    top_sector = sector_mode[0] if len(sector_mode) > 0 else "N/A"
    col3.metric("Top Sector", top_sector)

    # Table
    st.dataframe(
        holdings[["child_name", "child_isin", "weight_percent", "value_eur", "sector", "geography"]]
        .sort_values("value_eur", ascending=False)
        .rename(columns={
            "child_name": "Name",
            "child_isin": "ISIN",
            "weight_percent": "Weight (%)",
            "value_eur": "Value (€)",
            "sector": "Sector",
            "geography": "Region"
        }),
        column_config={
            "Weight (%)": st.column_config.NumberColumn(format="%.4f%%"),
            "Value (€)": st.column_config.NumberColumn(format="€%.2f"),
        },
        use_container_width=True,
        hide_index=True
    )

def render_stock_lookup(direct_df: pd.DataFrame, breakdown_df: pd.DataFrame):
    """Render the 'Where is my exposure?' view."""
    st.subheader("🔍 Stock Exposure Lookup")
    
    # Get all unique child names for autocomplete
    all_names = sorted(breakdown_df["child_name"].dropna().unique().tolist())
    
    search_term = st.selectbox(
        "Search for a Stock (e.g., Apple, NVIDIA)",
        options=all_names,
        index=None,
        placeholder="Type to search..."
    )
    
    if not search_term:
        st.info("Start typing to see your consolidated exposure.")
        return

    # Find matches
    # 1. Direct Exposure
    direct_match = direct_df[direct_df["name"] == search_term]
    direct_val = direct_match["market_value"].sum() if not direct_match.empty else 0.0
    
    # 2. Indirect Exposure (via ETFs)
    # Filter breakdown where child_name matches AND parent is NOT 'DIRECT'
    indirect_match = breakdown_df[
        (breakdown_df["child_name"] == search_term) & 
        (breakdown_df["parent_isin"] != "DIRECT")
    ]
    indirect_val = indirect_match["value_eur"].sum()
    
    total_val = direct_val + indirect_val
    
    if total_val == 0:
        st.warning(f"No exposure found for {search_term}.")
        return

    # Summary Card
    st.success(f"**{search_term}**")
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Exposure", f"€{total_val:,.2f}")
    c2.metric("Direct", f"€{direct_val:,.2f}", delta=f"{direct_val/total_val:.1%}" if total_val > 0 else None)
    c3.metric("Via ETFs", f"€{indirect_val:,.2f}", delta=f"{indirect_val/total_val:.1%}" if total_val > 0 else None)
    
    # Breakdown Table
    st.write("### Exposure Sources")
    
    # Prepare table data
    sources = []
    
    # Add Direct if exists
    if direct_val > 0:
        sources.append({
            "Source": "Direct Portfolio",
            "Type": "Direct",
            "Weight in Source": "100%",
            "Your Value": direct_val
        })
        
    # Add ETFs
    for _, row in indirect_match.iterrows():
        sources.append({
            "Source": row["parent_name"],
            "Type": "ETF",
            "Weight in Source": f"{row['weight_percent']:.2f}%",
            "Your Value": row["value_eur"]
        })
        
    source_df = pd.DataFrame(sources)
    
    st.dataframe(
        source_df,
        column_config={
            "Your Value": st.column_config.NumberColumn(format="€%.2f")
        },
        use_container_width=True,
        hide_index=True
    )

def render():
    st.header("Holdings Analysis")
    
    # Load Data
    direct_df = load_direct_holdings()
    breakdown_df = load_holdings_breakdown()
    
    if direct_df.empty or breakdown_df.empty:
        st.error("Missing data. Please run the pipeline first.")
        return

    # Mode Toggle
    mode = st.radio(
        "Analysis Mode",
        ["📦 Explore ETF", "🔍 Search Stock"],
        horizontal=True,
        label_visibility="collapsed"
    )
    
    st.divider()
    
    if mode == "📦 Explore ETF":
        render_etf_explorer(direct_df, breakdown_df)
    else:
        render_stock_lookup(direct_df, breakdown_df)
