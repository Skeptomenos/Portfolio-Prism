import streamlit as st
import pandas as pd
import json
import plotly.express as px
import os

# Page Config
st.set_page_config(page_title="Portfolio True Exposure", page_icon="📊", layout="wide")

# Constants
OUTPUT_DIR = "outputs"
CSV_PATH = os.path.join(OUTPUT_DIR, "true_exposure_report.csv")
DIRECT_CSV_PATH = os.path.join(OUTPUT_DIR, "direct_holdings_report.csv")
METRICS_PATH = os.path.join(OUTPUT_DIR, "pipeline_metrics.json")
QUALITY_PATH = os.path.join(OUTPUT_DIR, "data_quality_report.txt")


def load_data():
    """Loads the latest available data."""
    df = None
    direct_df = None
    metrics = None
    quality_text = ""

    if os.path.exists(CSV_PATH):
        df = pd.read_csv(CSV_PATH)

    if os.path.exists(DIRECT_CSV_PATH):
        direct_df = pd.read_csv(DIRECT_CSV_PATH)

    if os.path.exists(METRICS_PATH):
        with open(METRICS_PATH, "r") as f:
            metrics = json.load(f)

    if os.path.exists(QUALITY_PATH):
        with open(QUALITY_PATH, "r") as f:
            quality_text = f.read()

    return df, direct_df, metrics, quality_text


df, direct_df, metrics, quality_text = load_data()

st.title("📊 Portfolio True Exposure Dashboard")

if df is None:
    st.warning("⚠️ No data found. Please run the pipeline first.")
    st.stop()

# Tabs
tab1, tab2, tab3 = st.tabs(
    ["💰 Portfolio X-Ray", "🔍 Direct Holdings Audit", "🛠️ Pipeline Health"]
)

with tab1:
    st.header("Financial Exposure")

    # KPIs
    total_value = df["total_exposure"].sum()
    st.metric("Total Portfolio Value (Indirect)", f"€{total_value:,.2f}")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Top 10 Holdings")
        top_10 = df.nlargest(10, "total_exposure")
        fig_bar = px.bar(
            top_10,
            x="total_exposure",
            y="name",
            orientation="h",
            title="Top 10 Underlying Assets (Direct + Indirect)",
            labels={"total_exposure": "Value (€)", "name": "Asset"},
            text_auto=".2s",
        )
        fig_bar.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig_bar, use_container_width=True)

    with col2:
        st.subheader("Asset Allocation (Sunburst)")
        # Create a hierarchy for the sunburst
        # Ideally we'd have Sector/Region, but for now we use asset_type -> name
        # If we had sector data in the CSV, we'd use it here.
        # Let's check columns: 'isin', 'name', 'total_exposure', 'weight_pct', 'asset_type' (maybe?)
        # The aggregation output usually has: isin, name, total_exposure, weight_in_portfolio

        # We'll use a simple Pie chart for now if hierarchy is missing
        fig_pie = px.pie(
            df.head(20),  # Top 20 for readability
            values="total_exposure",
            names="name",
            title="Top 20 Assets Allocation",
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    st.subheader("Full Holdings Search")
    search_term = st.text_input("Search for an asset (e.g. 'Nvidia', 'Apple')", "")
    if search_term:
        filtered_df = df[df["name"].str.contains(search_term, case=False, na=False)]
        st.dataframe(filtered_df.sort_values(by="total_exposure", ascending=False))
    else:
        st.dataframe(df.sort_values(by="total_exposure", ascending=False).head(50))

with tab2:
    st.header("Direct Holdings Audit")
    if direct_df is not None:
        total_direct = direct_df["market_value"].sum()
        st.metric("Total Portfolio Value (Direct)", f"€{total_direct:,.2f}")

        st.dataframe(
            direct_df.style.format(
                {
                    "market_value": "€{:.2f}",
                    "current_price": "€{:.2f}",
                    "portfolio_weight": "{:.2%}",
                }
            ),
            use_container_width=True,
        )
    else:
        st.warning("No Direct Holdings report found.")

with tab3:
    st.header("Pipeline Operations & Health")

    if metrics:
        col1, col2, col3 = st.columns(3)
        col1.metric("Execution Time", f"{metrics.get('duration_seconds', 0):.2f}s")

        sys_metrics = metrics.get("system", {})
        col2.metric("Cache Hits", sys_metrics.get("cache_hits", 0))
        col3.metric("API Calls", sys_metrics.get("api_calls_providers", 0))

        st.divider()

        st.subheader("Data Funnel")
        funnel = metrics.get("funnel", {})
        funnel_df = pd.DataFrame(list(funnel.items()), columns=["Stage", "Count"])
        fig_funnel = px.funnel(funnel_df, x="Count", y="Stage")
        st.plotly_chart(fig_funnel, use_container_width=True)

    else:
        st.info("No metrics file found.")

    st.subheader("⚠️ Data Quality Report")
    if quality_text:
        st.text_area("Known Gaps & Failures", quality_text, height=200)
    else:
        st.success("No data quality issues reported.")
