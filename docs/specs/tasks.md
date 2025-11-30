# Implementation Plan (The "When")

## Phase 1: Spec-Driven Migration & Verification (Completed)
- [x] **TASK-001:** Scaffold Specification Documents (`docs/specs/`).
    - **Context/Constraints:** Align with `AI_CODING_DIRECTIVES.md`.
    - **Status:** Completed 2025-11-27.

- [x] **TASK-002:** Install Ruff Linter and Fix Lint Errors.
    - **Context/Constraints:** 173 ruff errors detected. Fixed 148 (85% reduction).
    - **Status:** Completed 2025-11-28. Remaining 25 E402 are intentional.

- [x] **TASK-003:** Document Pipeline Architecture in README.
    - **Context/Constraints:** Added comprehensive Mermaid flow diagram and stage explanations.
    - **Status:** Completed 2025-11-28.

- [x] **TASK-004:** Migrate Legacy DB to CSV.
    - **Context/Constraints:** See `Phase 1.5` plan. Use `scripts/migrate_db_to_csv.py`.
    - **Status:** Completed 2025-11-28. Merged 21 DB positions with 31 CSV positions.

- [x] **TASK-007:** Fix Remaining Test Failure.
    - **Context/Constraints:** `test_validation_failure_negative_weight` fails in `tests/test_validation.py`.
    - **Status:** Completed 2025-11-28. Added `ge=0.0` constraint to `HoldingsSchema.weight_percentage`.

- [x] **TASK-009:** Fix API Test Script Pytest Errors.
    - **Context/Constraints:** `scripts/test_isin_apis.py` functions collected as tests but not pytest-compatible.
    - **Status:** Completed 2025-11-28. Renamed `test_*` to `_check_*` to avoid pytest collection.

## Phase 1.5: Pipeline Architecture Fix (Critical Data Flow)

> **Plan Reference:** `docs/plans/pipeline_architecture_fix.md`
> **Status:** ✅ Completed via TASK-015 (2025-11-29)

### Phase 1: Fix Data Flow Architecture
- [x] **TASK-P1-001:** Update `state_manager.py` to read from calculated holdings.
    - **Change:** Point `HOLDINGS_PATH` to `data/working/calculated_holdings.csv`.
    - **Status:** Completed as part of TASK-015a.
- [x] **TASK-P1-002:** Update `parse_pdfs_to_csv.py` output path.
    - **Change:** Output to `data/working/calculated_holdings.csv`.
    - **Status:** Completed as part of TASK-015.
- [x] **TASK-P1-003:** Create unified pipeline entry point (`scripts/run_full_pipeline.py`).
    - **Status:** Completed as part of TASK-015e.

### Phase 2: Fix PDF Parser & Position Logic
- [x] **TASK-P2-001:** Verify PDF parser extracts all transactions (dry run).
    - **Status:** Completed. Parser works; missing data is source limitation (not parser bug).
- [x] **TASK-P2-002:** Fix position calculation for sold positions (exclude 0 qty).
    - **Status:** Completed as part of TASK-015.
- [x] **TASK-P2-003:** Handle missing transactions (if parser misses any).
    - **Status:** Completed via Manual Injection workaround (`manual_positions.csv`).

### Phase 3: Fix Ticker Mappings
- [ ] **TASK-P3-001:** Fix TKMS ticker in `asset_universe.csv`.
    - **Status:** Deferred. Small position, low priority.
- [ ] **TASK-P3-002:** Investigate/Fix delisted stocks (TAAT, Cresco).
    - **Status:** Deferred. Small positions, low priority.

### Phase 4: Documentation & Cleanup
- [x] **TASK-P4-001:** Update `SYSTEM_FLOW.md` with correct architecture.
    - **Status:** Completed 2025-11-29.
- [ ] **TASK-P4-002:** Remove misleading `data/true_data/portfolio_holdings.csv`.
    - **Status:** Deferred. File serves as reference/backup.
- [x] **TASK-P4-003:** Update README with correct usage instructions.
    - **Status:** Completed 2025-11-29.

## Phase 2: Technical Debt & Optimization

> **Comprehensive Plan:** See `docs/plans/phase_2_implementation.md` for detailed design.

### TASK-005: Pydantic Schemas for Core Data Structures
- [x] **TASK-005a:** Create `src/models/` directory structure.
    - **Files:** `__init__.py`, `portfolio.py`, `holdings.py`, `exposure.py`
    - **Deliverable:** Pydantic models for Position, ETFHolding, ExposureRecord
    - **Status:** Completed 2025-11-28.
- [x] **TASK-005b:** Integrate models into `state_manager.py`.
    - **Constraint:** Backward-compatible (still returns DataFrames for now)
    - **Status:** Completed 2025-11-28. Added Pydantic validation with NaN→None conversion.
- [x] **TASK-005c:** Integrate models into `aggregation.py`.
    - **Constraint:** Use ExposureRecord for internal aggregation dict
    - **Status:** Completed 2025-11-28. Replaced dict with AggregatedExposure model.
- **Status:** ✅ Completed
- **Estimated Time:** 2-3 hours

### TASK-006: Refactor `aggregation.py` Module
- [x] **TASK-006a:** Create `src/core/aggregation/` modular package.
    - **Files:** `direct.py`, `classification.py`, `grouping.py`, `enrichment.py`, `output.py`, `__init__.py`
    - **Status:** Completed 2025-11-28.
- [x] **TASK-006b:** Create unit tests for each module.
    - **File:** `tests/test_aggregation_v2.py` (13 tests)
    - **Status:** Completed 2025-11-28.
- [x] **TASK-006c:** Migrate callers and remove old monolithic file.
    - **Updated:** `scripts/run_pipeline.py`, `tests/test_aggregation.py`
    - **Status:** Completed 2025-11-28.
- **Status:** ✅ Completed
- **Estimated Time:** 2.5 hours (actual: ~1.5 hours)

### TASK-010: Add Integration Tests
- [x] **TASK-010a:** Create test fixtures in `tests/fixtures/`.
    - **Files:** `asset_universe_test.csv`, `portfolio_holdings_test.csv`, `ishares_holdings.csv`
    - **Status:** Completed 2025-11-28.
- [x] **TASK-010b:** Implement `tests/test_integration.py`.
    - **Tests:** Pipeline runs, value conservation, direct+indirect holdings aggregation
    - **Status:** Completed 2025-11-28. Fixed mock signature and column name assertions.
- [x] **TASK-010c:** Add unit tests for refactored aggregation modules.
    - **File:** `tests/test_aggregation_v2.py` (13 tests covering all modules)
    - **Status:** Completed 2025-11-28 (as part of TASK-006).
- **Status:** ✅ Completed
- **Estimated Time:** 1 hour (actual: ~30 mins)

### TASK-008: Add Type Hints to Core Modules
- [x] **TASK-008a:** Add explicit type casts in `src/core/aggregation/direct.py`.
    - **Issue:** `row["isin"]` returns ambiguous type; needs `str(row["isin"])` cast.
    - **Status:** Completed 2025-11-28.
- [x] **TASK-008b:** Add explicit type casts in `src/core/aggregation/grouping.py`.
    - **Issue:** Same row access pattern; `record.add_indirect()` receives ambiguous type.
    - **Status:** Completed 2025-11-28.
- [x] **TASK-008c:** Add explicit type casts in `src/core/aggregation/enrichment.py`.
    - **Issue:** `dropna(subset=)` and DataFrame subset return types. Used `cast()` for return types.
    - **Status:** Completed 2025-11-28.
- [x] **TASK-008d:** Document pandas stub limitations in output.py.
    - **Note:** `pd.DataFrame(columns=[...])` has incorrect type stubs - runtime correct.
    - **Status:** Completed 2025-11-28. No code change needed.
- [x] **TASK-008e:** Add type annotations to test files (optional).
    - **Status:** Completed 2025-11-28. Added `-> None` return types to all test methods.
- **Status:** ✅ Completed
- **Strategy:** Used explicit `str()`, `float()`, and `cast()` on DataFrame row access. Remaining warnings are pandas type stub issues (not runtime errors).

## Phase 3: Code Quality & Cleanup

### TASK-011: Fix Pydantic v2 Deprecation Warnings
- [x] **TASK-011a:** Update `src/models/holdings.py` to use `ConfigDict` instead of `class Config`.
    - **Context:** Pydantic v2 deprecation warning in test output.
    - **Status:** Completed 2025-11-28.
- [x] **TASK-011b:** Verify no other models use deprecated `class Config` pattern.
    - **Status:** Completed 2025-11-28. No other models affected.
- **Status:** ✅ Completed
- **Estimated Time:** 15 mins (actual: 5 mins)

### TASK-012: Fix Pandera Import Warnings
- [x] **TASK-012:** Update pandera imports from `import pandera as pa` to `import pandera.pandas as pa`.
    - **Files:** `scripts/run_pipeline.py`, `tests/test_validation.py`, `src/utils/schemas.py`
    - **Context:** FutureWarning in test output about deprecated top-level imports.
    - **Status:** Completed 2025-11-28. Also updated error imports to `from pandera import errors`.
- **Status:** ✅ Completed
- **Estimated Time:** 10 mins (actual: 10 mins)

### TASK-013: Fix Bare Except Anti-Pattern
- [x] **TASK-013:** Replace bare `except:` with `except (OSError, ValueError):` in `scripts/visualize_portfolio.py:16`.
    - **Context:** E722 ruff warning. Bare except catches KeyboardInterrupt/SystemExit.
    - **Status:** Completed 2025-11-28.
- **Status:** ✅ Completed
- **Estimated Time:** 5 mins (actual: 2 mins)

### TASK-015: Fix Pipeline Validation & Data Flow
- [x] **TASK-015a:** Strict I/O Separation (State Manager)
    - **File:** `src/data/state_manager.py`
    - **Action:** Remove `LEGACY_TRUTH_PATH` fallback logic. Ensure pipeline only reads `calculated_holdings.csv`.
- [x] **TASK-015b:** Update Validation Script Source
    - **File:** `scripts/validate_pipeline.py`
    - **Action:** Point `TRUTH_PATH` to `data/true_data/ground_truth_merged.csv`.
- [x] **TASK-015c:** Refine Validation Logic (Quantity vs Value)
    - **File:** `scripts/validate_pipeline.py`
    - **Action:** Make Quantity mismatch a Critical Fail, Value mismatch a Warning.
- [x] **TASK-015d:** Manual Data Injection (Workaround)
    - **Context:** PDF lacks quantities for "Direktkauf". Inject missing positions manually.
    - **Action:** Create `manual_positions.csv` and update `scripts/parse_pdfs_to_csv.py` to merge it.
- [x] **TASK-015e:** Verify End-to-End
    - **Action:** Run `scripts/run_full_pipeline.py` and confirm clean execution.

## Backlog (Future)

### TASK-014: Vanguard Adapter
- [ ] **TASK-014:** Create adapter for Vanguard ETFs.
    - **Context:** Auto-generated from ISIN DE0007500001 on 2025-11-23.
    - **Priority:** Low
- **Status:** Backlog
