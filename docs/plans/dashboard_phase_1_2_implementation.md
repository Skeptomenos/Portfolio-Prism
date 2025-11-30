# Implementation Plan: Dashboard Phase 1 & 2

## Goal
Initialize the Streamlit dashboard environment and implement the "Pipeline Health & Errors" tab (Phase 1 & 2).
This transforms the system from a CLI-only tool to a GUI-based application, starting with observability.

## User Review Required
> [!NOTE]
> This plan introduces `streamlit` and `plotly` as new dependencies.

## Proposed Changes

### 1. Environment & Dependencies (Phase 1)

#### [MODIFY] [requirements.txt](file:///Users/davidhelmus/Repos/portfolio-master/POC/requirements.txt)
- Add `streamlit>=1.30.0`
- Add `plotly>=5.18.0`
- Add `pandas>=2.0.0` (ensure version)

#### [NEW] [run_dashboard.sh](file:///Users/davidhelmus/Repos/portfolio-master/POC/run_dashboard.sh)
- Script to activate venv and run `streamlit run src/dashboard/app.py`

### 2. Dashboard Structure (Phase 2)

#### [NEW] [src/dashboard/__init__.py](file:///Users/davidhelmus/Repos/portfolio-master/POC/src/dashboard/__init__.py)
- Empty marker file.

#### [NEW] [src/dashboard/app.py](file:///Users/davidhelmus/Repos/portfolio-master/POC/src/dashboard/app.py)
- Main entry point.
- Sets up page config (layout, title).
- Loads CSS (if any).
- Implements the Tab container (`st.tabs`).
- **Logic:**
  - Tab 1: Portfolio X-Ray (Placeholder)
  - Tab 2: Holdings Analysis (Placeholder)
  - Tab 3: Data Manager (Placeholder)
  - Tab 4: Pipeline Health (Imports `tabs.pipeline_health`)

#### [NEW] [src/dashboard/tabs/__init__.py](file:///Users/davidhelmus/Repos/portfolio-master/POC/src/dashboard/tabs/__init__.py)
- Empty marker file.

#### [NEW] [src/dashboard/tabs/pipeline_health.py](file:///Users/davidhelmus/Repos/portfolio-master/POC/src/dashboard/tabs/pipeline_health.py)
- Implements the "Pipeline Stats & Errors" view.
- **Functions:**
  - `render()`: Main render function called by `app.py`.
  - `load_health_data()`: Reads `outputs/pipeline_health.json`.
  - `render_metrics(data)`: Displays the top-level KPIs (Direct Holdings, ETFs Processed, etc.).
  - `render_etf_stats(data)`: Displays the ETF processing table.
  - `render_failures(data)`: Displays the error table with "Fix" buttons (UI only for now).

### 3. Data Integration

#### [NEW] [src/dashboard/utils.py](file:///Users/davidhelmus/Repos/portfolio-master/POC/src/dashboard/utils.py)
- **New File**
- Helper functions for loading JSON/CSV data safely.
- Caching decorators (`@st.cache_data`) to prevent re-reading files on every interaction.

## Verification Plan

### Automated Verification
1. **Dependency Check:**
   ```bash
   pip install -r requirements.txt
   python -c "import streamlit; import plotly; print('Deps OK')"
   ```

2. **Data Existence:**
   - Ensure `outputs/pipeline_health.json` exists (run pipeline if needed).

### Manual Verification
1. **Launch Dashboard:**
   ```bash
   ./run_dashboard.sh
   ```
2. **Visual Check:**
   - Verify Browser opens to localhost:8501.
   - Verify Title "Portfolio Analysis System".
   - Click "Pipeline Health" tab.
   - **Verify KPIs:** Check if numbers match `pipeline_health.json`.
   - **Verify Error Table:** Check if "Fix" buttons appear (even if they don't do anything yet).
