# 🟢 Active Session State
**Objective:** Fix Pipeline Validation & Data Flow (TASK-015)
**Status:** Build

## 🛡️ Applied Constraints
- **Strict I/O Separation:** Production pipeline must NOT depend on validation data.
- **Validation Authority:** `ground_truth_merged.csv` is the single source of truth for direct holdings.
- **Quantity First:** Validation must prioritize Quantity (invariant) over Value (volatile).

## 📝 Current Focus
*   **Phase:** Phase 1 (Strict I/O Separation)
*   **Ref:** `docs/specs/tasks.md` (TASK-015)

## 🧠 Context & Learnings
*   The previous validation script pointed to a missing file `portfolio_truth.csv`.
*   The State Manager had a fallback to this missing file, which was a bad pattern (mixing test/prod data).
*   Correct truth file is `data/true_data/ground_truth_merged.csv`.
