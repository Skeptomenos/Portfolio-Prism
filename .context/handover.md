# Handover: Beta Tester ISIN Fix Complete (2025-12-04)

## Status: COMPLETE (v0.2.2)

Fixed 14 missing ISINs reported by beta tester. Migrated Selenium to Playwright. Created Vanguard adapter.

## What Was Done

### Beta Tester ISIN Fix
1. **13 ETF ISINs Added**: 9 iShares (with product IDs), 2 Xtrackers, 1 Vanguard
2. **2 Assets Added**: Impinj (US7223041028), WisdomTree ETC (IE00BF4TWC33 - marked ignore)
3. **Vanguard Adapter Created**: New `src/adapters/vanguard.py` with Playwright + BeautifulSoup

### Selenium → Playwright Migration
1. **Removed**: `selenium`, `selenium-wire` dependencies
2. **Added**: `playwright` dependency
3. **Created**: `src/utils/browser.py` (shared browser utilities)
4. **Refactored**: `src/adapters/amundi.py` for Playwright
5. **Created**: `scripts/test_adapter.py` for adapter testing

## Known Limitations

| Adapter | Issue | Workaround |
|---------|-------|------------|
| Vanguard | Only gets top 10 holdings (25% weight) | Manual CSV upload |
| Amundi | Playwright selectors broken | Manual XLSX upload (works) |

## Files Changed

| File | Change |
|------|--------|
| `config/adapter_registry.json` | +13 ISINs |
| `config/ishares_config.json` | +9 product IDs |
| `config/asset_universe.csv` | +2 assets |
| `src/adapters/vanguard.py` | Created |
| `src/adapters/amundi.py` | Playwright refactor |
| `src/utils/browser.py` | Created |
| `scripts/test_adapter.py` | Created |
| `pyproject.toml` | -selenium, +playwright |
| `requirements.txt` | -selenium, +playwright |
| `QUICKSTART.md` | Added playwright install step |

## Next Steps

1. **Fix Amundi Selectors**: Debug screenshot at `data/working/raw_downloads/debug_screenshots/amundi_FR0010361683_error.png`
2. **Vanguard Full Holdings**: Investigate API endpoints captured in logs, or implement "View All" button
3. **Beta Tester Retest**: Have friend `git pull` and confirm errors resolved

## Quick Commands

```bash
python scripts/test_adapter.py IE00B4L5Y983   # Test iShares
python scripts/test_adapter.py IE00BK5BQT80   # Test Vanguard
python scripts/test_adapter.py --list         # List all adapters
pytest                                         # 47 tests passing
```
