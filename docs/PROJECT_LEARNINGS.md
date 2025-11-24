# Project Learnings (Telegraphic Knowledge Base)

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
- **Import Hell:** `sys.path` hacks brittle -> **Packaging**: `pyproject.toml` + `pip install -e .`.
- **Path Sprawl:** Hardcoded strings (`data/inputs`) -> **Central Config**: `src/config.py`.
- **Refactoring:** Monoliths (Amundi) -> **Split**: `_fetch_manual` (Logic) vs `_fetch_selenium` (IO).

### 3.4. Data Modeling
- **Ghost Assets:** Stale state -> **Clean Slate**: Wipe DB before run. State > Events.
- **ID Conflict:** Ticker (Price) vs ISIN (Holdings) -> **Relational**: `asset_universe` maps ISIN <-> Ticker.
- **Weekend Pricing:** "Delisted" error -> **Escalation**: Try `1d` -> `5d` -> `1mo`.
- **Inflation Bug:** 75% Nvidia -> **Audit**: Divide % by 100. Verify against "Direct Holdings" baseline.
