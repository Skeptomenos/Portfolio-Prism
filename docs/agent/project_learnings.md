# Project Learnings & Mandates

This document is the single source of truth for the architectural principles, development methodologies, and tactical solutions discovered during this project. All developers must adhere to the principles outlined in Section 1.

---

## 1. Core Principles & Mandates (Critical)

These are the foundational rules for the project. They are not optional. They ensure the codebase remains maintainable, robust, and testable.

### 1.1. Architecture & Design
- **Strictly Separate Logic from I/O (Input/Output)**
  - **Why?** Core logic (like the aggregation calculation) should be "pure." It should only perform calculations on data it receives as input and should never make its own database or network calls. This makes the logic incredibly easy to test and reason about.
  - **Mandate:** I/O modules (`data_manager`, `holdings_fetcher`) fetch data. Logic modules (`aggregation`, `reporting`) perform calculations. Never mix the two.

- **Implement a Cache-First I/O Pattern with TTL**
  - **Why?** External API calls are slow, can be costly, and are often rate-limited. During development and testing, repeatedly fetching the same data is inefficient and can halt progress, as seen with the Finnhub API.
  - **Mandate:** All functions that make external API calls MUST be wrapped in a caching layer. This layer must:
    1.  **Use a Time-To-Live (TTL):** Each cached response must be stored with a timestamp. The cache is considered stale and re-fetched if its age exceeds the defined TTL (e.g., 24 hours). This prevents the use of outdated data.
    2.  **Generate a Unique Key:** The cache key must be a deterministic hash of the API endpoint and its specific parameters to ensure the correct response is retrieved.
    3.  **Allow Manual Override:** The caching mechanism must include a `force_refresh` parameter to allow for deliberate re-fetching of data when required.

- **Formalize the Project Structure**
  - **Why?** Ad-hoc `sys.path` modifications are brittle and cause `ModuleNotFoundError` errors.
  - **Mandate:** The project will be treated as a proper, installable Python package. A `setup.py` file or a `src` layout will be used to ensure imports are reliable and follow standard best practices.

- **Automate Environment & Data Setup**
  - **Why?** The project's successful execution depends on an environment (like a populated database) that is not automatically created.
  - **Mandate:** A master setup script (e.g., `scripts/setup_environment.sh`) will be created and maintained. It will be the single command to set up the entire development environment.

- **Externalize Configuration from Code**
  - **Why?** Hardcoding configuration values (like API keys, mappings, or feature flags) directly into the source code makes the application brittle. It requires a code change and redeployment for simple data updates, and it mixes the "what" of the application with the "how."
  - **Mandate:** All configuration that is likely to change between environments or over time MUST be stored in external files (e.g., `.json`, `.yaml`, or `.env` for secrets) and loaded by the application at runtime.

- **Respect External Rate Limits via Client-Side Throttling**
  - **Why?** Relying on API response headers to handle rate limits is reactive and often too late. Aggressive looping (as seen with Finnhub) triggers `429 Too Many Requests` errors immediately, causing data gaps or crashes.
  - **Mandate:** For any batch process involving an external API with known limits (e.g., 60 calls/min), explicit `time.sleep()` calls MUST be implemented within the loop to enforce a safe request pace (e.g., 1.1s delay). Do not rely on the network to be slow enough.

### 1.2. Development Methodology
- **Provide Immediate Visual Feedback for Batch Operations**
  - **Why?** A CLI tool that produces no output for minutes is indistinguishable from a crashed process. The user noted "no output for 13 minutes" during a long enrichment run, causing uncertainty.
  - **Mandate:** Any loop expected to take longer than 5 seconds MUST provide visual feedback.
    1.  **Granular Feedback:** Print a character (e.g., `.`, `*`) or update a progress bar for *every single item* processed.
    2.  **Flush Stdout:** Ensure the output buffer is flushed (`flush=True`) so the feedback appears in real-time, not in delayed chunks.

- **Isolate Logic with Mock Data First**
  - **Why?** Building and testing complex logic is much faster and more reliable when decoupled from live data sources.
  - **Mandate:** For any new core logic module, the first version must be developed against a mock I/O interface. A unit test that validates the logic in isolation is required before any integration with live data pipelines.

- **Adopt a Two-Tiered Testing Strategy**
  - **Why?** Unit tests alone do not prevent integration bugs. Our biggest challenges were in the "seams" where modules connect.
  - **Mandate:** We will use a two-tiered testing strategy:
    1.  **Unit Tests:** Use mocks (`unittest.mock.patch`) to validate "pure" logic modules in complete isolation.
    2.  **Integration Tests:** Write small, focused tests to verify the data handoffs and contracts between real components (e.g., does the reporting module correctly process the DataFrame from the *real* enrichment module?).

- **Validate External Data Contracts at the Boundary**
  - **Why?** External data sources (APIs, websites, file downloads) are brittle and can change their format without warning. If this bad data is allowed into the system, it can cause confusing failures far downstream from the original source. This is a "fail-late" strategy.
  - **Mandate:** For any module that fetches and parses data from an external source, a "contract test" must be implemented. This test validates the parsing logic against a static, saved copy (a "fixture") of the real data. It must assert that the resulting data structure (e.g., a DataFrame) strictly adheres to the expected contract (e.g., correct columns, data types, etc.). This enforces a "fail-fast" strategy.

- **Always Prefer Direct Data Sources Over UI Automation**
  - **Why?** UI automation is extremely brittle, slow, and should be the absolute last resort. The multi-day effort to build a Selenium scraper for VanEck was rendered obsolete by a single direct download link.
  - **Mandate:** Before writing any web scraper, a thorough investigation for APIs, direct download links (XLS, CSV), or data hidden in JSON within the page source must be conducted.

- **Adopt the 'Three-Strikes' Rule for Debugging**
  - **Why?** Repeatedly attempting the same type of fix for a seemingly simple bug (like the `NameError` loop) indicates a flawed understanding of the problem. This "trial-and-error" approach is inefficient and frustrating.
  - **Mandate:** If a simple fix fails more than once (a "strike"), do not attempt a third fix. Instead, halt and re-diagnose. This requires:
    1.  **Expanding Context:** Re-reading the entire function or module to re-establish the full execution context.
    2.  **Tracing Data Flow:** Manually tracing the relevant variables from their creation to the point of failure to confirm their state and scope.
    3.  **Formulating a New Hypothesis:** Only after re-grounding your understanding should a new, different fix be attempted.

- **Treat Documentation as Code**
  - **Why?** Stale or incorrect documentation is actively harmful. It causes confusion, wastes time, and leads to errors (e.g., the conflicting `QUICKSTART.md` files).
  - **Mandate:** Documentation that describes the project's setup, architecture, or core workflows (`QUICKSTART.md`, `CHANGELOG.md`, plans) must be updated within the same work cycle as the code it describes. It is not an afterthought.

- **Build Resilient Pipelines**
  - **Why?** Prototypes can crash on a single error. Production-grade systems must be robust to partial failures and provide clear, structured output for monitoring and debugging.
  - **Mandate:**
    1.  **Isolate Failure:** In any loop processing a batch of items (especially those involving I/O), the work for each single item MUST be wrapped in a `try...except` block. Log the specific error, but allow the loop to continue to the next item.
    2.  **Log with Intent:** All `print()` statements MUST be replaced with a centralized, structured logger that uses appropriate levels (`info`, `warning`, `error`). This provides clarity and allows for effective filtering.

- **Enforce Internal Data Contracts**
  - **Why?** A bug or data quality issue in one module (e.g., an adapter producing `NaN` values) can cause a crash in a completely different, downstream module that receives the bad data. This makes debugging difficult and violates the principle of modularity.
  - **Mandate:** Each module or pipeline stage MUST defensively validate the data it receives from other parts of the application, especially data read from intermediate files (like CSVs). Do not assume upstream components are bug-free. Each module is a gatekeeper responsible for its own inputs.

---

## 2. The Project's Development Blueprint

This is the proven, repeatable workflow for developing new features in this project. It is the practical application of our core principles.

1.  **Plan:** Create a formal plan document (e.g., `phaseX-plan.md`) that explicitly states how the work will adhere to the project's core principles.
2.  **Define the I/O Interface:** In the I/O module (e.g., `enrichment.py`), define the function signature that will fetch the external data (e.g., `enrich_securities(df)`).
3.  **Create a Mock Implementation:** Implement the I/O function with a hardcoded, realistic set of fake data.
4.  **Build the Logic Module:** Build the core calculation module (e.g., `reporting.py`) against the mocked I/O interface.
5.  **Write a Mocked Unit Test:** Create a unit test that uses `@patch` to mock the I/O function and validates the core logic is correct in complete isolation.
6.  **Write an Integration Test:** Create a second test that calls the logic module with the *real* (mocked) I/O module to verify the "seams" between them.
7.  **Build the Real I/O Implementation:** Only after the logic is proven correct, replace the mock I/O with the real implementation (e.g., an API call). The existing tests should continue to pass.
8.  **Update Documentation:** Update `QUICKSTART.md` and `CHANGELOG.md` to reflect the new feature or changes.

---

## 3. Tactical Playbook & Case Studies

This section is a reference library of solutions to specific technical challenges we have already solved.

### 3.1. Data Acquisition
- **Case Study: The Amundi 'Manual Escape Hatch' (Phase 5)**
  - **Problem:** Full automation for the Amundi ETF was blocked by two intractable issues: a Selenium import paradox that crashed the driver and an unparsable, malformed `.xlsx` file.
  - **Solution:** Instead of pursuing a brittle automated solution, a pragmatic semi-manual workflow was created. A dedicated helper script (`tools/acquire_amundi.py`) guides the user through the interactive download and file conversion. The main pipeline was modified to check if the data exists and, if not, halt and direct the user to the helper script.
  - **Principle:** This pattern, the "Manual Escape Hatch," is now the official solution for data providers that resist full automation. It prioritizes reliability and a good user experience over the dogmatic pursuit of 100% automation.

- **Case Study: Bypassing the VanEck Website Modals (Phase 1)**
  - **Problem:** The VanEck holdings page was protected by a Shadow DOM cookie banner and a subsequent investor modal.
  - **Solution (Shadow DOM):** Use `driver.execute_script` to pierce the shadow boundary, as standard Selenium selectors cannot access these elements.
      - **Solution (Race Conditions):** Use a JavaScript-based click (`driver.execute_script("arguments[0].click();", ...)` for elements that are slow to become interactive after animations.
  
  - **Case Study: Amundi Blob Downloads (JavaScript-Driven) (Phase 6)**
    - **Problem:** Some Amundi downloads are triggered by client-side JavaScript (blobs) and cannot be intercepted as standard network requests or wget calls.
    - **Solution:** The only reliable method is to configure the WebDriver to auto-download files to a specific directory (via ChromePrefs) and then poll the filesystem to verify the file's existence. See `src/adapters/amundi.py` for the implementation.
  
  ### 3.2. Data Parsing & Cleaning
  - **Case Study: Trade Republic PDF Heuristics (Phase 6)**
    - **Problem:** Parsing German Trade Republic PDFs is fragile due to layout variations.
    - **Tactics:**
      1.  **Anchor Text:** Verify the presence of "UMSATZÜBERSICHT" on the first page to establish the coordinate system.
      2.  **Line Grouping:** Use a vertical threshold of `10-15px` (pixels) when grouping words into rows. Too small splits lines; too large merges them.
      3.  **German Number Formatting:** Explicitly handle the German decimal format: `.replace(".", "").replace(",", ".")` converts "1.234,56" to "1234.56".
  
  - **Case Study: Parsing Unreliable Excel Headers with Pandas (Phase 1)**  - **Problem:** `pd.read_excel` failed to identify the correct header row due to merged cells and metadata.
  - **Solution:** Specify the header row directly and explicitly using the `header=n` argument (where `n` is the 0-indexed row number).
  - **Troubleshooting Tip:** When getting a `KeyError` on a column, the first step is always to print `df.columns.tolist()` to see the exact names pandas has parsed.

  - **Case Study: The Downstream `NaN` Bug (Phase 5)**
  - **Problem:** The application crashed with an `AttributeError: 'float' object has no attribute 'encode'` in the caching module during the enrichment step. The root cause was not the cache, but `NaN` (float) values for security identifiers being passed to it. This was caused by missing tickers in the raw iShares data.
  - **Solution:** A defensive data cleaning step was added to both the `aggregation` and `reporting` modules. Before processing, they now explicitly drop rows where the key identifier (`ticker` or `isin`) is null.
  - **Principle Reinforced:** This validates the "Enforce Internal Data Contracts" mandate. The location of a crash is often a symptom, not the cause. Each module must act as a gatekeeper and sanitize its own inputs, especially when those inputs come from other modules or intermediate files.

- **Case Study: Heuristic Normalization of Inconsistent Data Formats (Phase 5)**
  - **Problem:** Files from the same provider (Amundi) exhibited inconsistent formatting: one file used percentage weights (Sum ≈ 100) while another used decimal weights (Sum ≈ 1), leading to a massive 99% value drop for the latter. Additionally, header rows appeared at different indices.
  - **Solution:** Instead of hardcoding rules per ISIN, a heuristic "Auto-Scale" logic was implemented. The adapter calculates the column sum; if `sum <= 1.5`, it infers decimal format and scales by 100. Similarly, a "Header Hunting" loop was added to scan the first 30 rows for key terms ("ISIN", "Name") to dynamically locate the header.
  - **Principle:** **Trust Data Properties, Not Metadata.** Do not assume consistency even from a single source. Use intrinsic data properties (sums, keywords, shapes) to dynamically determine how to parse and normalize input, making the system robust to upstream format changes.

### 3.3. Development & Testing- **Success Story: Maturation from POC Script to Orchestrated Pipeline (Phase 5)**
  - **Success Story:** The project successfully evolved from a single, monolithic `poc.py` script to a clean, orchestrated pipeline run by `main.py`. This new structure formalizes the data flow (load -> aggregate -> report -> validate), improves maintainability, and makes the system far easier to reason about and extend.
  - **Principle:** This transition validates the "Formalize the Project Structure" and "Automate Environment & Data Setup" mandates, proving their value in creating a robust and scalable project.

- **Case Study: Successful Decoupling of Logic and I/O (Phase 4)**
  - **Success Story:** The `reporting.py` and `enrichment.py` modules were developed using the blueprint. `reporting.py` (pure logic) was built against a mocked version of `enrichment.py` (I/O). This resulted in zero integration bugs and a fast, predictable development cycle.
  - **Python Detail (`defaultdict`):** For aggregation tasks, using `collections.defaultdict` can simplify the code for creating or updating dictionary entries, avoiding the need for conditional `if key in dict` checks. This was used effectively in Phase 2.

- **Case Study: Fixing the Critical Aggregation Bug (Phase 5)**
  - **Problem:** A critical bug was causing indirect holdings to be calculated incorrectly. The root cause was twofold: 1) The `run_aggregation` function was fetching its own data instead of receiving it as a parameter, violating the separation of I/O and logic. 2) This made the function difficult to test, and the unit tests were using inaccurate mocks (e.g., wrong data types), which masked the underlying issue.
  - **Solution:** The `run_aggregation` function was refactored to accept a pre-fetched dictionary of ETF holdings (`etf_holdings_map`), making it a "pure" calculation function. This is a form of Dependency Injection. The test suite was then updated to pass this map directly, which immediately and clearly revealed the calculation flaw.
  - **Principle Reinforced:** This experience is a powerful, real-world validation of the "Strictly Separate Logic from I/O" mandate. It proves that even a small violation of this principle can lead to critical, hard-to-diagnose bugs. It also adds a new tactical lesson: **a test's mock data must be an exact contract of the real data**, otherwise the test is not reliable.

- **Success Story: Externalizing the Adapter Registry (Phase 5)**
  - **Success Story:** The project successfully refactored the hardcoded `ADAPTER_REGISTRY` dictionary into an external `config/adapter_registry.json` file. The `holdings_fetcher` now loads this file at runtime to map ISINs to the correct adapter.
  - **Principle:** This transition validates the "Externalize Configuration from Code" mandate. It makes the system significantly more maintainable, as new ETFs can be added or modified without changing any Python code, reducing risk and lowering the barrier for updates.

- **Success Story: Implementing Adapter Contract Tests (Phase 5)**
  - **Success Story:** The project successfully implemented contract tests for the VanEck and iShares adapters. This involved creating a `tests/fixtures` directory to store static, local copies of the provider's data files. The new tests in `tests/test_adapters.py` now mock the download step and run the parsing logic against this stable, predictable data.
  - **Principle:** This is the practical application of the "Validate External Data Contracts at the Boundary" mandate. These tests act as a critical defense layer, ensuring that if a provider changes their file format, the corresponding adapter test will fail immediately, protecting the rest of the pipeline from being corrupted by unexpected data.

- **Success Story: Implementing Logging and Graceful Degradation (Phase 5)**
  - **Success Story:** The project successfully replaced all `print()` statements with a centralized logger. Furthermore, the main pipeline in `main.py` was refactored to wrap the `fetch_etf_holdings` call in a `try...except` block, allowing it to continue processing even if one adapter fails.
    - **Principle:** This work validates the "Build Resilient Pipelines" mandate. The structured logs now provide clear, filterable operational data, and the graceful degradation ensures that a single point of failure does not bring down the entire system.
  
  - **Case Study: The 'Silent Failure' of Rate Limiting (Phase 5)**
    - **Problem:** The enrichment pipeline appeared to hang for 13 minutes with no output, while internally it was hammering the Finnhub API and receiving `429` errors for every request. The loop was too fast for the 60 req/min free tier.
    - **Solution:** Two changes were made:
      1.  **Throttling:** A `time.sleep(1.1)` was added to the loop to forcefully restrict the speed to ~55 calls/minute.
      2.  **Feedback:** A `print(..., end="", flush=True)` statement was added to output a dot `.` for cache hits and a star `*` for API hits.
    - **Result:** The process execution time remained similar, but the user could verify progress in real-time, and the API errors dropped to zero.
    - **Principle Reinforced:** This validates the "Respect External Rate Limits" and "Provide Immediate Visual Feedback" mandates.

- **Case Study: Hybrid Data Sourcing (The 'Escape Hatch' Pattern) (Phase 5)**
  - **Problem:** The Amundi adapter was blocked by a Selenium driver crash, and debugging environment-specific driver versions is a low-ROI activity.
  - **Solution:** A "Hybrid" approach was adopted. The adapter was modified to first check for a local file (e.g., `data/inputs/manual_holdings/{ISIN}.csv`) before attempting to use the web driver.
  - **Principle:** For brittle data sources, always implement a file-based fallback. This prioritizes system robustness and allows the user to bypass automation failures manually.

- **Case Study: Validation Relativity in Look-Through Analysis (Phase 5)**
  - **Problem:** The "Completeness Check" validation was failing because it expected the input ETF ISINs to be present in the final report.
  - **Insight:** In a "look-through" analysis, the input container (ETF) is *supposed* to be replaced by its contents (stocks). Therefore, the validation logic was flawed.
  - **Solution:** The check was updated to only verify the persistence of **Direct Holdings** (Stock assets), acknowledging that ETF assets are intentionally decomposed.
  - **Principle:** Validation logic must be domain-aware. A "missing" input is not always an error if the transformation logic intends to replace it.

- **Strategy: Global vs. Regional Pricing APIs (Phase 5)**
  - **Problem:** The project initially considered the Alpaca API for price fetching, but discovered it only supports US markets, leaving European UCITS ETFs unpriced.
  - **Solution:** The team switched to `yfinance` (Yahoo Finance) because it supports global exchanges (Xetra, Euronext, LSE).
  - **Principle:** API selection must prioritize coverage over "official" status when dealing with multi-regional portfolios. We explicitly documented this decision in `knowledge/research/price_source_evaluation.md` to prevent regression.
  