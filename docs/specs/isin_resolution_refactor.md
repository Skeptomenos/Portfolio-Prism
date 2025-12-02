# ISIN Resolution Architecture Refactor

> **Status:** Approved  
> **Created:** 2025-12-02  
> **Author:** AI Assistant + User

## Problem Statement

The current ISIN enrichment system has a critical flaw: it creates composite fallback keys 
(`FALLBACK|ticker|name`) when ISIN resolution fails, then treats these keys as if they were 
valid identifiers. This causes:

1. **Cache pollution:** Invalid composite keys stored as cache keys
2. **API failures:** Composite keys sent to Finnhub/Wikidata/YFinance causing 404 errors
3. **Pipeline timeouts:** Thousands of failed API calls with rate limiting
4. **Data corruption:** `isin` column contains non-ISIN values

### Root Cause

Two code paths create the issue:
1. `src/core/aggregation/grouping.py:70` - `generate_group_id()` creates `FALLBACK|ticker|name`
2. `src/core/reporting.py:43-47` - Second enrichment pass sends these to APIs

## Solution Overview

### Core Principles

1. **ISIN column is sacred:** Only valid ISINs or NULL, never composite keys
2. **Local-first resolution:** asset_universe.csv → cache → API (in that order)
3. **Explicit status tracking:** Every holding has a `resolution_status`
4. **Auto-grow asset_universe:** Successfully resolved ISINs are saved for future runs
5. **Never send garbage to APIs:** Validate before any external call

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     Resolution Pipeline                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Adapter Output (ticker, name, weight, provider_isin?)         │
│         │                                                       │
│         ▼                                                       │
│  ┌──────────────────┐                                          │
│  │ 1. Provider ISIN │  ← VanEck/Xtrackers provide ISIN         │
│  │    (if valid)    │                                          │
│  └────────┬─────────┘                                          │
│           │ not found                                           │
│           ▼                                                       │
│  ┌──────────────────┐                                          │
│  │ 2. Universe      │  ← asset_universe.csv by ticker          │
│  │    (by ticker)   │                                          │
│  └────────┬─────────┘                                          │
│           │ not found                                           │
│           ▼                                                       │
│  ┌──────────────────┐                                          │
│  │ 3. Universe      │  ← asset_universe.csv by alias           │
│  │    (by alias)    │                                          │
│  └────────┬─────────┘                                          │
│           │ not found                                           │
│           ▼                                                       │
│  ┌──────────────────┐                                          │
│  │ 4. Cache         │  ← enrichment_cache.json (validated)     │
│  │    (validated)   │                                          │
│  └────────┬─────────┘                                          │
│           │ not found                                           │
│           ▼                                                       │
│  ┌──────────────────┐                                          │
│  │ 5. Tier Check    │                                          │
│  │    weight > 1%?  │                                          │
│  └────────┬─────────┘                                          │
│           │                                                     │
│     ┌─────┴─────┐                                              │
│     │           │                                              │
│   Tier 1      Tier 2                                           │
│   (>1%)       (≤1%)                                            │
│     │           │                                              │
│     ▼           ▼                                              │
│  ┌──────────┐  ┌──────────┐                                    │
│  │ 6. API   │  │ Mark as  │                                    │
│  │ Chain    │  │ SKIPPED  │                                    │
│  │ F→W→Y    │  │          │                                    │
│  └────┬─────┘  └────┬─────┘                                    │
│       │             │                                          │
│       ▼             ▼                                          │
│  ┌─────────────────────────────────────┐                       │
│  │ Output:                             │                       │
│  │   isin: valid ISIN or NULL          │                       │
│  │   resolution_status: resolved/      │                       │
│  │                      unresolved/    │                       │
│  │                      skipped        │                       │
│  │   resolution_detail: source info    │                       │
│  │   group_key: ISIN or UNRESOLVED:... │                       │
│  └─────────────────────────────────────┘                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Key Design Decisions

### ADR-001: ISIN Column Semantics

**Decision:** The `isin` column only contains valid ISINs (12-char, checksum-valid) or NULL.

**Rationale:** Prevents downstream pollution; aggregation uses separate `group_key`.

**Consequences:** 
- Need new `group_key` column for aggregation
- Existing outputs with `FALLBACK|` pattern are invalid and need regeneration

### ADR-002: Fuzzy Matching Disabled for Tier 1

**Decision:** Holdings with weight >1% do NOT use fuzzy name matching.

**Rationale:** False positives on major holdings (e.g., CLASS A vs CLASS C) would 
significantly skew portfolio analysis. Better to flag as unresolved for manual review.

**Consequences:**
- More unresolved Tier 1 holdings initially
- Users must manually add entries to asset_universe.csv
- Higher accuracy once resolved

### ADR-003: Auto-Add Resolved ISINs to Universe

**Decision:** All successfully resolved ISINs (from any source) are automatically 
added to asset_universe.csv.

**Rationale:** Builds a valuable, growing database; reduces future API calls.

**Consequences:**
- asset_universe.csv grows over time
- Need deduplication logic
- Need source tracking for auditability

### ADR-004: Hash-Based Fallback Key

**Decision:** Unresolved holdings use `UNRESOLVED:{ticker}:{hash10}` as group_key, 
where hash10 is a 10-digit hash of the normalized name.

**Rationale:** 
- Deterministic: same input → same key (enables cross-ETF aggregation)
- Collision-resistant: 1 in 10,000,000 chance
- Human-readable ticker preserved
- No special characters that caused API pollution

## Data Model Changes

### asset_universe.csv Schema

```csv
ISIN,Yahoo_Ticker,Name,Aliases,Sector,Geography,Source,Added_Date,Last_Verified
US0378331005,AAPL,Apple Inc,"Apple Computer|AAPL US",Technology,US,manual,2025-01-01,2025-12-01
US5949181045,MSFT,Microsoft Corp,,Technology,US,api_finnhub,2025-12-02,2025-12-02
```

| Column | Type | Description |
|--------|------|-------------|
| ISIN | string | Primary key, 12-char validated |
| Yahoo_Ticker | string | Yahoo Finance compatible ticker |
| Name | string | Primary company name |
| Aliases | string | Pipe-separated alternative names |
| Sector | string | Industry sector |
| Geography | string | Country of domicile |
| Source | enum | `manual`, `api_finnhub`, `api_wikidata`, `api_yfinance`, `provider` |
| Added_Date | ISO date | When first added |
| Last_Verified | ISO date | Last API confirmation |

### Holdings DataFrame Schema

| Column | Type | Description |
|--------|------|-------------|
| ticker | string | Yahoo-compatible ticker |
| name | string | Security name from provider |
| weight_percentage | float | Weight in ETF (0-100) |
| isin | string/null | Valid ISIN or NULL |
| resolution_status | enum | `resolved`, `unresolved`, `skipped` |
| resolution_detail | string | Source/failure reason |
| group_key | string | ISIN if resolved, else `UNRESOLVED:{ticker}:{hash}` |
| asset_class | enum | `Equity`, `Cash`, `Derivative` |

### Resolution Status Values

| Status | Meaning | When Used |
|--------|---------|-----------|
| `resolved` | Valid ISIN obtained | Provider, universe, cache, or API success |
| `unresolved` | Could not determine ISIN | All resolution methods failed for Tier 1 |
| `skipped` | Resolution not attempted | Tier 2 holdings (≤1% weight) |

### Resolution Detail Values

| Detail | Source |
|--------|--------|
| `provider` | Adapter provided valid ISIN |
| `universe_ticker` | Matched by ticker in asset_universe.csv |
| `universe_alias` | Matched by alias in asset_universe.csv |
| `cache` | Found in enrichment_cache.json |
| `api_finnhub` | Resolved via Finnhub API |
| `api_wikidata` | Resolved via Wikidata API |
| `api_yfinance` | Resolved via YFinance API |
| `tier2_skipped` | Weight ≤1%, resolution skipped |
| `api_all_failed` | All API attempts failed |

## Output Files

### true_exposure_report.csv

Main aggregated exposure report, now includes resolution_status:

```csv
isin,name,direct,indirect,total_exposure,asset_class,resolution_status,portfolio_percentage
US0378331005,Apple Inc,1000.00,35.00,1035.00,Equity,resolved,4.5
,GLENCORE PLC,0.00,12.34,12.34,Equity,unresolved,0.05
```

Note: Unresolved holdings have empty `isin` (NULL), not FALLBACK pattern.

### unresolved_holdings.csv

Separate actionable list for users, sorted by value:

```csv
group_key,ticker,name,total_exposure,resolution_detail,parent_etfs
UNRESOLVED:GLEN.L:4829173625,GLEN.L,GLENCORE PLC,234.56,api_all_failed,"iShares MSCI World|iShares STOXX 600"
UNRESOLVED:RIO.L:7291836452,RIO.L,RIO TINTO PLC,189.23,api_all_failed,iShares MSCI World
```

## Implementation Phases

1. **Phase 0:** Preparation - spec, backup, cache cleanup
2. **Phase 1:** Data model changes - schema extensions
3. **Phase 2:** Resolution module - core architecture
4. **Phase 3:** Aggregation refactor - integrate resolution
5. **Phase 4:** Cache management - cleanup, validation
6. **Phase 5:** Reporting - output generation
7. **Phase 6:** Testing - unit and integration
8. **Phase 7:** Documentation - changelog, learnings

## Files Changed

### New Files
- `src/data/resolution.py` - Unified resolution module
- `src/utils/isin_validator.py` - ISIN validation with checksum
- `scripts/cleanup_cache.py` - One-time cache cleanup
- `tests/test_resolution.py` - Resolution module tests

### Modified Files
- `src/models/holdings.py` - Add resolution fields
- `src/core/aggregation/grouping.py` - Remove FALLBACK pattern
- `src/core/aggregation/enrichment.py` - Integrate resolution module
- `src/core/reporting.py` - Filter before enrichment
- `src/data/caching.py` - Add validation, auto-clean
- `config/asset_universe.csv` - Extended schema

## Rollback Plan

If issues arise:
1. Restore `config/asset_universe.csv.bak.{date}`
2. Restore `data/working/cache/enrichment_cache.json.bak.{date}`
3. Revert code changes via git

## Success Criteria

1. No `FALLBACK|` pattern in any output file
2. All holdings have valid `resolution_status`
3. `unresolved_holdings.csv` generated with actionable list
4. asset_universe.csv grows with each pipeline run
5. Pipeline completes without API timeout
6. All tests pass
