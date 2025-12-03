# Specification: Portfolio Valuation Fix

**Status:** In Progress
**Created:** 2025-12-03
**Reference Date:** 2025-11-24 (Monday closing prices)

## Problem Statement

**User Need:** Accurate portfolio valuation that matches broker (Trade Republic) displayed values.

**Current State:** Portfolio value is 37% lower than reality (€25,855 calculated vs €41,431 ground truth).

**Obstacle:** Multiple interacting issues in price fetching, currency conversion, and ground truth data quality.

## Root Cause Analysis

### Investigation Findings

| Issue | Evidence | Impact |
|-------|----------|--------|
| Wrong prices | IWDA.AS: €110 vs €220 expected | 2x undervaluation |
| Ground truth errors | META: 0.055 qty in GT, actual 0.229 | Validation unreliable |
| Wrong ticker mapping | SXRV.DE was mapped as CSNDX.MI | Wrong price fetched |
| Currency bugs | Some GBP/GBX confusion suspected | Variable undervaluation |

### Ground Truth Corrections Applied

| ISIN | Field | Old Value | New Value | Reason |
|------|-------|-----------|-----------|--------|
| IE00B53SZB19 | Yahoo_Ticker | CSNDX.MI | SXRV.DE | User confirmed TR ticker |
| IE00B53SZB19 | Quantity | 0.614875 | 4.5 | User confirmed |
| IE00B53SZB19 | Value_EUR | 5507.60 | 5760.00 | User confirmed (~€1,280/share) |
| US30303M1027 | Quantity | 0.055023 | 0.229 | User confirmed |
| US30303M1027 | Value_EUR | 109.24 | 127.00 | User confirmed |

## Solution Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    VALIDATION FRAMEWORK                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐     ┌──────────────┐     ┌─────────────────┐  │
│  │ Ground Truth│     │ Historical   │     │ Validation      │  │
│  │ (Nov 24)    │────▶│ Price Fetch  │────▶│ & Comparison    │  │
│  │             │     │              │     │                 │  │
│  └─────────────┘     └──────────────┘     └─────────────────┘  │
│         │                   │                      │            │
│         ▼                   ▼                      ▼            │
│  ┌─────────────┐     ┌──────────────┐     ┌─────────────────┐  │
│  │ Quantity    │     │ Price per    │     │ Discrepancy     │  │
│  │ Verification│     │ Position     │     │ Report          │  │
│  └─────────────┘     └──────────────┘     └─────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Components

### 1. Ground Truth File
**File:** `data/true_data/ground_truth_validated.csv`

- Contains verified portfolio positions as of 2025-11-24
- Includes metadata: Reference_Date, Validated, Notes
- Source of truth for validation during development

### 2. Historical Price Fetcher
**File:** `src/data/historical_prices.py`

- Fetches closing prices for specific historical dates
- Handles currency conversion with full audit trail
- Manages GBp (pence) to GBP conversion
- Returns structured results with traceability

### 3. Validation Framework
**File:** `scripts/validate_portfolio.py`

Usage:
```bash
# Batch validation
python scripts/validate_portfolio.py

# Debug single position
python scripts/validate_portfolio.py --debug IE00B53SZB19

# Override date
python scripts/validate_portfolio.py --date 2025-11-24
```

### 4. Pipeline Integration
**File:** `scripts/run_pipeline.py`

- Optional validation hook (VALIDATE_PORTFOLIO env var)
- Advisory mode: warn but continue
- Logs discrepancies for later investigation

## Parameters

| Parameter | Value | Notes |
|-----------|-------|-------|
| Reference Date | 2025-11-24 | Monday closing prices |
| Value Tolerance | 2% | For pass/fail determination |
| Ground Truth Tolerance | 5-10% | Acceptable due to date differences |
| Pipeline Mode | Advisory | Warn but continue |

## Success Criteria

| Metric | Target |
|--------|--------|
| Positions within 2% tolerance | >90% |
| Portfolio total discrepancy | <5% |
| No NaN/missing prices | 0 |
| All ISINs resolved | 100% |

## Implementation Phases

1. **Documentation & Ground Truth** - Spec doc, validated GT file, ticker map fix
2. **Historical Price Fetcher** - Module for fetching historical prices
3. **Validation Framework** - Script with batch and debug modes
4. **Pipeline Integration** - Add validation hook to pipeline
5. **Initial Validation** - Run and analyze discrepancies
6. **Root Cause Fixes** - Fix issues identified in Phase 5

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| yfinance missing historical data | Fallback to closest available date |
| Ground truth has more errors | Iterative verification with user |
| Currency rates differ from TR | Document and accept small variance |
| Tickers delisted/changed | Manual mapping in ticker_map.json |
