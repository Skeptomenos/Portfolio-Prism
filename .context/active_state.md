# Active State: Vanguard US API Integration - COMPLETE

**Objective:** Full Vanguard holdings via US API | **Status:** COMPLETE | **Date:** 2025-12-04

## Summary

Implemented Vanguard US API integration to fetch complete ETF holdings with ISINs. European Vanguard ETFs now get full holdings data by mapping to their US equivalents.

## Completed This Session

| Task | Status |
|------|--------|
| Discovered Vanguard US API endpoint | ✅ Complete |
| Added VANGUARD_US_EQUIVALENTS mapping | ✅ Complete |
| Implemented `_fetch_via_us_api()` with pagination | ✅ Complete |
| Fixed pagination params (start/count vs offset/limit) | ✅ Complete |
| All 86 tests pass | ✅ Verified |

## API Details

**Endpoint:**
```
https://investor.vanguard.com/investment-products/etfs/profile/api/{FUND_ID}/portfolio-holding/stock
```

**Parameters:**
- `start`: 1-based start index
- `count`: Number of records (max 500)
- `sortColumn`: `percentWeight`
- `sortOrder`: `desc`

**Response fields:**
- `size`: Total holdings count
- `fund.entity[]`: Holdings array with ticker, isin, weight, etc.

## ISIN Mappings Added

| European ISIN | US Ticker | US Fund ID | Index |
|---------------|-----------|------------|-------|
| IE00BK5BQT80 (VWCE) | VT | 3141 | FTSE All-World |
| IE00B3RBWM25 (VWRL) | VT | 3141 | FTSE All-World |
| IE00BKX55T58 (VEVE) | VXUS | 3369 | FTSE Developed ex-US |

## Test Results (VWCE / IE00BK5BQT80)

- **Holdings fetched:** 9,936 (via 20 API calls)
- **Unique holdings:** 2,059 (after filtering)
- **Total weight:** 91.78% (stocks only - bonds/cash in other endpoints)
- **ISINs present:** 2,058/2,059
- **Tickers present:** 2,001/2,059

## Strategy Order

1. Manual file (CSV/XLSX in `data/inputs/manual_holdings/`)
2. **US Vanguard API** (complete holdings with ISINs) ← NEW
3. Playwright (German site fallback)
4. BeautifulSoup (top 10 only, last resort)

## Files Changed

| File | Change |
|------|--------|
| `src/adapters/vanguard.py` | Added US API integration with pagination |

## Next Steps (Future)

1. Add more ISIN mappings for other Vanguard ETFs (VUAA, VUSA, etc.)
2. Consider fetching bonds endpoint for fixed income ETFs
3. Beta tester feedback integration
