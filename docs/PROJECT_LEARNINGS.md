# Project Learnings (Telegraphic Knowledge Base)

> **CRITICAL:** You must always append learnings, never replace or delete existing learnings.
> **CRITICAL:** See `docs/agent/AI_CODING_DIRECTIVES.md` for Project Constitution (Mandates).

## 1. Applied Principles (Context)
- **Logic/IO Separation:** Logic = Pure Math. IO = Side Effects. Test Logic without IO.
- **Cache-First IO:** APIs slow/flaky. Cache everything (TTL). *See Directive 1.5.2.*
- **Project Structure:** Use `src/` layout. No `sys.path` hacks. Installable package.
- **Automate Setup:** Master script (`setup_environment.sh`) required.
- **Config:** Externalize secrets/keys (`.env`, `.json`). No hardcoding.
- **Rate Limits:** Client-side `time.sleep`. Headers unreliable. *See Directive 1.5.2.*
- **Visual Feedback:** Batch > 5s? Show progress (`.`/`*`). Flush stdout.
- **Mock-First:** Build logic vs Mock IO. Verify "seams" with Integration Tests.
- **Fail-Fast Contracts:** Validate external data at gate. Fixture-based tests.
- **Direct Data:** APIs/Downloads > UI Automation. *See Directive 1.5.1.*
- **3-Strikes Debugging:** Fix fails 2x? Stop. Re-read. Trace. New Hypothesis.
- **Docs as Code:** Update docs (`QUICKSTART`, `CHANGELOG`) with code.
- **Resilience:** `try...except` in loops. Log errors. Continue processing.
- **Internal Contracts:** Modules must validate inputs (defensive programming).

## 2. Development Blueprint
1.  **Plan:** Write `phaseX-plan.md`.
2.  **Interface:** Define `enrich_securities(df)`.
3.  **Mock:** Hardcode fake data.
4.  **Logic:** Build `reporting.py` vs Mock.
5.  **Test (Unit):** Verify logic isolated.
6.  **Test (Integration):** Verify logic + Mock IO.
7.  **Implement:** Swap Mock for Real API.
8.  **Doc:** Update `CHANGELOG.md`.

## 3. Tactical Playbook (Problem -> Solution)

### 3.1. Data Acquisition
- **Amundi Automation:** Selenium crashed/blocked -> **Manual Escape Hatch**: User drops file. Script checks existence.
- **VanEck Modals:** Shadow DOM/Race conditions -> **JS Clicks**: `driver.execute_script("arguments[0].click();")`.
- **Amundi Blobs:** JS-triggered downloads -> **ChromePrefs**: Auto-download to folder + Poll filesystem.
- **Hybrid Sourcing:** Driver crash specific to env -> **Fallback**: Check `data/inputs/manual_holdings/{ISIN}.csv` first.

### 3.2. Parsing & Cleaning
- **PDF Layouts:** Variable positioning -> **Anchors**: Find "UMSATZÜBERSICHT". **Threshold**: `10-15px` line grouping.
- **German Numbers:** `1.234,56` -> **String Replace**: `.replace(".", "").replace(",", ".")`.
- **Excel Headers:** Merged cells/metadata -> **Explicit Index**: `pd.read_excel(header=n)`.
- **NaN Crashes:** Missing tickers -> **Gatekeeping**: Drop rows where `ticker` is NaN before processing.
- **Inconsistent Formats:** % vs Decimal weights -> **Heuristics**: If `sum <= 1.5`, scale by 100. **Header Hunt**: Scan first 30 rows.
- **Strict XML:** Malformed `.xlsx` (Amundi) -> **Calamine**: Use `engine='calamine'` (Rust) as fallback.
- **Ticker Normalization:** `yfinance` strictness -> **Rules**: UK=`RR.L` (remove dot), HK=`0388.HK` (pad 4), Spaces=`-`.

### 3.3. Architecture & Logic
- **Monolith:** `poc.py` unmanageable -> **Pipeline**: `scripts/run_pipeline.py` (Load -> Agg -> Report).
- **Logic/IO Coupling:** Aggregation fetching data -> **Dependency Injection**: Pass data *into* function.
- **Hardcoded Config:** `ADAPTER_REGISTRY` in code -> **JSON**: `config/adapter_registry.json`.
- **Provider Changes:** Broken parsers -> **Contract Tests**: Test against static `tests/fixtures`.
- **Silent Rate Limits:** 13min hang -> **Throttling**: `time.sleep(1.1)` + Print `.`/`*`.
- **Validation Errors:** "Missing" ETF in Look-Through -> **Relativity**: Only validate *Direct Holdings* persistence.
- **Pricing Coverage:** Alpaca (US only) -> **Yahoo (yfinance)**: Global coverage (Xetra, LSE).
- **Slow PDF Parsing:** 10mins -> **Multiprocessing**: Pool per page + **Incremental**: Skip known file hashes (SQLite).
- **Yahoo Tickers:** `NESN` (No) vs `NESN.SW` (Yes) -> **Suffix Logic**: Add exchange suffix based on ISIN/Region.
- **Config Drift:** Manual registry updates -> **CLI**: Interactive `update_registry.py` prompts user.
- **Import Hell:** `sys.path` hacks brittle - **Packaging** (Phase 10): `pyproject.toml` > `requirements.txt`. Enables `pip install -e .` for dev. Eliminates `sys.path` hacks.
- **Config** (Phase 10): Centralize paths in `src/config.py`. Hardcoded strings = refactoring nightmare.
- **Refactoring** (Phase 10): 300-line functions → smaller, testable units. Amundi adapter: monolithic `fetch_holdings` → modular `_fetch_from_manual`, `_fetch_via_selenium`, `_parse_downloaded_file`.

### Phase 11: Technical Debt Resolution (2025-11-25)
- **Dead Code Detection**: Grep imports before deleting modules. `manager.py` imported by 3 files but unused in all.
- **CSV vs DB**: Manual data > automated parsing when incomplete. Screenshots = authoritative, PDFs = incremental.
- **Auto-Sync Pattern**: CLI tools should auto-trigger dependencies. Asset add → ticker_map sync = better UX.
- **Validation First**: Validation mode before destructive operations. `--mode validate` catches issues without changes.
- **Subprocess Python**: Use `sys.executable` not `'python'` for venv compatibility in subprocess calls.
- **Backup Everything**: Always backup before destructive ops. Users trust tools that preserve data.
- **CLI User Confirmation**: Interactive prompts for irreversible actions (delete). `input("Are you sure? (y/N)")` prevents accidents.
- **Telegraphic Efficiency**: Completed 4 phases in 165 min vs 330 min estimate (50% time). Focused implementation > perfect planning.

### Phase 11.5: Troubleshooting & Stability (2025-11-25)
- **Currency Blindness:** `yfinance` returns *local* currency (e.g., HKD for Xiaomi). **Rule:** Always check `ticker.fast_info['currency']` and normalize to Base Currency (EUR) immediately.
- **Numeric Hygiene:** "Ghost" values (35k Nvidia) often stem from string/float mismatches (e.g., "22,50" treated as string). **Rule:** Explicitly coerce columns to numeric (`pd.to_numeric(..., errors='coerce')`) before aggregation.
- **Cache Rot:** Changing parser logic without clearing `data/working/cache` leads to "Zombie Data". **Rule:** If parser logic changes, automated cache invalidation (or versioning) is required.
- **Semantic Naming:** Distinct ISINs with identical Names (S&P 500 Dist vs Acc) cause debug confusion. **Rule:** Enforce distinct names in `asset_universe` for distinct ISINs.
- **API Data Merging:** When enriching data from external APIs (e.g., Finnhub), prioritize locally resolved high-confidence data (like ISINs from `asset_universe.csv`) over potentially missing or incomplete API responses. Avoid blind overwrites.
- **ISIN Resolution Reality:** Free APIs (Finnhub, YFinance) are unreliable for ISIN resolution (YFinance returns "NOT FOUND" for US stocks). **Wikidata** is a surprisingly robust, free alternative for ISIN lookup when combined with multi-signal validation (Name + Ticker).
- **Self-Learning Systems (Harvesting):** Instead of manually maintaining a massive database, build a system that "learns" from its successful resolutions. The "Harvesting" pattern (Cache -> Validated Data -> Permanent Store) turns expensive API calls into one-time costs.

### 3.4. Data Modeling
- **Ghost Assets:** Stale state -> **Clean Slate**: Wipe DB before run. State > Events.
- **ID Conflict:** Ticker (Price) vs ISIN (Holdings) -> **Relational**: `asset_universe` maps ISIN <-> Ticker.
- **Weekend Pricing:** "Delisted" error -> **Escalation**: Try `1d` -> `5d` -> `1mo`.
- **Inflation Bug:** 75% Nvidia -> **Audit**: Divide % by 100. Verify against "Direct Holdings" baseline.

### Phase 12: Spec-Driven Architecture (2025-11-27)
- **Document Drift:** Documentation naturally drifts from code unless structurally enforced. **Solution:** Use a "Bootloader" (`docs/agent/GEMINI.md`) that acts as a pointer to the authoritative Directives (`docs/agent/AI_CODING_DIRECTIVES.md`) rather than duplicating them.
- **State Persistence:** Ephemeral logs are lost. **Solution:** Mandate "Archival Rotation" of the active state file to a history folder at the end of every session.

### Phase 12.5: Lint Compliance & Documentation (2025-11-28)
- **Unicode in F-Strings:** Emojis (✓, ✗, 📊) inside Python f-strings cause syntax errors. **Rule:** Use ASCII alternatives `[OK]`, `[X]`, `[INFO]` for CLI output.
- **Dead Code After Raise:** Code after `raise NotImplementedError()` is unreachable but still parsed. **Rule:** Comment out or delete dead code to avoid F821 undefined name errors.
- **Bare Except Anti-Pattern:** `except:` catches `KeyboardInterrupt` and `SystemExit`. **Rule:** Always use `except Exception:` or specific types like `except (ValueError, TypeError):`.
- **E402 Import Order:** When `sys.path.insert()` is required before imports, E402 is acceptable technical debt. **Note:** 25 remaining E402 errors are intentional for project structure.
- **Linter as Gate:** Running `ruff check .` before commit catches issues early. Integrate into CI/CD.