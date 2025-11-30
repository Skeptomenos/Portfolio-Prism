# Implementation Plan: Dashboard Phase 3 & 4

## Goal
Implement the "Holdings Analysis" (Phase 3) and "Data Manager" (Phase 4) tabs in the Streamlit dashboard.
These features enable deep-dive analysis (ETF drill-down, stock lookup) and operational fixes (adding missing ISINs).

## User Review Required
> [!NOTE]
> This plan involves editing the `asset_universe.csv` configuration file via the UI. A backup mechanism is included.

## Proposed Changes

### 1. Phase 3: Holdings Analysis Tab

#### [NEW] [src/dashboard/tabs/holdings_analysis.py](file:///Users/davidhelmus/Repos/portfolio-master/POC/src/dashboard/tabs/holdings_analysis.py)
- **Functions:**
  - `render()`: Main entry point.
  - `render_etf_explorer(direct_df, breakdown_df)`: "What's inside this ETF?" view.
  - `render_stock_lookup(direct_df, breakdown_df)`: "Where is my Apple exposure?" view.
- **Logic:**
  - Toggle between "Explore ETF" and "Search Stock" modes.
  - **ETF Explorer:** Selectbox for ETFs -> Filter breakdown -> Show stats & table.
  - **Stock Lookup:** Text input (fuzzy search) -> Consolidate Direct + Indirect exposure -> Show summary card & breakdown table.

#### [MODIFY] [src/dashboard/utils.py](file:///Users/davidhelmus/Repos/portfolio-master/POC/src/dashboard/utils.py)
- Add `load_direct_holdings()` -> reads `outputs/direct_holdings_report.csv`.
- Add `load_holdings_breakdown()` -> reads `outputs/holdings_breakdown.csv`.

#### [MODIFY] [src/dashboard/app.py](file:///Users/davidhelmus/Repos/portfolio-master/POC/src/dashboard/app.py)
- Import `holdings_analysis`.
- Wire up `tab2` to call `holdings_analysis.render()`.

### 2. Phase 4: Data Manager Tab

#### [NEW] [src/dashboard/tabs/data_manager.py](file:///Users/davidhelmus/Repos/portfolio-master/POC/src/dashboard/tabs/data_manager.py)
- **Functions:**
  - `render()`: Main entry point.
  - `render_universe_editor()`: `st.data_editor` for `asset_universe.csv`.
  - `save_universe(df)`: Backup & Save logic.
- **Logic:**
  - Load `config/asset_universe.csv`.
  - Check `st.session_state.pending_fix` (from Phase 2) to show a "Fix Hint" alert.
  - Display editable dataframe.
  - **Save Action:**
    1. Create backup: `config/asset_universe.csv.bak.{timestamp}`
    2. Validate (check duplicates).
    3. Save to disk.
    4. Clear `pending_fix` state.

#### [MODIFY] [src/dashboard/utils.py](file:///Users/davidhelmus/Repos/portfolio-master/POC/src/dashboard/utils.py)
- Add `load_asset_universe()` -> reads `config/asset_universe.csv`.

#### [MODIFY] [src/dashboard/app.py](file:///Users/davidhelmus/Repos/portfolio-master/POC/src/dashboard/app.py)
- Import `data_manager`.
- Wire up `tab3` to call `data_manager.render()`.

#### [MODIFY] [src/dashboard/tabs/pipeline_health.py](file:///Users/davidhelmus/Repos/portfolio-master/POC/src/dashboard/tabs/pipeline_health.py)
- Update "Fix" button to switch tabs:
  ```python
  if st.button("Fix"):
      st.session_state.pending_fix = ...
      # No direct tab switch in Streamlit, but we can use a visual cue or rerun
      st.toast("Fix request sent to Data Manager tab!")
  ```

## Verification Plan

### Manual Verification
1. **Launch Dashboard:** `./run_dashboard.sh`
2. **Tab 2 (Holdings Analysis):**
   - **ETF Mode:** Select an ETF (e.g., iShares World). Verify table shows holdings.
   - **Stock Mode:** Search "NVIDIA". Verify it shows Direct + ETF exposure.
3. **Tab 3 (Data Manager):**
   - **Edit:** Add a dummy row (ISIN: `TEST1234`, Name: `Test Asset`).
   - **Save:** Click Save.
   - **Verify File:** Check `config/asset_universe.csv` has the new row.
   - **Verify Backup:** Check `config/` for a `.bak` file.
4. **Integration (Fix Flow):**
   - Go to Tab 4 (Health).
   - Click "Fix" on an error.
   - Go to Tab 3. Verify "💡 Add ISIN for..." message appears.
