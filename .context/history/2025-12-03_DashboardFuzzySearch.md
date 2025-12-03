# Handover: Dashboard Fuzzy Search & Test Isolation (2025-12-03)

## Status: COMPLETE

Completed dashboard UX improvements for Stock Lookup and fixed critical test isolation bug.

## What Was Done

### 1. Dashboard Fuzzy Search Enhancement
- Replaced dropdown with text input (3-char minimum)
- Shows matching securities as expandable cards
- Sort options: Name (A-Z), Total Exposure, Direct %
- First 3 results expanded, rest collapsed
- Maximum 20 results with "refine search" message

### 2. Stock Lookup Duplicate Bug Fix
- **Problem**: Alphabet showed 6 times with different name variants
- **Root Cause**: Dashboard grouped by `name` instead of `ISIN`
- **Fix**: Group by ISIN, use canonical name from `asset_universe.csv`
- Added `get_isin_name_mapping()` helper to `src/dashboard/utils.py`
- Removed duplicate ISIN (`US02079K1079`) from `asset_universe.csv`
- Added duplicate detection warning in `AssetUniverse.load()`

### 3. Test Isolation Fix
- **Problem**: Running `pytest` overwrote `outputs/holdings_breakdown.csv` with test data
- **Root Cause**: Hardcoded path in `run_aggregation()`
- **Fix**: 
  - Added `HOLDINGS_BREAKDOWN_PATH` to `src/config.py`
  - Updated `src/core/aggregation/__init__.py` to use config path
  - Patched both test files to write to temp directories

## Commits
- `003cf75` feat(dashboard): add fuzzy search for stock lookup, fix test isolation

## Test Status
- All 47 tests passing
- Production breakdown file (4376 lines) preserved after test runs

## Files Modified
- `src/config.py` - Added `HOLDINGS_BREAKDOWN_PATH`
- `src/core/aggregation/__init__.py` - Use config path
- `src/dashboard/tabs/holdings_analysis.py` - Fuzzy search rewrite
- `src/dashboard/utils.py` - Added `get_isin_name_mapping()`
- `src/data/resolution.py` - Duplicate ISIN warning
- `config/asset_universe.csv` - Removed duplicate
- `tests/test_aggregation.py` - Temp directory patch
- `tests/test_integration.py` - Temp directory patch

## Launch
```bash
./run_dashboard.sh
pytest  # Safe - won't corrupt production data
```

## Next Steps
- Consider adding more output paths to config (e.g., `TRUE_EXPOSURE_REPORT` already there)
- Backlog item added for CI check on output file protection
