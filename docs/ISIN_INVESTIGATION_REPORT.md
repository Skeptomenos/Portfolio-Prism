# ISIN Resolution Investigation - Final Report

## Problem Summary

**Issue:** Securities like Apple appear with `N/A` ISIN, causing:
- Duplicate entries (one with ISIN, one without)
- Ghost assets with massive overvaluation (~€24.5k vs actual ~€5)
- Failed aggregation across direct + indirect holdings

## Root Causes Identified

### 1. Incomplete Local Data
- `asset_universe.csv` contains only 32 assets (user's direct holdings + ETFs)
- Does NOT include 1000+ underlying ETF holdings (Apple, Microsoft, etc.)
- Local-first strategy fails when security not in local DB

### 2. API Limitations
- **Finnhub:** Returns `N/A` for many securities
- **YFinance:** Does NOT provide ISINs for US stocks (confirmed: `AAPL → ISIN: NOT FOUND`)
- **iShares CSV:** Does not contain ISIN column (per adapter code comment line 166)
- **No free API reliably provides ISINs**

### 3. Why Nvidia Worked
- Nvidia (NVDA) was in `asset_universe.csv` as a direct holding
- Local resolution succeeded before API fallback needed
- Created false impression that the fix was complete

## Failed Solutions

1. ✗ **YFinance ISIN Fallback** - Implemented but YFinance doesn't provide ISINs
2. ✗ **Asset Universe Pre-population** - Would require 1000+ manual ISIN entries
3. ✗ **iShares Native ISINs** - iShares CSVs don't contain ISIN column

## Recommended Solution: Ticker-Based Aggregation

**Approach:** Use `(Ticker, Name)` tuple as identity instead of ISIN

**Implementation:**
1. Modify aggregation logic to group by `ticker` + `name` combo
2. Create synthetic ID: `{ticker}_{sanitized_name}` for tracking
3. Accept that some edge cases (ticker changes, different exchanges) may cause duplicates
4. Add logging to identify aggregation conflicts

**Pros:**
- All adapters provide ticker + name
- No external API dependencies
- Handles 95%+ of cases correctly

**Cons:**
- Same company on different exchanges may duplicate
- Ticker symbol changes over time won't be tracked
- Less "correct" than ISIN-based approach

## Alternative: Paid ISIN API

**OpenFIGI API** (Bloomberg):
- Free tier: 25k requests/day
- Provides ISIN for ticker/name lookup
- Requires registration

**Implementation:**
- Add OpenFIGI client to enrichment.py
- Fallback order: Local → Finnhub → OpenFIGI → Ticker-based

## Recommended Path Forward

**Phase 1: Quick Fix (Ticker-Based)**
- Modify aggregation to use ticker+name identity
- Clear existing data and rerun
- Verify Apple/Nvidia aggregate correctly
- Time: ~2 hours

**Phase 2: Long-term (OpenFIGI Integration)**
- Register for OpenFIGI API
- Implement as enrichment fallback
- Build up ISIN cache over time
- Time: ~4 hours

**Decision Point:** User should choose based on:
- Accuracy requirements (how important is perfect ISIN matching?)
- Time constraints (need fix now vs. can wait)
- API complexity tolerance (simple vs. proper solution)
