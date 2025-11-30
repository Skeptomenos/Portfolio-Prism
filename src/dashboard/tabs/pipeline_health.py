import streamlit as st
import pandas as pd
from src.dashboard.utils import load_pipeline_health

def render_metrics(data: dict):
    """Render top-level KPIs."""
    metrics = data.get("metrics", {})
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Direct Holdings", metrics.get("direct_holdings", 0))
    with col2:
        processed = metrics.get("etfs_processed", 0)
        total = metrics.get("etf_positions", 0)
        st.metric("ETFs Processed", f"{processed}/{total}")
    with col3:
        st.metric("ISINs Resolved", metrics.get("tier1_resolved", 0))
    with col4:
        failed = metrics.get("tier1_failed", 0)
        st.metric("Resolution Failures", failed, delta=-failed if failed > 0 else 0)

def render_etf_stats(data: dict):
    """Render ETF processing statistics."""
    st.subheader("📦 ETF Processing Status")
    
    etf_stats = data.get("etf_stats", [])
    if not etf_stats:
        st.info("No ETF statistics available.")
        return

    df = pd.DataFrame(etf_stats)
    
    # Rename columns for display
    df = df.rename(columns={
        "ticker": "ISIN",
        "holdings_count": "Holdings",
        "weight_sum": "Weight Sum (%)",
        "status": "Status"
    })
    
    st.dataframe(
        df,
        column_config={
            "Weight Sum (%)": st.column_config.NumberColumn(format="%.2f%%"),
            "Status": st.column_config.TextColumn()
        },
        use_container_width=True,
        hide_index=True
    )

def render_failures(data: dict):
    """Render error table with actionable fixes."""
    st.subheader("⚠️ Action Required")
    
    failures = data.get("failures", [])
    if not failures:
        st.success("✅ No errors found in the last run!")
        return

    # Convert to DataFrame
    df = pd.DataFrame(failures)
    
    # Display as a table with "Fix" buttons (simulated for now)
    for index, row in df.iterrows():
        with st.expander(f"{row.get('severity', 'UNKNOWN')} | {row.get('item', 'Unknown')} - {row.get('error', 'Error')}"):
            st.write(f"**Stage:** {row.get('stage')}")
            st.write(f"**Error:** {row.get('error')}")
            st.write(f"**Suggested Fix:** {row.get('fix')}")
            
            if st.button(f"Fix {row.get('item')}", key=f"fix_{index}"):
                st.session_state["pending_fix"] = {
                    "ticker": row.get("item"),
                    "fix_hint": row.get("fix")
                }
                st.toast("💡 Fix request sent to Data Manager tab!", icon="ℹ️")
                st.info("→ Navigate to the **🛠️ Data Manager** tab to add the missing ISIN.")

def render():
    st.header("Pipeline Health & Status")
    
    data = load_pipeline_health()
    if not data:
        st.warning("No pipeline health data found. Please run the pipeline first.")
        return

    st.caption(f"Last Run: {data.get('timestamp', 'Unknown')}")
    
    render_metrics(data)
    st.divider()
    render_etf_stats(data)
    st.divider()
    render_failures(data)
