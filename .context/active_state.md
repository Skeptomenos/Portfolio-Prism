# Active State: Pipeline Fixed - NVIDIA Now Visible

## Status: COMPLETE

Fixed column name collision that was breaking the pipeline and preventing NVIDIA from appearing.

## Session Summary

### Issues Fixed

1. **pytr 5-column format** - Parser was expecting 6 columns, pytr outputs 5
2. **Column name collision** - Both holdings CSV and universe CSV had `Name` column
3. **Pipeline crash** - Merge created `Name_x`/`Name_y`, code looked for `Name`

### Changes Made

| File | Change |
|------|--------|
| `scripts/fetch_tr_api.py` | Renamed `Name` → `TR_Name` in CSV output |
| `src/data/state_manager.py` | Added `_auto_add_to_universe()` function |
| `data/working/calculated_holdings.csv` | Updated header to use `TR_Name` |
| `docs/plans/tr-api-refactor-plan.md` | Created comprehensive future refactor plan |
| `docs/BACKLOG.md` | Added TR API refactor task |

### Verification

**NVIDIA now correctly appears as #1 holding:**
```
ISIN: US67066G1040
Direct: €1,595.33
Indirect (via ETFs): €3,595.12
Total Exposure: €5,190.45 (12.4% of portfolio)
```

**Pipeline output:**
- 19 Stocks loaded
- 10 ETFs loaded
- 1,792 exposures calculated
- All validation checks passed

## Auto-Add to Universe

New feature: Unmapped ISINs are now automatically added to `asset_universe.csv` using:
- `TR_Name` as the security name
- Heuristic asset class detection (ETF vs Stock)
- Source marked as `auto_tr`

## Tests

All 47 tests pass.

## Next Steps

1. Run dashboard to verify visual display: `./run_dashboard.sh`
2. Consider Phase 2: Performance Dashboard Tab (P/L display)

## Files Changed This Session

```
scripts/fetch_tr_api.py          # TR_Name column, 5-col parsing
src/data/state_manager.py        # Auto-add to universe
docs/plans/tr-api-refactor-plan.md   # Future refactor plan
docs/BACKLOG.md                  # Added backlog item
```
