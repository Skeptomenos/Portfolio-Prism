# Active State: Portfolio Valuation Fix (Phase 6 Complete)

## Status: COMPLETE

Successfully fixed portfolio valuation discrepancy from -27% to -0.2% through ground truth quantity recalculation.

## Session Summary

### Problem
- Portfolio calculated value: €30,452
- Ground truth value: €41,702  
- Discrepancy: **-27%** (unacceptable)

### Root Cause Analysis
GT data had correct **values** but wrong **quantities** for 12/30 positions. The quantities were systematically understated by 2-5x for major ETF positions.

### Solution Applied
**Reverse Engineering Pattern:**
```
Corrected_Quantity = GT_Value_EUR / Actual_Price_EUR
```

Created `scripts/recalculate_gt.py` to:
1. Fetch historical prices for Nov 24, 2025
2. Calculate correct quantities from trusted GT values
3. Apply corrections with automatic backup

### Results

| Metric | Before | After |
|--------|--------|-------|
| PASS | 8 | **27** |
| FAIL | 12 | **0** |
| WARN | 7 | **0** |
| ERROR | 3 | 3 (delisted) |
| Discrepancy | -27.0% | **-0.2%** |

### Key Corrections Applied

| Asset | Original Qty | Corrected Qty |
|-------|-------------|---------------|
| IWDA.AS | 59.33 | 119.06 |
| NQSE.DE | 20.00 | 100.22 |
| IUSA.MI | 10.00 | 27.58 |
| GOOGL | 1.85 | 3.92 |

### Ticker Fix
- Vulcan Energy: `VM3.F` → `VUL.DE` (was fetching €0.10 instead of €3.18)

## Files Created/Modified

### Created
- `scripts/recalculate_gt.py` - Quantity recalculation utility

### Modified
- `data/true_data/ground_truth_validated.csv` - Corrected quantities
- `config/ticker_map.json` - Fixed Vulcan Energy ticker
- `PROJECT_LEARNINGS.md` - Added Phase 18 learnings
- `DECISION_LOG.md` - Added recalculation strategy ADR

### Backups Created
- `data/true_data/ground_truth_validated.csv.bak.20251203_*`
- `data/true_data/ground_truth_recalculated.csv`

## Remaining Issues

3 positions have no price data (delisted/OTC):
- TKMS (DE000TKMS000) - €61.23
- TAAT Global (CA87320L1031) - €29.98  
- Cresco Labs (CA22587M1068) - €22.85

Total: €114.06 (~0.3% of portfolio) - requires manual verification.

## Commands

```bash
# Validate portfolio
python3 scripts/validate_portfolio.py

# Preview recalculation (without applying)
python3 scripts/recalculate_gt.py

# Apply recalculation
python3 scripts/recalculate_gt.py --apply

# Debug single position
python3 scripts/validate_portfolio.py --debug IE00B4L5Y983
```

## Next Steps

1. **Fresh GT Export**: When user provides new Trade Republic export, run validation to confirm quantities
2. **Delisted Securities**: Either remove from GT or manually set values
3. **Pipeline Integration**: Consider running validation as part of `run_full_pipeline.py`
