# Handover: Graceful Enrichment Failure System - COMPLETE

**Date:** 2025-12-05 | **Status:** Complete

## Summary

Implemented a complete graceful degradation system for ISIN resolution failures, including dashboard UI for manual enrichment.

## What Was Done

### New Files Created
| File | Purpose |
|------|---------|
| `src/core/enrichment_gaps.py` | EnrichmentGap dataclass + collector |
| `src/data/manual_enrichments.py` | Load/save user ISIN mappings |
| `config/suggested_isins.json` | 36 pre-populated ISINs (Asian/biotech) |
| `src/dashboard/tabs/missing_data.py` | Dashboard tab with editable form |

### Files Modified
| File | Change |
|------|--------|
| `scripts/run_pipeline.py` | Gap collector integration, TR prices, health check fix |
| `src/data/resolution.py` | Check manual_enrichments first in resolve() |
| `src/core/aggregation/enrichment.py` | Record gaps, pass ETF context |
| `src/core/aggregation/__init__.py` | Calculate ETF portfolio weight |
| `src/dashboard/app.py` | Add "Missing Data" tab |
| `pyproject.toml` | Added pydantic, streamlit, plotly, matplotlib, pytr |

## Architecture

```
Pipeline Run
    │
    └── EnrichmentGapCollector
            ├── Records gaps during ETF enrichment
            └── Saves to outputs/enrichment_gaps.json

Dashboard (Missing Data Tab)
    │
    ├── Shows coverage %, gap count, weight affected
    ├── Pre-fills suggestions from config/suggested_isins.json
    └── Saves to config/manual_enrichments.json

Next Pipeline Run
    │
    └── Resolution checks manual_enrichments.json FIRST
```

## Key Decisions

1. **TR prices only** - Portfolio valuation uses Trade Republic prices, not yfinance
2. **Format-only ISIN validation** - Dashboard checks 12-char format, not database
3. **Manual first** - Resolution checks user mappings before any API calls

## Tests

86 tests passing (1 error is false positive - `scripts/test_adapter.py` is a CLI tool, not a pytest test)

## Next Steps (Future)

1. Add more suggested ISINs as patterns emerge from beta testers
2. Consider auto-detecting common ticker patterns (e.g., `.HK` suffix for HK stocks)
3. Build ISIN lookup helper (query OpenFIGI/Wikidata from dashboard)
