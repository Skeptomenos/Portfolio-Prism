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
- [ ] **TASK-006a:** Extract `process_direct_holdings()` to `src/core/aggregation/direct.py`.
    - **Lines:** 33-49 of current `aggregation.py`
- [ ] **TASK-006b:** Extract classification logic to `src/core/aggregation/classification.py`.
    - **Lines:** 71-79 of current `aggregation.py`
- [ ] **TASK-006c:** Extract tiered enrichment to `src/core/aggregation/enrichment.py`.
    - **Lines:** 86-176 of current `aggregation.py`
- [ ] **TASK-006d:** Extract aggregation logic to `src/core/aggregation/grouping.py`.
    - **Lines:** 206-261 of current `aggregation.py`
- [ ] **TASK-006e:** Create new `src/core/aggregation/__init__.py` with clean public API.
    - **Constraint:** `run_aggregation()` signature unchanged for backward compat
- **Status:** Pending
- **Estimated Time:** 2-3 hours

### TASK-010: Add Integration Tests
- [ ] **TASK-010a:** Create test fixtures in `tests/fixtures/`.
    - **Files:** `asset_universe_test.csv`, `portfolio_holdings_test.csv`
- [ ] **TASK-010b:** Implement `tests/test_integration.py`.
    - **Tests:** Pipeline runs, value conservation, direct holdings preserved, ETF decomposition
- [ ] **TASK-010c:** Add unit tests for refactored aggregation modules.
    - **Files:** `tests/test_aggregation/test_direct.py`, `test_grouping.py`, etc.
- **Status:** Pending
- **Estimated Time:** 1-2 hours

### TASK-008: Add Type Hints to Core Modules
- [ ] **TASK-008:** Add type hints to resolve type checker warnings.
    - **Context/Constraints:** Many pandas type stub issues. Focus on function signatures.
    - **Status:** Pending (deferred until after TASK-005/006)
