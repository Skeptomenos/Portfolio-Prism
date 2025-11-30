# 🟢 Active Session State
**Objective:** Troubleshoot PDF Parser (TASK-015d)
**Status:** Build / Debug

## 🛡️ Applied Constraints
- **Strict I/O Separation:** Pipeline must rely on parsed data, not validation files.
- **Regex Robustness:** Parser must handle "Direktkauf" (Direct Buy) and "Sparplan" (Savings Plan) equally.
- **Verification:** Unit test the regex fix before running full pipeline.

## 📝 Current Focus
*   **Phase:** Phase 2 (Parser Troubleshooting)
*   **Ref:** `docs/plans/phase_3_validation_fix_v2.md`

## 🧠 Context & Learnings
*   **Issue:** `validate_pipeline.py` exposed that `calculated_holdings.csv` is missing major assets (MSFT, AMZN).
*   **Root Cause:** The PDF definitely contains these transactions (confirmed by agent scan), so `src/pdf_parser/parser.py` is failing to regex-match them.
*   **Hypothesis:** The parser might be over-optimized for "Sparplan" or misses the specific "Direktkauf" keyword pattern.
