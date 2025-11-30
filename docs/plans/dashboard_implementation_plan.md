# Dashboard Implementation Plan (Streamlit)

## 1. Objective

Create a unified, interactive Graphical User Interface (GUI) for the Portfolio Analysis System.

**Core User Goals:**
1. **Visualization:** See direct holdings (ETFs + stocks) and total portfolio exposure.
2. **ETF Drill-Down:** Look into any ETF and see all holdings with their value in portfolio.
3. **Stock Lookup:** Search a stock (e.g., Apple) and see consolidated exposure across all sources.
4. **Data Editing:** Add missing ISINs to fix resolution failures.
5. **Run Statistics:** See ISINs found, ETFs processed, and comprehensive error lists.

---

## 2. Architecture

### Framework
* **Streamlit** (Python-native web app)

### Data Sources
| File | Location | Purpose |
|------|----------|---------|
| `direct_holdings_report.csv` | `outputs/` | Your direct ETF + stock positions |
| `holdings_breakdown.csv` | `outputs/` | Parent-child lineage (ETF → holdings) |
| `true_exposure_report.csv` | `outputs/` | Aggregated exposure per security |
| `pipeline_health.json` | `outputs/` | Run metrics, ETF stats, error list |
| `asset_universe.csv` | `config/` | ISIN mapping (editable) |

### Interaction Model
* **Read:** Dashboard loads CSVs/JSON on startup (cached).
* **Edit:** Dashboard modifies `config/asset_universe.csv` (with mandatory backup).
* **Execute:** Dashboard triggers `scripts/run_pipeline.py` via `subprocess`.

---

## 3. Implementation Phases

### Phase 1: Environment & Verification

**Goal:** Ensure all dependencies and data artifacts exist.

**Tasks:**
- [ ] Add `streamlit`, `plotly` to `requirements.txt` (if not present).
- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Run pipeline and verify outputs exist:
  ```bash
  python -m scripts.run_pipeline
  ls -la outputs/holdings_breakdown.csv
  ls -la outputs/pipeline_health.json
  ```

**Verification Checklist:**
| File | Expected |
|------|----------|
| `outputs/holdings_breakdown.csv` | Contains `parent_isin`, `child_isin`, `value_eur` columns |
| `outputs/pipeline_health.json` | Contains `metrics`, `failures[]`, `etf_stats[]` |
| `outputs/direct_holdings_report.csv` | Contains `isin`, `name`, `asset_type`, `market_value` |

---

### Phase 2: Tab 4 - Pipeline Stats & Errors (Quick Win)

**Goal:** Surface run statistics and make errors actionable.

**Context:** The current prototype reads wrong JSON keys. We fix this and add the error dashboard.

#### 2.1 Run Statistics Panel

**Source:** `pipeline_health.json` → `metrics` object

| Metric | JSON Key | Display Example |
|--------|----------|-----------------|
| Direct Holdings | `metrics.direct_holdings` | "20 positions" |
| ETF Positions | `metrics.etf_positions` | "11 ETFs" |
| ETFs Processed | `metrics.etfs_processed` | "11/11 ✅" |
| Holdings Discovered | `metrics.tier1_holdings` | "110 holdings" |
| ISINs Resolved | `metrics.tier1_resolved` | "110 resolved" |
| Resolution Failures | `metrics.tier1_failed` | "5 failed ⚠️" |
| Last Run | `timestamp` | "2025-11-29 12:30" |

**Implementation:**
```python
if health_data:
    m = health_data.get("metrics", {})
    col1, col2, col3 = st.columns(3)
    col1.metric("ETFs Processed", f"{m.get('etfs_processed', 0)}/{m.get('etf_positions', 0)}")
    col2.metric("ISINs Resolved", m.get("tier1_resolved", 0))
    col3.metric("Resolution Failures", m.get("tier1_failed", 0))
```

#### 2.2 ETF Processing Table

**Source:** `pipeline_health.json` → `etf_stats[]` array

| Column | Description |
|--------|-------------|
| ETF Ticker | ISIN of the ETF |
| Holdings Count | Number of underlying holdings |
| Weight Sum | Should be ~100% |
| Status | "OK" or error |

**Display:** Highlight rows where `status != "OK"` or `weight_sum` deviates from 100%.

#### 2.3 Error Dashboard (NEW)

**Source:** `pipeline_health.json` → `failures[]` array

**Components:**
1. **Error Summary KPIs:**
   - Total Errors: `len(failures)`
   - Group by `stage` (ENRICHMENT, INGESTION, etc.)
   - Group by `severity` (HIGH, MEDIUM, LOW)

2. **Error Table:**
   | Stage | Item | Error | Suggested Fix | Severity | Action |
   |-------|------|-------|---------------|----------|--------|
   | ENRICHMENT | GOOG | ISIN Resolution Failed | Add GOOG to asset_universe.csv | MEDIUM | [Fix] |

3. **"Fix" Button Behavior:**
   - Store `{"ticker": item, "suggested_isin": "", "fix_hint": fix}` in `st.session_state.pending_fix`
   - User clicks → navigates to Tab 3 (Data Manager)
   - Tab 3 checks `session_state.pending_fix` and highlights/scrolls to add new row

---

### Phase 3: Tab 2 - Holdings Analysis (Core Feature)

**Goal:** Enable both forward (ETF → holdings) and reverse (stock → sources) drill-downs.

**Context:** Current prototype only has basic search. We add dual-mode analysis.

#### 3.1 Mode Toggle

```python
mode = st.radio("Analysis Mode", ["🔍 Search Stock", "📦 Explore ETF"], horizontal=True)
```

#### 3.2 ETF Explorer (Forward Drill-Down) - NEW

**Purpose:** Answer "What's inside this ETF?"

**Components:**
1. **ETF Dropdown:**
   - Source: `direct_holdings_report.csv` filtered by `asset_type == 'ETF'`
   - Display: ETF name + ISIN

2. **Holdings Table:**
   - Source: `holdings_breakdown.csv` filtered by `parent_isin == selected_etf`
   - Columns: `child_name`, `weight_percent`, `value_eur`, `child_isin`
   - Sort: By `value_eur` descending

3. **Summary Card:**
   ```
   📦 iShares Core MSCI World ETF (IE00B4L5Y983)
   └── 1,343 holdings | Total Value: €6,609.08
   ```

**Implementation:**
```python
if mode == "📦 Explore ETF":
    etf_options = direct_df[direct_df["asset_type"] == "ETF"][["name", "isin"]]
    selected = st.selectbox("Select ETF", etf_options["name"])
    etf_isin = etf_options[etf_options["name"] == selected]["isin"].iloc[0]

    holdings = breakdown_df[breakdown_df["parent_isin"] == etf_isin]
    st.metric("Holdings Count", len(holdings))
    st.metric("Total Value", f"€{holdings['value_eur'].sum():,.2f}")
    st.dataframe(holdings.sort_values("value_eur", ascending=False))
```

#### 3.3 Stock Lookup (Reverse Drill-Down) - ENHANCED

**Purpose:** Answer "Where does my Apple exposure come from?"

**Components:**
1. **Search Box:**
   - Autocomplete from `holdings_breakdown.csv` unique `child_name` values
   - Fuzzy match supported

2. **Consolidated Summary Card:**
   ```
   🍎 Apple Inc (US0378331005)
   ├── Total Exposure: €500.00
   ├── Direct: €100.00 (20%)
   └── Via ETFs: €400.00 (80%)
   ```

3. **Breakdown Table:**
   | Source | Type | Weight in Source | Your Value |
   |--------|------|------------------|------------|
   | Direct Portfolio | Direct | - | €100.00 |
   | iShares MSCI World | ETF | 2.5% | €250.00 |
   | iShares S&P 500 | ETF | 1.5% | €150.00 |
   | **Total** | | | **€500.00** |

**Data Logic:**
```python
# Combine direct + indirect for searched stock
stock_direct = direct_df[direct_df["name"].str.contains(search, case=False)]
stock_indirect = breakdown_df[breakdown_df["child_name"].str.contains(search, case=False)]

direct_value = stock_direct["market_value"].sum() if not stock_direct.empty else 0
indirect_value = stock_indirect["value_eur"].sum()
total = direct_value + indirect_value
```

---

### Phase 4: Tab 3 - Data Manager (Operations)

**Goal:** Allow safe editing of `asset_universe.csv` to fix missing ISINs.

#### 4.1 Universe Editor

**Component:** `st.data_editor` with editable columns

```python
universe_df = pd.read_csv("config/asset_universe.csv")
edited_df = st.data_editor(
    universe_df,
    num_rows="dynamic",  # Allow adding rows
    column_config={
        "ISIN": st.column_config.TextColumn("ISIN", required=True),
        "Name": st.column_config.TextColumn("Name"),
        "Asset_Class": st.column_config.SelectboxColumn("Type", options=["Stock", "ETF"]),
    }
)
```

#### 4.2 Pending Fix Integration

**When arriving from Tab 4 "Fix" button:**
```python
if "pending_fix" in st.session_state:
    fix = st.session_state.pending_fix
    st.info(f"💡 Add ISIN for: **{fix['ticker']}** — {fix['fix_hint']}")
    # Optionally pre-populate a new row
```

#### 4.3 Safety Mechanism

**Before Save:**
1. **Backup:** Copy to `config/asset_universe.csv.bak.{YYYYMMDD_HHMMSS}`
2. **Validation:**
   - Check for duplicate ISINs
   - Check for empty required fields
   - Warn (don't block) on suspicious data

**Save Button:**
```python
if st.button("💾 Save Changes"):
    # Backup
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.copy("config/asset_universe.csv", f"config/asset_universe.csv.bak.{timestamp}")

    # Validate
    dupes = edited_df[edited_df["ISIN"].duplicated(keep=False)]
    if not dupes.empty:
        st.warning(f"⚠️ Duplicate ISINs found: {dupes['ISIN'].tolist()}")

    # Save
    edited_df.to_csv("config/asset_universe.csv", index=False)
    st.success("✅ Saved! Backup created.")
```

---

### Phase 5: Tab 1 - Portfolio X-Ray (Visualization)

**Goal:** High-level portfolio overview with charts.

**Status:** Prototype exists. Enhance with better data handling.

#### 5.1 KPIs Row
| KPI | Source | Calculation |
|-----|--------|-------------|
| Total Portfolio Value | `direct_holdings_report.csv` | `sum(market_value)` |
| Number of Positions | `direct_holdings_report.csv` | `count(*)` |
| Unique Underlying Assets | `true_exposure_report.csv` | `count(distinct isin)` |

#### 5.2 Charts
1. **Top 10 Holdings Bar Chart** (exists) - keep as-is
2. **Asset Allocation Pie/Treemap** - use `asset_type` grouping for now
3. **Sunburst** (FUTURE) - defer until sector/geography enrichment improves

---

### Phase 6: Tab 4 - Pipeline Control (Execution)

**Goal:** Allow triggering pipeline runs from the dashboard.

#### 6.1 Two-Tier Execution

| Button | Command | Use Case |
|--------|---------|----------|
| 🔄 Refresh Reports | `python -m scripts.run_pipeline --skip-ingestion` | Quick re-aggregation |
| 🚀 Full Pipeline | `python -m scripts.run_pipeline` | Complete run with downloads |

#### 6.2 Execution Feedback

**Options (choose one):**
- **Option A:** `st.spinner` + capture `subprocess.run` output → display in `st.code`
- **Option B:** Stream output via `subprocess.Popen` + `st.empty().write()` updates
- **Option C:** Write to log file, use `st.text_area` with auto-refresh

**Recommended:** Option A for simplicity.

```python
if st.button("🚀 Run Full Pipeline"):
    with st.spinner("Running pipeline..."):
        result = subprocess.run(
            ["python", "-m", "scripts.run_pipeline"],
            capture_output=True, text=True, cwd=PROJECT_ROOT
        )
    if result.returncode == 0:
        st.success("✅ Pipeline completed!")
        st.code(result.stdout[-2000:])  # Last 2000 chars
    else:
        st.error("❌ Pipeline failed!")
        st.code(result.stderr[-2000:])
```

---

### Phase 7: Integration & Polish

**Tasks:**
- [ ] Wire Tab 4 "Fix" button → Tab 3 via `st.session_state`
- [ ] Add "🔄 Reload Data" button to refresh cached data after pipeline run
- [ ] Update `run_dashboard.sh` script
- [ ] Add usage documentation to `README.md`

**run_dashboard.sh:**
```bash
#!/bin/bash
cd "$(dirname "$0")/.."
source venv/bin/activate
streamlit run src/dashboard/app.py --server.port 8501
```

---

## 4. Execution Order (Checklist)

### Week 1: Foundation + Quick Wins
- [ ] Phase 1: Verify environment and data artifacts
- [ ] Phase 2: Implement Tab 4 stats + error dashboard
- [ ] Test: Confirm metrics display correctly from `pipeline_health.json`

### Week 2: Core Features
- [ ] Phase 3.2: Implement ETF Explorer (forward drill-down)
- [ ] Phase 3.3: Enhance Stock Lookup (reverse drill-down with consolidation)
- [ ] Test: "What's in MSCI World?" and "Where's my Apple exposure?"

### Week 3: Operations
- [ ] Phase 4: Implement Data Manager with backup/validation
- [ ] Phase 6: Implement pipeline execution buttons
- [ ] Test: Full "Error → Fix → Save → Run → Verify" loop

### Week 4: Polish
- [ ] Phase 5: Enhance Portfolio X-Ray charts
- [ ] Phase 7: Integration, reload button, documentation
- [ ] Test: End-to-end user journey

---

## 5. Data Schema Reference

### holdings_breakdown.csv
```
parent_isin,parent_name,source,child_isin,child_name,asset_class,sector,geography,weight_percent,value_eur
IE00B4L5Y983,iShares Core MSCI World ETF,ETF,US67066G1040,NVIDIA Corp,Equity,Technology,US,5.68,558.43
DIRECT,Direct Portfolio,Direct,US67066G1040,NVIDIA Corp,Equity,,,0,1391.57
```

### pipeline_health.json
```json
{
  "metrics": {
    "direct_holdings": 20,
    "etf_positions": 11,
    "etfs_processed": 11,
    "tier1_holdings": 110,
    "tier1_resolved": 110,
    "tier1_failed": 5
  },
  "failures": [
    {
      "stage": "ENRICHMENT",
      "item": "GOOG",
      "error": "Tier 1 ISIN Resolution Failed",
      "fix": "Add GOOG to config/asset_universe.csv",
      "severity": "MEDIUM"
    }
  ],
  "etf_stats": [
    {"ticker": "IE00B4L5Y983", "holdings_count": 1343, "weight_sum": 100.04, "status": "OK"}
  ],
  "timestamp": "2025-11-29T12:30:20"
}
```

---

## 6. Success Criteria

| Requirement | Acceptance Test |
|-------------|-----------------|
| Show direct holdings | Tab 1 displays all positions from `direct_holdings_report.csv` |
| ETF drill-down | Select "iShares MSCI World" → see 1,343 holdings with values |
| Stock lookup with consolidation | Search "NVIDIA" → see total from direct + all ETFs |
| Add missing ISINs | Edit `asset_universe.csv` → backup created → save succeeds |
| Run statistics | Tab 4 shows "11 ETFs processed", "5 resolution failures" |
| Comprehensive error list | Tab 4 shows filterable error table with "Fix" buttons |
| Error-to-fix workflow | Click "Fix GOOG" → lands on Tab 3 with hint displayed |
