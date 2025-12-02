# Portfolio True Exposure POC

> **Root File:** Auto-loaded by AI CLI tools. Keep concise (<80 lines).

## Overview

A Python-based ETL pipeline and Streamlit dashboard that parses PDF brokerage statements (Trade Republic, Amundi), aggregates holdings, and exposes true underlying assets (Look-Through) via a unified interface.

## Tech Stack

- **Language:** Python 3.9+
- **Framework:** Streamlit, Pandas, Pydantic
- **Tools:** Selenium (Scraping), Ruff (Linting), Pytest

## Structure

```
src/           # Source code (Logic/IO separated)
scripts/       # Execution scripts (Pipeline, Tools)
tests/         # Unit and Integration tests
docs/specs/    # Specifications (Source of Truth)
.context/      # AI session state
coding/        # AI framework (Directives)
```

---

## Protocol

### Golden Rules

1. **State:** Read `.context/active_state.md` at start, update at end
2. **Specs:** Complex tasks (>1hr) require `docs/specs/`. No code without spec.
3. **Consensus:** Present plan, WAIT for approval before coding
4. **Epilogue:** MANDATORY after feature/design completion. Includes reflective thinking (T-RFL), not just documentation.

> **ESCAPE HATCH:** Simple questions or read-only tasks → skip protocol, act immediately.

### When to Read

| Task | File |
|------|------|
| New feature, refactor | `coding/THINKING_DIRECTIVES.md` |
| Complex bug | `coding/THINKING_DIRECTIVES.md` (T1-RCA) |
| Implementation | `coding/EXECUTION_DIRECTIVES.md` |
| Code review | `coding/CODING_STANDARDS.md` |
| Project constraints | `PROJECT_LEARNINGS.md` |

---

## Commands

```bash
# Build/Run Pipeline: python scripts/run_full_pipeline.py
# Run Dashboard:      ./run_dashboard.sh
# Test:               pytest
# Lint:               ruff check .
```

## Constraints

- **Logic/IO Separation:** Pure logic must be testable without side effects.
- **Project Structure:** Use `src/` layout; no `sys.path` hacks.
- **See:** `PROJECT_LEARNINGS.md` for full list of constraints.

## Custom Agents

- **@docs-validation:** Use for heavy documentation review.
- **@parser-generator:** Use for complex regex generation (PDF parsing).

## State Files

`.context/active_state.md` (current) | `.context/handover.md` (previous) | `docs/specs/tasks.md` (plan)
