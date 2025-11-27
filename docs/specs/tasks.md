# Implementation Plan (The "When")

## Phase 1: Spec-Driven Migration & Verification (Current)
- [x] **TASK-001:** Scaffold Specification Documents (`docs/specs/`).
    - **Context/Constraints:** Align with `AI_CODING_DIRECTIVES.md`.
    - **Status:** Completed.

- [ ] **TASK-002:** Verify Ongoing Pipeline Results.
    - **Context/Constraints:** Previous agent left pipeline running. Verify `outputs/true_exposure_report.csv` and `config/asset_universe.csv`.
    - **Status:** Pending

- [ ] **TASK-003:** Migrate Legacy DB to CSV.
    - **Context/Constraints:** See `Phase 1.5` plan. Use `scripts/migrate_db_to_csv.py`.
    - **Status:** Pending

## Phase 2: Technical Debt & Optimization
- [ ] **TASK-004:** Implement Pydantic Schemas for Core Data Structures.
    - **Context/Constraints:** Replace ad-hoc dicts with formal schemas (Tech Spec).
    - **Status:** Pending

- [ ] **TASK-005:** Refactor `amundi.py` Adapter.
    - **Context/Constraints:** Break monolithic functions into testable atoms (Project Learnings).
    - **Status:** Pending
