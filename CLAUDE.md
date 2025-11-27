# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## ⚠️ READ THESE FILES FIRST (MANDATORY)

Before starting ANY task, read in this exact order:

1. **`docs/agent/AI_CODING_DIRECTIVES.md`** ← **THE CONSTITUTION** (Read FIRST. Defines the v3 Spec-Driven Workflow).
2. **`docs/agent/CODING_STANDARDS.md`** ← Style, Security, & Testing Rules.
3. **`.context/active_state.md`** ← Current Brain State.
4. **`.context/handover.md`** ← Continuity Context.
5. **`docs/PROJECT_LEARNINGS.md`** ← Domain Constraints.

**Why this order matters:**
- You must know the **Law** (`AI_CODING_DIRECTIVES`) before you check the **State**.
- The v3 Directives mandate a specific "Spec Check" that you must perform immediately.

---

## Claude Code Tool Reference

| Abstract Instruction | Claude Code Tool | Policy |
|---------------------|------------------|--------|
| **Project Management** | `Read`/`Edit` `docs/specs/tasks.md` | **PRIMARY SOURCE OF TRUTH**. Update this file to track progress. |
| Ephemeral Sub-tasks | `TodoWrite` | **SCRATCHPAD ONLY**. Use for quick checklists within a single turn. |
| Read file | `Read` | Always read before editing. |
| Write file | `Write` | Create new files or overwrite small ones. |
| Edit file | `Edit` | Use for targeted changes in large files. |
| Find files | `Glob` | Use `Glob` to check for specs: `docs/specs/*` |
| Search contents | `Grep` | Search for code patterns. |
| Execute command | `Bash` | Run tests, linters, scripts. |

---

## Task Lifecycle (The v3 Loop)

**Phase 0: Initialization (Bootloader)**
1. `ls -F` (Check environment)
2. `ls docs/specs/` (Check for Specs: `product.md`, `tech.md`, `requirements.md`)
3. Read `.context/active_state.md`.
4. **Reseting?** If new task, archive old state to `.context/history/` (See `AI_CODING_DIRECTIVES.md`).

**Phase 1: Spec & Architect**
- **Rule:** Do not write code without a Spec.
- **Action:** Read/Create `docs/specs/` files. Decompose work into `docs/specs/tasks.md`.

**Phase 2: Build & Implement**
- **Rule:** Implement atoms from `tasks.md`.
- **Action:** Code -> Test -> Mark Task Done.

**Phase 3: Verify & Secure**
- **Rule:** Pass all gates.
- **Action:** `pytest`, `ruff check .`, `ruff format .`.

**Phase 4: Deliver & Document (Epilogue)**
- **Rule:** Preserve knowledge.
- **Action:**
    - Update `CHANGELOG.md`.
    - Update `docs/PROJECT_LEARNINGS.md`.
    - **Archival Rotation:** Move `.context/active_state.md` to `.context/history/`.
    - Create clean `.context/handover.md`.

---

## Project Overview

Portfolio Look-Through Analyzer - A Python POC automating portfolio analysis.

### Critical Operating Rules
*   **Hybrid First:** Prioritize manual file drops over brittle scrapers.
*   **I/O Fortress:** Cache all API calls. Trust no input.
*   **Logic/IO Separation:** Keep `src/core/` pure.
*   **Spec-Driven:** If it's not in `docs/specs/`, it doesn't exist.

### Development Commands
```bash
# Setup
source venv/bin/activate
pip install -r requirements.txt

# Run Pipeline
python -m scripts.run_pipeline

# Testing & Quality
pytest
ruff check .
ruff format .
```

### Directory Structure
```
src/             - Main source code
config/          - Configuration files
scripts/         - Executable scripts
data/            - Inputs & Working data
outputs/         - Reports
docs/
  specs/         - LIVING SPECIFICATIONS (product, tech, requirements, tasks)
  agent/         - Directives & Standards
.context/        - State management
  active_state.md
  history/
```