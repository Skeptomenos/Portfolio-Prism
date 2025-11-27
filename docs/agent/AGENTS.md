# AI Agent Instructions (Generic)

This document provides the "Bootloader" instructions for any AI agent (Claude, ChatGPT, etc.) operating in this repository.

> **CRITICAL AUTHORITY:**
> The "Code of Law" for this project is located in **`docs/agent/AI_CODING_DIRECTIVES.md`**.
> You **MUST** read that file immediately after initialization. It defines your Directives, Directives for Coding, and Operational Mandates.
> **Violating those directives is a system failure.**

## 1. Initialization Protocol (Phase 0)

You are "booting up" into an ongoing development process. Do not act until you are oriented.

1.  **Environment Scan:**
    *   `ls -F` (See immediate context)
    *   `git status` (Check for dirty state)
    *   `ls -F docs/specs/` (Check for existing Specifications)

2.  **Load Directives:**
    *   **READ** `docs/agent/AI_CODING_DIRECTIVES.md` (The Constitution)
    *   **READ** `docs/agent/CODING_STANDARDS.md` (The Style Guide)

3.  **Load State:**
    *   **READ** `.context/active_state.md`.
    *   **READ** `.context/handover.md`.
    *   **READ** `docs/PROJECT_LEARNINGS.md`.

4.  **State Decision:**
    *   *Continuing?* **RESUME** work. Update "Current Focus" in `active_state.md`.
    *   *New Task?* **ARCHIVE** old state (see Finalization) and **RESET** `active_state.md`.

## 2. Execution Lifecycle (The Loop)

Follow the phases defined in `AI_CODING_DIRECTIVES.md`:

*   **Phase 1: Spec & Architect** -> Update `docs/specs/` (product, tech, requirements).
*   **Phase 2: Build & Implement** -> Code -> `tasks.md` update.
*   **Phase 3: Verify & Secure** -> Tests -> Contract Checks.
*   **Phase 4: Deliver & Document** -> Docs -> Changelog.

**Task Tracking:**
*   **Source of Truth:** `docs/specs/tasks.md` is your project manager.
*   **Scratchpad:** Use internal tool lists only for ephemeral sub-steps.

## 3. Finalization Protocol (The Epilogue)

You are **NOT DONE** until you preserve your brain state for the next agent.

1.  **Documentation Sync:**
    *   Update `CHANGELOG.md`.
    *   Update `docs/specs/` if reality diverged from the plan.

2.  **Recursive Learning:**
    *   Update `docs/PROJECT_LEARNINGS.md` with **one** new pattern/anti-pattern found.

3.  **Archival Rotation (CRITICAL):**
    *   **MOVE** `.context/active_state.md` TO `.context/history/YYYY-MM-DD_TaskName.md`.
    *   **CREATE** a fresh `.context/active_state.md` (or leave it for the next agent to initialize).
    *   **UPDATE** `.context/handover.md` with a clean summary for the next agent.

## Project Structure (Map)

*   `src/`: Source code (logic/io separated).
*   `config/`: JSON/CSV config (no hardcoding).
*   `data/`:
    *   `inputs/`: Read-only external data (PDFs).
    *   `working/`: Scratchpad (DBs, Cache).
*   `docs/`:
    *   `specs/`: **Living Specifications** (product, tech, requirements, tasks).
    *   `agent/`: Meta-instructions (Directives, Standards).
*   `.context/`:
    *   `active_state.md`: The current brain.
    *   `history/`: Archived brains.

## Custom Agents

*   **@docs-validation:** Use for heavy documentation review.
*   **@parser-generator:** Use for complex regex generation (PDF parsing).