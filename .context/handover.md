# Handover: Documentation & MVP Planning (2025-12-03)

## Status: COMPLETE

Restructured README for Trade Republic users and created MVP migration plan.

## What Was Done

### 1. README Restructure
- **5-Minute Quickstart** now first section (was buried under architecture)
- **Trade Republic PDF workflow** - corrected from wrong CSV instructions
- **API key setup** - Finnhub registration link and .env instructions
- **Dashboard section** - was completely missing
- **Simplified Mermaid diagram** - horizontal flow, PDF as input
- **Troubleshooting** - added PDF-specific issues

### 2. New Documentation
- `.env.example` - API key template with instructions
- `docs/plans/MVP-plan.md` - Comprehensive POC→MVP migration plan

### 3. MVP Plan Key Decisions
- **Input:** Trade Republic PDF only (no CSV alternative)
- **Deployment:** Docker container with baked API keys
- **Selenium:** Will be removed, use pre-cached ETF holdings
- **Target:** Friends & family testing with zero Python setup

## Key Insight

> **The README incorrectly told users to create a CSV file manually.**
> Trade Republic only exports PDFs. The tool parses PDFs automatically
> and generates `calculated_holdings.csv` as an intermediate file.

## Files Changed

| File | Change |
|------|--------|
| `README.md` | Complete restructure for TR workflow |
| `.env.example` | New: API key template |
| `docs/plans/MVP-plan.md` | New: MVP migration plan |
| `.context/active_state.md` | Updated |
| `.context/handover.md` | This file |

## Quick Commands

```bash
# Full pipeline (parse PDF + analyze)
bash run.sh

# Dashboard only
./run_dashboard.sh

# Validate holdings
python3 scripts/validate_portfolio.py
```

## Next Steps

1. **Techy friend test** - Share repo, gather feedback on README
2. **Docker container** - Phase 5 of MVP plan
3. **Pre-cache Amundi** - Remove Selenium dependency

## Open Questions for User

1. Which ETFs do test users own? (need to pre-cache)
2. Any feedback from techy friend on README clarity?
