# Implementation Plan: TASK-015 (Fix Pipeline Validation & Data Flow)

## Objective
Establish strict I/O separation between the production pipeline and validation data, and restore correct validation logic using the authoritative Ground Truth file.

## Phase 1: Strict I/O Separation (The Firewall)
**Goal:** Sever the link where the pipeline reads validation data as input.

- [x] **Step 1.1: Remove Fallback Logic**
    - **File:** `src/data/state_manager.py`
    - **Action:** Delete `LEGACY_TRUTH_PATH` fallback block.
    - **Status:** **Done** (Applied in previous turn).
- [x] **Step 1.2: Clean Configuration**
    - **File:** `src/data/state_manager.py`
    - **Action:** Remove `LEGACY_TRUTH_PATH` constant.
    - **Status:** **Done** (Applied in previous turn).

## Phase 2: Validation Restoration (The Guardrail)
**Goal:** Repair the validation script to use the correct ground truth file and comparison logic.

- [x] **Step 2.1: Update Truth Source**
    - **File:** `scripts/validate_pipeline.py`
    - **Action:** Change `TRUTH_PATH` to `data/true_data/ground_truth_merged.csv`.
    - **Status:** **Done** (Applied via file rewrite).
- [x] **Step 2.2: Rewrite Data Loader**
    - **File:** `scripts/validate_pipeline.py`
    - **Action:** Simplify `load_ground_truth()` to read `ISIN` and `Quantity` directly from the CSV.
    - **Status:** **Done** (Applied via file rewrite).
- [x] **Step 2.3: Refine Comparison Logic**
    - **File:** `scripts/validate_pipeline.py`
    - **Action:** Implement "Quantity First" validation (Critical Fail) and "Value Second" (Warning).
    - **Status:** **Done** (Applied via file rewrite).

## Phase 3: Verification (The Proof)
**Goal:** Prove end-to-end functionality.

- [ ] **Step 3.1: Dry Run Validation**
    - **Action:** `python -m scripts.validate_pipeline`
- [ ] **Step 3.2: Full Pipeline Test**
    - **Action:** `python -m scripts.run_full_pipeline`
