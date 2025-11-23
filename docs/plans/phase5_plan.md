# Phase 5 Plan: Visualization & Pipeline Intelligence [COMPLETE]

**Objective:** Create an interactive dashboard that provides dual insights: **Financial Exposure** (What do I own?) and **Pipeline Health** (How well is the tool working?). This visibility is crucial for identifying data gaps and prioritizing future adapter development.

## 1. Architecture: The "Glass Box" Dashboard

We will use **Streamlit** for the UI due to its speed of iteration and native support for Pandas/Plotly.

### Data Sources
1.  **Portfolio Data:** `outputs/true_exposure_report.csv` (The financial output).
2.  **Quality Data:** `outputs/data_quality_report.txt` (The known failures).
3.  **Run Metrics:** `outputs/pipeline_metrics.json` (**NEW** - needs to be created).
    *   We need to instrument the pipeline to save structured stats (e.g., Total Positions, ETFs Processed, Cache Hits/Misses, API Errors).

## 2. Dashboard Layout

### Tab 1: Portfolio X-Ray (Financials)
*   **Sunburst Chart:** Interactive drill-down: Asset Class $\rightarrow$ Region $\rightarrow$ Sector.
*   **Top Holdings:** Bar chart of the top 20 underlying assets by absolute value (€).
*   **Search:** "Do I own 'Nvidia'?" - Quick lookup to see effective weight and value across all ETFs.

### Tab 2: Pipeline Health (Operations)
*   **The "Data Funnel":** A funnel chart showing the flow of assets:
    *   Total Positions in DB
    *   $\rightarrow$ Mapped to Adapter
    *   $\rightarrow$ Successfully Fetched
    *   $\rightarrow$ Successfully Enriched
    *   $\rightarrow$ Final Report
*   **Gap Analysis:** A structured table of "Missing Data" (reading from the Quality Report), grouped by Provider (e.g., "Vanguard: 3 ETFs missing"). This directly informs the roadmap.
*   **Operational Metrics:**
    *   Execution Time.
    *   API Cache Hit Rate (Efficiency).
    *   Data Freshness (Last run timestamp).

## 3. Implementation Steps

### Step 1: Instrument the Pipeline (`src/utils/metrics.py`) [Done]
*   **Task:** Create a simple singleton or context manager to collect metrics during the `run_pipeline.py` execution.
*   **Metrics to Capture:**
    *   `count_total_positions`
    *   `count_etfs_processed`
    *   `count_etfs_failed`
    *   `count_api_calls_yfinance`
    *   `count_cache_hits`
*   **Output:** Save to `outputs/pipeline_metrics.json` at the end of the run.

### Step 2: Build the Dashboard (`src/dashboard/app.py`) [Done]
*   **Task:** Initialize a Streamlit app.
*   **Logic:**
    *   Load the CSV, Text, and JSON files.
    *   Handle missing files gracefully (show "No Data - Run Pipeline First").
    *   Use `plotly.express` for interactive charts.

### Step 3: Launch Script [Done]
*   **Task:** Create `run_dashboard.sh` (or add to `run.sh`) to simplify startup: `streamlit run src/dashboard/app.py`.

## 4. Success Criteria
1.  **Visual Proof:** I can see my top 10 holdings in a chart.
2.  **Gap Visibility:** I can clearly see that "Vanguard" is a missing provider without reading a log file.
3.  **Usability:** The dashboard launches with a single command.
