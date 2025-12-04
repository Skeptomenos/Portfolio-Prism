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

### Phase 14: Validation & Data Integrity (2025-11-29)
- **Input Data Limitations**: The Trade Republic "Account Statement" (Kontoauszug) PDF is a Cash Journal, not a Portfolio Statement. It often omits share quantities for "Direct Buy" (Direktkauf) transactions, listing only the Euro amount. **Rule:** Do not assume "Account Statements" contain position data. Use "Securities Account Statement" (Depotauszug) or "Order Confirmations" (Abrechnung) if possible.
- **Validation Authority**: Never allow the production pipeline to "fallback" to reading the validation/ground-truth file when input is missing. This defeats the purpose of validation. **Rule:** Strict separation of Prod I/O and Test I/O.
- **Invariant Validation**: When validating financial pipelines, compare **Quantities** (invariant), not **Market Values** (volatile). Price fluctuations can trigger false positive validation failures.
- **Manual Escape Hatch**: When parsing fails due to source document limitations (missing data), a manual injection file (CSV) is a pragmatic and necessary workaround to unblock the pipeline.

- **Parallel Development Strategy:** When refactoring critical modules, build new code alongside old (`aggregation_v2/`), test equivalence, then atomic switch. Zero downtime, safe rollback.
- **Modular Decomposition:** 350-line monolith → 6 focused modules. Each module <100 lines. Single responsibility = easier testing and debugging.
- **Test Before Delete:** Never delete old code until new code passes ALL existing tests + new unit tests. Integration test comparing old vs new output is critical proof.
- **AggregatedExposure Model:** Using Pydantic model with `get_or_create_record()` pattern simplifies aggregation logic. Records stored as list, accessed via `get_record(isin)` method.
- **Tiered Enrichment:** Only resolve ISINs for holdings >1% weight. Reduces API calls by 80%+ while maintaining 95%+ value coverage. Minor holdings use fallback grouping.

### Phase 15: Dashboard Development (2025-11-30)
- **Streamlit State Management:** Session state (`st.session_state`) enables cross-tab communication (e.g., error "Fix" button → Data Manager). Critical for user flows spanning multiple tabs.
- **Safe Mode Calculation:** Always check `len(series.mode()) > 0` before accessing `[0]`. Empty Series from all-null columns raises KeyError, not handled by `.empty` check.
- **Cached Data Loading:** Use `@st.cache_data` decorator on all file I/O functions. Prevents re-reading CSVs/JSON on every widget interaction. Clear cache after saves: `st.cache_data.clear()`.
- **Plotly over Matplotlib:** For web dashboards, Plotly provides interactivity (zoom, hover, filter) out-of-the-box. Matplotlib static images lack these UX benefits.
- **Incremental Implementation:** Build dashboards tab-by-tab with placeholders for future tabs. Allows iterative deployment and user feedback before full completion.

### Phase 17: Test Isolation & Output Protection (2025-12-03)
- **Test Pollution:** Tests that write to real output paths silently corrupt production data. Tests pass but dashboard shows wrong data. **Rule:** All file outputs in tests must use `tempfile.TemporaryDirectory()` or patch/mock output paths.
- **Centralized Paths:** Hardcoded paths like `"outputs/file.csv"` are non-configurable and fragile. **Rule:** Centralize all output paths in `src/config.py`.
- **Patch Location:** When patching constants, patch where they're **used**, not where they're **defined** (e.g., `@patch("src.core.aggregation.HOLDINGS_BREAKDOWN_PATH")` not `@patch("src.config.HOLDINGS_BREAKDOWN_PATH")`).
- **Incremental Verification:** After any pipeline run, verify key outputs (row counts, sample data) to catch corruption early.

### Phase 18: Portfolio Valuation & Ground Truth Correction (2025-12-03)
- **Ground Truth Data Quality:** User-provided ground truth (GT) may contain systematic errors. The GT "values" were correct but "quantities" were wrong for 12/30 positions (some off by 400%!). **Rule:** Never assume GT is authoritative without validation. Cross-check GT quantities against: `Quantity = Value / (Price × FX_Rate)`.
- **Reverse Engineering Pattern:** When GT values are trusted but quantities are suspect, use the formula `Recalculated_Qty = GT_Value_EUR / Actual_Price_EUR` to reverse-engineer correct quantities. This is especially useful when the original data capture method is unknown.
- **Ticker Mapping Vigilance:** Wrong ticker mappings cause silent, massive errors. Vulcan Energy (`VM3.F` → `VUL.DE`) was fetching €0.10 instead of €3.18, causing 3000% recalculation error. **Rule:** When a recalculated change exceeds 500%, suspect ticker mapping first.
- **Validation-Driven Development:** Build validation scripts BEFORE fixing data. The `validate_portfolio.py` script identified exactly which positions failed, enabling targeted fixes. **Pattern:** Observe → Measure → Fix → Re-measure.
- **Backup Before Overwrite:** The `recalculate_gt.py` script creates timestamped backups before modifying GT files. **Rule:** Any script that modifies source-of-truth files must create backups automatically.
- **Delisted Securities:** Some securities (TKMS, TAAT, Cresco Labs) return no price data from yfinance. These are likely delisted or OTC. **Rule:** Flag these as "MANUAL_REQUIRED" rather than silently setting to zero.

### Phase 19: pytr Deep Integration (2025-12-03)
- **CLI Tool Wrapping:** When integrating external CLI tools (like pytr), subprocess wrapping is often more robust than importing internal modules. CLI contracts are stable; internal APIs change. **Rule:** Prefer `subprocess.run(["tool", "args"])` over `from tool.internal import X` for external dependencies.
- **Credential Storage Patterns:** Store user credentials in `.env` (local, gitignored) with interactive first-run prompts. Include privacy notice and `--reconfigure` flag for updates. **Rule:** Never store credentials in version control; always provide reconfiguration path.
- **Auto-Backup on Overwrite:** Before overwriting user data files, create timestamped backups automatically (e.g., `file.2025-12-03_143022.csv.bak`). Users trust tools that preserve their data.
- **Interactive Menu UX:** For CLI tools with multiple input methods, provide an interactive menu with sensible defaults. "Press Enter for recommended option" reduces friction for new users.
- **Fallback Messaging:** When primary method fails, provide clear error message + explicit fallback instructions. Don't auto-switch (user should decide) but make alternatives obvious.

### Phase 20: CSV Column Collision & pytr Format Fix (2025-12-04)
- **Column Name Collision:** When merging CSVs with `pd.merge()`, duplicate column names create `_x`/`_y` suffixes. Code expecting original column name fails with `KeyError`. **Rule:** Always prefix source-specific columns to avoid collisions (e.g., `TR_Name` instead of `Name`).
- **External Tool Output Formats:** pytr v0.4.2 outputs 5 columns (`Name;ISIN;quantity;avgCost;netValue`), not 6 as previously assumed. The `price` field doesn't exist; `netValue` is calculated internally by pytr. **Rule:** Always verify external tool output format against actual source code, not assumptions or documentation.
- **Derived Values:** When a value isn't directly available, derive it from related fields. `current_price = netValue / quantity`. Document the derivation clearly in code comments.
- **Auto-Grow Universe:** When new ISINs appear in holdings but aren't in the asset universe, auto-add them using available metadata (TR_Name) rather than failing. Mark source as `auto_tr` for auditability. The universe should be the ultimate source of truth and grow automatically.

### Phase 21: Dashboard Analytics Enhancement (2025-12-04)
- **Tab Organization:** Dashboard tab order should reflect user priority: actionable insights first (Performance, X-Ray), exploration second (ETF Overlap, Holdings), maintenance last (Data Manager, Health). Users scan left-to-right.
- **Concentration Metrics:** HHI (sum of squared weights) is a robust, single-number concentration measure. Values >0.15 = concentrated, >0.25 = highly concentrated. Complement with top-N percentages for intuition.
- **Similarity Metrics:** For ETF overlap analysis, Jaccard similarity (intersection/union) works well for binary membership. Alternative: weighted overlap using actual value contributions.
- **Snapshot Strategy:** Daily JSON snapshots enable historical tracking without database complexity. Key: auto-trigger on dashboard load with staleness check (>24h). Store in `data/working/snapshots/` with date-based filenames.
- **Cost Basis from API:** pytr provides `avgCost` per position, enabling P/L calculations without manual tracking. Derive current price from `netValue/quantity` when not directly available.
- **Phased Implementation:** 4-phase dashboard enhancement (Performance → Concentration → Overlap → Snapshots) allowed iterative validation. Each phase testable in isolation before proceeding.