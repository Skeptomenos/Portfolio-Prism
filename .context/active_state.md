# Active State: Docker MVP - Holdings Cache Complete

**Objective:** Docker MVP with 3-tier holdings cache | **Status:** IN PROGRESS | **Date:** 2025-12-04

## Summary

Completed Phase 2 (Holdings Cache System) of Docker MVP. The 3-tier cache provides offline-first resolution for ETF holdings.

## Completed This Session

| Task | Status |
|------|--------|
| Exception consolidation (`ManualUploadRequired`) | ✅ Complete |
| `amundi.py` now imports from `holdings_cache.py` | ✅ Complete |
| All 86 tests pass | ✅ Verified |

## Phase Status

| Phase | Description | Status |
|-------|-------------|--------|
| Phase 1 | Docker Foundation | ✅ Complete |
| Phase 2 | Holdings Cache System | ✅ Complete |
| Phase 3 | Dashboard UX (sync, upload, stats) | ⏳ Next |
| Phase 4 | Build & Deploy | ⏳ Pending |

## Key Files

| File | Purpose |
|------|---------|
| `src/data/holdings_cache.py` | 3-tier cache + `ManualUploadRequired` exception |
| `src/data/holdings_normalizer.py` | Normalize messy CSV/XLSX uploads |
| `src/data/community_sync.py` | GitHub pull/push for community data |
| `src/adapters/amundi.py` | Imports exception from holdings_cache |
| `scripts/run_pipeline.py` | Integrated with cache (Option B) |

## Known Limitations

1. **Vanguard:** Only extracts top 10 holdings (~25% weight)
2. **Amundi Playwright:** Download button selectors broken, manual fallback works
3. **Normalizer:** Substring matching issue in `_map_columns()` (documented, not critical)

## Next Steps

1. **Phase 3:** Dashboard UX - sync button, upload widget, cache stats display
2. **Phase 4:** Docker image to GHCR, friend documentation
