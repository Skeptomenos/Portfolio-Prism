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

- [ ] **TASK-004:** Migrate Legacy DB to CSV.
    - **Context/Constraints:** See `Phase 1.5` plan. Use `scripts/migrate_db_to_csv.py`.
    - **Status:** Pending (script fixed, ready to run)

## Phase 2: Technical Debt & Optimization
- [ ] **TASK-005:** Implement Pydantic Schemas for Core Data Structures.
    - **Context/Constraints:** Replace ad-hoc dicts with formal schemas (Tech Spec).
    - **Status:** Pending

- [ ] **TASK-006:** Refactor `amundi.py` Adapter.
    - **Context/Constraints:** Break monolithic functions into testable atoms (Project Learnings).
    - **Status:** Pending

- [ ] **TASK-007:** Fix Remaining Test Failure.
    - **Context/Constraints:** `test_validation_failure_negative_weight` fails in `tests/test_validation.py`.
    - **Status:** Pending

- [ ] **TASK-008:** Add Type Hints to Core Modules.
    - **Context/Constraints:** Type checker shows many type warnings. Add proper type annotations.
    - **Status:** Pending
