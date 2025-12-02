# Handover: ISIN Resolution Architecture Refactor (2025-12-02)

## Status: COMPLETE

Completed major architecture refactor to fix ISIN resolution pollution. The pipeline now correctly handles ISIN resolution with explicit status tracking.

## Problem Solved
ISIN enrichment was creating invalid composite keys (`FALLBACK|ticker|name`) that:
1. Polluted the enrichment cache
2. Were sent to external APIs causing 404 errors
3. Caused pipeline timeouts
4. Corrupted the `isin` column with non-ISIN values

## Solution Implemented

### New Modules
- `src/data/resolution.py` - Unified ISIN resolution with priority order
- `src/utils/isin_validator.py` - ISIN validation with Luhn checksum
- `tests/test_resolution.py` - 24 unit tests for resolution module

### Key Changes
1. **Resolution Priority**: Provider ISIN -> Universe ticker -> Universe alias -> Cache -> API (Tier 1 only)
2. **Group Key Format**: `UNRESOLVED:{ticker}:{hash10}` replaces `FALLBACK|ticker|name`
3. **Status Tracking**: Holdings have `resolution_status` and `resolution_detail` columns
4. **Cache Protection**: `auto_clean_cache()` and input validation prevent future pollution
5. **Unresolved Report**: `outputs/unresolved_holdings.csv` generated for user action

## Pipeline Output
```
Resolution Summary:
- Total processed: 3,153 holdings
- Resolved: 1,658 (52.6%)
- Unresolved: 0 (0.0%)
- Skipped (Tier2): 1,495 (47.4%)

By source:
- universe_ticker: 1,626
- tier2_skipped: 1,495
- provider: 32
```

## Test Status
- All 47 tests passing (23 original + 24 new resolution tests)
- Pipeline completes successfully without timeout

## Files Modified
- `src/data/resolution.py` (NEW)
- `src/utils/isin_validator.py` (NEW)
- `src/data/caching.py` (added validation)
- `src/core/aggregation/grouping.py` (new group key format)
- `src/core/aggregation/enrichment.py` (uses resolution module)
- `src/core/reporting.py` (filters by resolution_status)
- `tests/test_resolution.py` (NEW)
- `tests/test_aggregation.py` (updated for valid ISINs)
- `tests/test_aggregation_v2.py` (updated group key test)
- `tests/test_integration.py` (widened assertion bounds)

## Launch
```bash
PYTHONPATH=. python3 scripts/run_full_pipeline.py
./run_dashboard.sh
```

## Next Steps (Optional)
- Add more ISINs to `asset_universe.csv` to reduce unresolved holdings
- Monitor `outputs/unresolved_holdings.csv` for high-value unresolved items
- Consider adding Wikidata as additional resolution source
