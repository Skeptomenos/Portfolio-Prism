import streamlit as st
from pathlib import Path
import sys

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

from src.dashboard.tabs import (
    pipeline_health,
    holdings_analysis,
    data_manager,
    portfolio_xray,
    performance,
    etf_overlap,
)

st.set_page_config(
    page_title="Portfolio Analysis System",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("📊 Portfolio Analysis System")

# Tabs - Performance first as it's the primary user interest
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
    [
        "📈 Performance",
        "🔍 Portfolio X-Ray",
        "🔄 ETF Overlap",
        "📦 Holdings Analysis",
        "🛠️ Data Manager",
        "🏥 Pipeline Health",
    ]
)

with tab1:
    performance.render()

with tab2:
    portfolio_xray.render()

with tab3:
    etf_overlap.render()

with tab4:
    holdings_analysis.render()

with tab5:
    data_manager.render()

with tab6:
    pipeline_health.render()
