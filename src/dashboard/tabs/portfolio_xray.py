import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from src.dashboard.utils import load_direct_holdings, load_exposure_report

def render():
    st.header("📊 Portfolio X-Ray")
    
    # Load Data
    direct_df = load_direct_holdings()
    exposure_df = load_exposure_report()
    
    if direct_df.empty:
        st.error("Missing data. Please run the pipeline first.")
        return

    # KPIs Row
    st.subheader("Portfolio Overview")
    
    col1, col2, col3 = st.columns(3)
    
    total_value = direct_df["market_value"].sum()
    num_positions = len(direct_df)
    unique_assets = len(exposure_df) if not exposure_df.empty else num_positions
    
    col1.metric("Total Portfolio Value", f"€{total_value:,.2f}")
    col2.metric("Direct Positions", num_positions)
    col3.metric("Unique Underlying Assets", unique_assets)
    
    st.divider()
    
    # Charts Section
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.subheader("📈 Top 10 Holdings")
        
        # Use exposure report if available, otherwise direct holdings
        if not exposure_df.empty and "total_exposure" in exposure_df.columns:
            top_10 = exposure_df.nlargest(10, "total_exposure")
            value_col = "total_exposure"
        else:
            top_10 = direct_df.nlargest(10, "market_value")
            value_col = "market_value"
        
        # Create horizontal bar chart
        fig_top = px.bar(
            top_10.sort_values(value_col),
            x=value_col,
            y="name",
            orientation="h",
            labels={value_col: "Exposure (€)", "name": ""},
            color=value_col,
            color_continuous_scale="Blues"
        )
        fig_top.update_layout(
            showlegend=False,
            height=400,
            margin=dict(l=0, r=0, t=0, b=0)
        )
        st.plotly_chart(fig_top, use_container_width=True)
    
    with col_right:
        st.subheader("🎯 Asset Allocation")
        
        # Group by asset type
        if "asset_type" in direct_df.columns:
            allocation = direct_df.groupby("asset_type")["market_value"].sum().reset_index()
            allocation.columns = ["Asset Type", "Value"]
            
            # Create pie chart
            fig_pie = px.pie(
                allocation,
                values="Value",
                names="Asset Type",
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            fig_pie.update_layout(
                height=400,
                margin=dict(l=0, r=0, t=0, b=0)
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Asset type information not available.")
    
    st.divider()
    
    # Detailed Holdings Table
    st.subheader("📋 All Holdings")
    
    display_df = direct_df[["name", "isin", "asset_type", "market_value"]].copy()
    display_df = display_df.sort_values("market_value", ascending=False)
    
    # Calculate percentage
    display_df["percentage"] = (display_df["market_value"] / total_value * 100)
    
    st.dataframe(
        display_df.rename(columns={
            "name": "Name",
            "isin": "ISIN",
            "asset_type": "Type",
            "market_value": "Value (€)",
            "percentage": "% of Portfolio"
        }),
        column_config={
            "Value (€)": st.column_config.NumberColumn(format="€%.2f"),
            "% of Portfolio": st.column_config.NumberColumn(format="%.2f%%")
        },
        use_container_width=True,
        hide_index=True
    )
