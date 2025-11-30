# 🟢 Active Session State
**Objective:** Manual Data Injection (Workaround) (TASK-015d)
**Status:** Build

## 🛡️ Applied Constraints
- **Strict I/O Separation:** Pipeline must rely on `calculated_holdings.csv` (which will now include manual inputs).
- **Manual Override:** Explicitly support `data/inputs/manual_holdings/manual_positions.csv`.
- **Validation Authority:** `ground_truth_merged.csv` remains the authority for validation.

## 📝 Current Focus
*   **Phase:** Phase 2 (Manual Injection)
*   **Ref:** `docs/plans/phase_3_validation_fix_final.md`

## 🧠 Context & Learnings
*   **Critical Finding:** The `Account statement.pdf` (Format A: Direktkauf) **does not contain quantities**. Parsing is impossible for these rows.
*   **Decision:** We will inject the missing positions manually from the Truth data into the pipeline input stream.
