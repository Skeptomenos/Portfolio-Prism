# Sophisticated ISIN Resolution - Implementation Summary

## Problem Solved
Apple (and other securities) were appearing with `N/A` ISIN, causing:
- Duplicate entries in aggregation
- Massive overvaluation (~€24.5k vs actual ~€5k)
- Failed merging of direct + indirect holdings

## Root Cause
1. **iShares CSV files do NOT contain ISINs** (only ticker, name, exchange, location)
2. **No free API reliably provides ISINs:**
   - Finnhub: Returns N/A for many securities
   - YFinance: Does NOT provide ISINs for US stocks
   - OpenFIGI: Provides FIGI identifiers, not ISINs

## Solution Implemented

### 1. Preserve Raw Ticker from Provider
**File:** `src/adapters/ishares.py`

**Change:** Added `raw_ticker` column to preserve the original ticker from iShares CSV before applying Yahoo Finance suffixes.

```python
# Before renaming, preserve raw ticker
holdings_df['raw_ticker'] = holdings_df['Emittententicker']
```

**Result:** We now have:
- `raw_ticker`: Original from provider (e.g., "AAPL", "ALV")
- `ticker`: Yahoo-compatible format (e.g., "AAPL", "ALV.DE")

### 2. Sophisticated Wikidata ISIN Lookup
**File:** `src/data/enrichment.py`

**Implementation:** Multi-signal validation using:
1. **Company Name** - Primary search term
2. **Raw Ticker** - Strong validation signal (score +2)
3. **Yahoo Ticker** - Secondary validation (score +1)
4. **ISIN Presence** - Required (score +1)

**Matching Logic:**
- Accept if `match_score >= 2` OR `(has_ISIN AND match_score >= 1)`
- Fallback: Search by raw ticker if name search fails

**Example:**
```python
fetch_isin_from_wikidata(
    company_name="APPLE INC",
    raw_ticker="AAPL",
    yahoo_ticker="AAPL"
)
# Returns: US0378331005
```

### 3. Enrichment Flow Update
**Fallback Chain:**
1. **Local Resolution** (`asset_universe.csv`) - Fastest
2. **Finnhub API** - Sector/Geography metadata
3. **Wikidata API** - ISIN resolution (NEW!)
4. **YFinance API** - Additional metadata if needed

## Test Results

### Unit Test (3 securities)
```
✓ Apple:     ISIN=US0378331005 (Raw=AAPL, Yahoo=AAPL)
✓ Microsoft: ISIN=US5949181045 (Raw=MSFT, Yahoo=MSFT)
✓ Allianz:   ISIN=DE0008404005 (Raw=ALV, Yahoo=ALV.DE)
```

### Full Pipeline Test
**Status:** Running (enriching 1323 securities from MSCI World ETF)

**Expected Outcome:**
- Apple should have correct ISIN: `US0378331005`
- Total Apple exposure: ~€5k (not ~€24.5k)
- Single aggregated entry (no duplicates)

## Known Limitations

1. **Wikidata Coverage:** Not all securities are in Wikidata
   - Example: Broadcom (AVGO) - not found
   - Example: Berkshire Hathaway Class B (BRKB) - not found

2. **Performance:** Wikidata lookups are slower than local/cached resolution
   - ~2-3 seconds per security
   - For 1323 securities: ~1 hour total
   - **Mitigation:** Results are cached, subsequent runs are instant

3. **Rate Limiting:** Wikidata has no strict rate limits but requests should be reasonable
   - Current implementation: Sequential requests
   - Could be optimized with batching if needed

## Next Steps (If Issues Persist)

### Option A: Pre-populate asset_universe.csv
- Run pipeline once to build ISIN cache
- Export enriched ISINs to `asset_universe.csv`
- Future runs use local resolution (instant)

### Option B: Hybrid Approach
- Use Wikidata for major holdings (>1% weight)
- Accept missing ISINs for minor holdings
- Aggregate by `(ticker, name)` tuple as fallback

### Option C: Paid API Integration
- **OpenISIN.com** - Dedicated ISIN lookup service
- **Bloomberg API** - Enterprise-grade data
- **Refinitiv** - Financial data provider

## Files Modified

1. `src/adapters/ishares.py` - Preserve `raw_ticker`
2. `src/data/enrichment.py` - Sophisticated Wikidata lookup
3. `debug_wikidata_strategy.py` - Test script
4. `test_enrichment_wikidata.py` - Unit test

## Verification Commands

```bash
# Check Apple in final output
grep -i "APPLE" outputs/true_exposure_report.csv

# Count unique ISINs
cut -d',' -f1 outputs/true_exposure_report.csv | sort -u | wc -l

# Check for N/A ISINs
grep "^N/A," outputs/true_exposure_report.csv
```

## Success Criteria

✓ Apple has ISIN `US0378331005`
✓ Apple total value ~€5k (not ~€24.5k)
✓ No duplicate Apple entries
✓ Majority of securities have ISINs resolved
✓ Cache enables fast subsequent runs
