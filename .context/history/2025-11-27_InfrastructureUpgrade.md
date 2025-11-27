# 🟢 Active Session State
**Objective:** Transition to Spec-Driven Architecture & Verify Pipeline
**Status:** Verify

## 🛡️ Applied Constraints
- **Logic/IO Separation:** Logic = Pure Math. IO = Side Effects.
- **Cache-First IO:** APIs slow/flaky. Cache everything (TTL).
- **Hybrid First:** Manual Escape Hatch priority.
- **Fail-Fast Contracts:** Validate external data at gate.

## 📝 Current Focus
*   **Phase:** Phase 1: Spec-Driven Migration & Verification
*   **Ref:** See `docs/specs/tasks.md` for detailed execution status.

## 🧠 Context & Learnings
*   **State Reset:** Transitioned to `v3` directives. Scaffolding complete.
*   **Legacy Context:** Need to verify the output of the previous run (ISIN resolution/Apple valuation) and execute the DB->CSV migration plan.