# Comprehensive Plan: Pipeline Architecture Fix

**Created:** 2025-11-28
**Status:** Approved, Pending Execution

## Executive Summary

The pipeline is currently reading from **validation data** (`data/true_data/portfolio_holdings.csv`) instead of **calculated data** from the PDF parser. This architectural bug causes a €15,211 (36.71%) discrepancy between calculated and expected values.

---

## Current State (BROKEN)

```
data/true_data/portfolio_holdings.csv (MANUAL/STALE)
        │
        ▼
src/data/state_manager.py (reads wrong file)
        │
        ▼
Pipeline runs with wrong quantities
        │
        ▼
Wrong output (€26,219 instead of €41,431)
```

---

## Target State (CORRECT)

```
data/inputs/portfolio/Account statement.pdf
        │
        ▼ [STEP 1: PDF Parser]
scripts/parse_pdfs_to_csv.py
        │
        ▼ (extracts transactions)
        │
        ▼ [STEP 2: Position Keeper]
src/core/position_keeper.py
        │
        ▼ (calculates: buys - sells = current positions)
        │
        ▼ [OUTPUT: Calculated Holdings]
data/working/calculated_holdings.csv (NEW LOCATION)
        │
        ▼ [STEP 3: State Manager]
src/data/state_manager.py (MUST BE FIXED)
        │
        ▼ [STEP 4: Pipeline]
scripts/run_pipeline.py
        │
        ▼
outputs/direct_holdings_report.csv
outputs/true_exposure_report.csv
        │
        ▼ [STEP 5: Validation]
scripts/validate_pipeline.py
        │
        ▼ (compare against)
data/true_data/portfolio_truth.csv (MANUAL GROUND TRUTH)
```

---

## Implementation Tasks

### Phase 1: Fix Data Flow Architecture

#### TASK-P1-001: Update `state_manager.py` to read from calculated holdings
- **File:** `src/data/state_manager.py`
- **Change:** Line 27 - Change `HOLDINGS_PATH` from `data/true_data/portfolio_holdings.csv` to `data/working/calculated_holdings.csv`
- **Constraint:** Must fail gracefully if file doesn't exist (prompt user to run PDF parser first)

#### TASK-P1-002: Update `parse_pdfs_to_csv.py` output path
- **File:** `scripts/parse_pdfs_to_csv.py`
- **Change:** Line 27 - Change `CSV_PATH` from `data/true_data/portfolio_holdings.csv` to `data/working/calculated_holdings.csv`
- **Rationale:** Calculated data belongs in `data/working/`, not `data/true_data/`

#### TASK-P1-003: Create unified pipeline entry point
- **File:** `scripts/run_full_pipeline.py` (NEW)
- **Purpose:** Single command to run the entire flow:
  1. Parse PDFs → calculated_holdings.csv
  2. Run enrichment pipeline → direct_holdings_report.csv, true_exposure_report.csv
  3. Run validation → compare against ground truth
- **Usage:** `python -m scripts.run_full_pipeline`

### Phase 2: Fix PDF Parser Issues

#### TASK-P2-001: Verify PDF parser extracts all transactions
- **Action:** Run `python -m scripts.parse_pdfs_to_csv --mode dry_run`
- **Expected:** Should find all trades from the account statement
- **Verify:** Compare extracted positions against `portfolio_truth.csv`

#### TASK-P2-002: Fix position calculation for sold positions
- **File:** `src/core/position_keeper.py`
- **Issue:** Rheinmetall appears in output but was sold (should have 0 quantity and be excluded)
- **Verify:** `total_quantity > 0` filter (line 56) should exclude sold positions

#### TASK-P2-003: Handle missing transactions
- **Issue:** Some positions in `portfolio_truth.csv` have different quantities than what parser calculates
- **Action:** Debug the PDF parser to ensure all buy/sell transactions are captured

### Phase 3: Fix Ticker Mapping Issues

#### TASK-P3-001: Fix TKMS ticker
- **File:** `config/asset_universe.csv`
- **Issue:** `DE000TKMS000` has Yahoo ticker `TKMS` which doesn't exist
- **Action:** Research correct Yahoo ticker for ThyssenKrupp Marine Systems

#### TASK-P3-002: Investigate delisted stocks
- **ISINs:** `CA87320L1031` (TAAT Global), `CA22587M1068` (Cresco Labs)
- **Issue:** yfinance returns "possibly delisted"
- **Action:** Confirm if delisted; if so, need manual price entry or mark as delisted

### Phase 4: Documentation & Cleanup

#### TASK-P4-001: Update SYSTEM_FLOW.md
- Document the correct pipeline architecture
- Add data flow diagram

#### TASK-P4-002: Clean up data/true_data/
- Remove `portfolio_holdings.csv` (it's being used incorrectly)
- Keep only validation files: `portfolio_truth.csv`, images

#### TASK-P4-003: Update README with correct usage
- Document the two-step process: parse PDFs → run pipeline
- Document validation workflow

---

## File Changes Summary

| File | Action | Description |
|------|--------|-------------|
| `src/data/state_manager.py` | MODIFY | Change HOLDINGS_PATH to `data/working/calculated_holdings.csv` |
| `scripts/parse_pdfs_to_csv.py` | MODIFY | Change CSV_PATH to `data/working/calculated_holdings.csv` |
| `scripts/run_full_pipeline.py` | CREATE | Unified entry point |
| `config/asset_universe.csv` | MODIFY | Fix TKMS ticker |
| `data/true_data/portfolio_holdings.csv` | DELETE | Remove to prevent misuse |
| `docs/SYSTEM_FLOW.md` | MODIFY | Update architecture docs |

---

## Validation Criteria

After implementation, running `python -m scripts.validate_pipeline` should show:
- Total value within 5% of ground truth (€41,431)
- No MAJOR_DIFF positions (except for price fluctuations)
- 0 MISSING_IN_PIPELINE positions
- Only minor differences due to real-time price changes

---

## Execution Order

1. **TASK-P1-001** and **TASK-P1-002** (can be parallel)
2. **TASK-P2-001** - Verify PDF parser works
3. **TASK-P2-002** and **TASK-P2-003** - Fix any parser issues found
4. **TASK-P3-001** and **TASK-P3-002** - Fix ticker issues
5. **TASK-P1-003** - Create unified entry point
6. **TASK-P4-001**, **TASK-P4-002**, **TASK-P4-003** - Documentation

---

## Notes

- `data/true_data/` is for **validation only** - never used as pipeline input
- `data/working/` is for **calculated/intermediate data**
- `data/inputs/` is for **raw input data** (PDFs, manual holdings)
- `outputs/` is for **final reports**
