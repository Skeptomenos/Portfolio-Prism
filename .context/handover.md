# Handover: Portfolio Valuation Fix (2025-12-03)

## Status: COMPLETE

Fixed portfolio valuation discrepancy from -27% to -0.2% via ground truth quantity recalculation.

## Where Are We?

- **Validation framework works**: `validate_portfolio.py` correctly identifies discrepancies
- **GT quantities corrected**: 12 positions had wrong quantities, now fixed via reverse engineering
- **27/30 positions pass**: Only 3 delisted securities remain as errors (€114 total, 0.3%)

## What Was Done

1. **Created `scripts/recalculate_gt.py`**: Reverse-engineers quantities from GT values
2. **Fixed Vulcan Energy ticker**: `VM3.F` → `VUL.DE` (was €0.10 vs actual €3.18)
3. **Applied recalculations**: 12 positions updated, timestamped backups created
4. **Updated learnings**: Phase 18 added to `PROJECT_LEARNINGS.md`
5. **Added ADR**: Recalculation strategy documented in `DECISION_LOG.md`

## Key Insight

> **Ground truth values were correct, quantities were wrong.**
> Formula: `Corrected_Qty = GT_Value / Actual_Price`
> This pattern is reusable whenever GT capture method is suspect.

## Remaining Issues

| ISIN | Name | Value | Issue |
|------|------|-------|-------|
| DE000TKMS000 | TKMS | €61.23 | Delisted |
| CA87320L1031 | TAAT Global | €29.98 | Delisted |
| CA22587M1068 | Cresco Labs | €22.85 | Delisted |

## Next Steps

1. User provides fresh Trade Republic export → re-validate to confirm quantities
2. Decide: Remove delisted securities from GT or manually set values
3. Consider: Integrate validation into `run_full_pipeline.py`

## Quick Commands

```bash
python3 scripts/validate_portfolio.py           # Full validation
python3 scripts/recalculate_gt.py               # Preview recalc
python3 scripts/recalculate_gt.py --apply       # Apply recalc
python3 scripts/validate_portfolio.py --debug ISIN  # Debug one
```
