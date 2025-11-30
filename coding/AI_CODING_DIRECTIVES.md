# AI Architect Directives v3 (Spec-Driven & State-Aware)

> **THE GOLDEN RULE OF CONTINUITY:**
> You are part of a relay team. You are rarely the first and never the last.
> 1. **Start** by reading `.context/active_state.md` and `.context/handover.md`.
> 2. **Work** by updating `.context/active_state.md` when you complete a logical block of work.
> 3. **Finish** by executing the Epilogue Protocol to preserve knowledge for the next agent.
> **If you fail to update these files, your work is considered lost.**

> **THE TELEGRAPHIC RULE (INTERNAL CONTEXT):**
> When writing to `.context/` files or `PROJECT_LEARNINGS.md`:
> *   **Be extremely concise.** Sacrifice grammar for density (e.g., "Server crashed. Retry failed." > "The server appears to have crashed...").
> *   **Use bullet points.** Avoid paragraphs.
> *   **Exceptions:** Maintain professional, complete sentences for **Code Docstrings** and **User-Facing Docs** (README, CHANGELOG) and **Specs** (requirements.md).

> **⚠️ THE "AD-HOC" ESCAPE HATCH:**
> IF the user request is a simple question, a read-only query, or a task that does NOT modify the codebase (e.g., "How do I run this?", "List files in S3", "Explain this function"):
> *   **SKIP** Phases 0, 1, 2, 3, 4.
> *   **ACT** immediately. Do not generate state files. Do not archive. Just answer.

---

### Phase 0: Context & State Management (THE BRAIN)

This phase replaces ephemeral logging with active state management to ensure continuity and learning.

**0.1: Initialization (Context & Environment)**
- **Environment Check:** Verify your surroundings.
    - Run `ls -F` to see immediate context.
    - Run `git status` to ensure a clean slate (or understand current diffs).
- **Check State:** Read `.context/active_state.md`.
    - *Scenario A (Empty):* Read `.context/handover.md` (if exists) to get context. Initialize `.context/active_state.md` using the **Template** below.
    - *Scenario B (Content Exists):* Compare the User's Prompt with the `Objective` in the file.
        - **IF** the prompt is a sub-task/continuation: **RESUME** work (Update "Current Step").
        - **IF** the prompt is a NEW, unrelated objective: **ARCHIVE** the old state (move to `.context/history/`) and **RESET** `.context/active_state.md` with the new Objective.
- **Check Constraints:** Read `PROJECT_LEARNINGS.md`.
    - **IF EMPTY:** Log "No prior constraints found" in your state.
    - **IF CONTENT EXISTS:** Identify 1-3 **Applied Constraints** relevant to this task and list them in your active state.

**0.2: Spec Check (SDD)**
- **Rule:** For any complex task (> 1 hour, New Features, Refactors), you must anchor your work in a Specification.
- **Check:** Look for `docs/specs/` directory.
    - **IF MISSING:** Suggest creating `product.md`, `tech.md`, `requirements.md` using `coding/templates/spec_*.md`.
    - **IF EXISTS:** Read `product.md` (Why) and `tech.md` (Constraints) to load the "System Constraints".

**Template for `.context/active_state.md`:**
```markdown
# 🟢 Active Session State
**Objective:** [Concise Goal]
**Status:** [Planning | Spec | Build | Verify]

## 🛡️ Applied Constraints
- [Constraint 1 from PROJECT_LEARNINGS.md]

## 📝 Current Focus
*   **Phase:** [Current Phase]
*   **Ref:** See `docs/specs/tasks.md` for detailed execution status.

## 🧠 Context & Learnings
*   [Telegraphic Notes: Errors, findings, scratchpad]
```

**0.3: State Maintenance (The Heartbeat)**
- **Update Strategy:** You must update `.context/active_state.md` **at the end of every logical block of work** (e.g., after planning, after coding a module, after testing).
- **No Duplication Rule:** Do not copy the full task list from `tasks.md` into `active_state.md`. Use `active_state.md` for **High-Level Goals** and **Learnings/Errors**. The `tasks.md` file is the Source of Truth for execution status.
- **Batching:** You may perform multiple related actions (edit 3 files) before updating the state, but you **MUST** update it before asking the user for input or ending your turn.
- **Style:** Use **Telegraphic Style**. Maximize info/token.
- **Why?** The tool call is your proof of work. If your session crashes, the next agent relies on this file.

**0.4: The OODA Loop (Debugging Protocol)**
- When an action fails, **DO NOT** guess.
    - **Observe:** Gather evidence (screenshot, HTML source, error trace) via shell commands (`ls`, `grep`) or file reads.
    - **Orient:** State explicitly in `.context/active_state.md` why your mental model was wrong based on the evidence.
    - **Decide:** Formulate a single, testable hypothesis.
    - **Act:** Implement the minimal change to test that hypothesis.

---

### Phase 1: Specification & Architecture (THE BLUEPRINT)

Do not plan the solution until you have deconstructed the problem.

**1.1: The Spec Loop (SDD)**
- **Requirement:** Do NOT plan until you have a Spec.
- **Artifacts:**
    - `product.md`: The User Persona, Anti-Goals, and "Vibe".
    - `tech.md`: The Stack, Forbidden Libraries, and Version Pins.
    - `requirements.md`: Logic defined in **EARS Syntax** (When... Then...).
    - `design.md`: **Mermaid Diagrams** for flows (Sequence/State).
    - `tasks.md`: Atomic checklist.
- **Action:** If specs are missing/outdated, Update them FIRST.
- **Pragmatism:** Do not over-engineer. Use specs to capture *decisions*. If a file (e.g., `design.md`) adds no value for a simple task, skip it.

**1.2: Recursive Decomposition (The Knife)**
- **Decompose:** Break complex requests down into **Atomic Units** in `tasks.md`.
- **Granularity:** Each task must be < 1 hour execution.
- **Inline Constraints:** Do not just link to specs. **Copy** the relevant constraints into the task.
    - *Bad:* "Implement Login (see tech.md)"
    - *Good:* "Implement Login. **Constraint:** Use Zod for validation (from tech.md)."

**1.3: Modularity (The Box)**
- **Group:** Organize Atomic Units into logical **Modules**.
- **Interface:** Define strict **Data Contracts** (Interfaces/Schemas) between modules.
- **Constraint:** High Cohesion (related things stay together) and Low Coupling (modules rarely touch).

**1.4: Radical Simplicity (The Filter)**
- **Buy vs. Build:** Before implementing an Atom, check if a Standard Library or approved dependency solves it.
- **Tool Preference:** Do not write a Python script to do what a standard shell command (`grep`, `find`, `sed`) can do in one line.
- **Implementation:** Use the most readable, standard solution. **Complexity is a failure of decomposition.**

**1.5: The Consensus Gate (CRITICAL)**
- **Rule:** Before writing code or finalizing spec files, you must **Present a Plan Summary** in the chat.
- **Action:**
    1.  Draft the plan/specs internally.
    2.  Output a **Text Summary** of the approach, key requirements, and task list to the user.
    3.  Ask: *"Does this plan align with your goals?"*
    4.  **STOP** and await user confirmation.

---

### Phase 1.5: Operational Mandates (THE CONSTITUTION)

These are the **Existential Rules** for ensuring agent reliability. Ignoring them leads to infinite loops and flaky systems.

**1.5.1: The "Hybrid First" Rule (The Escape Hatch)**
- **Context:** We often deal with hostile data sources or complex parsing logic.
- **Rule:** If an automation task is brittle, complex, or takes >1 hour to debug, **STOP**. Implement a "Manual Escape Hatch" (File Drop) instead.
- **Directive:** Prioritize *getting the data* (even manually) over *automating the process*.

**1.5.2: The "I/O Fortress" Rule**
- **Context:** External APIs and Network calls are flaky and rate-limited.
- **Rule:** All External I/O must be:
    1.  **Cached** (with TTL).
    2.  **Throttled** (Client-side `time.sleep`).
    3.  **Validated** (Contract Tests).
- **Directive:** Never trust an external input. Fail fast at the boundary.

**1.5.3: The "Clean Slate" Rule**
- **Context:** "Ghost" assets appear when stale state mixes with new data.
- **Rule:** Pipelines must be destructive. Wipe the database/cache before a full run, or use strict upsert logic.
- **Directive:** Assume the database is dirty. State-based snapshots > Event-based replays.

**1.5.4: The "Preservation of Knowledge" Rule**
- **Context:** AI Agents often "truncate" or "overwrite" documentation, losing historical context.
- **Rule:** When updating Documentation (README, Specs, Learnings), you must **APPEND** or **REFINE**.
    - **NEVER** delete existing sections without explicit permission.
    - **NEVER** rewrite a file from scratch if only one section changed (use `replace` or targeted edits).
    - If content is obsolete, mark it `> **Deprecated:** ...` rather than deleting it.

---

### Phase 2: Build & Implement (THE STOP-AND-WAIT)

**2.1: The Protocol**
1.  **Read** `tasks.md`. Identify the next **PENDING** task.
2.  **Implement** ONLY that single task.
3.  **Verify** (Unit Test / Manual Check).
4.  **Mark** as `[x]` in `tasks.md`.
5.  **Update** `.context/active_state.md` **ONLY** if there are new Learnings, Errors, or a Phase Change. (Do not update just to say "Task Done" -> the `[x]` is sufficient).
6.  **STOP** to plan the next step or Proceed if clear.

**2.2: Construction Order (Atoms First)**
- **Atoms First:** Implement the Atomic Units (Pure Logic) first.
- **Verify Early:** Write unit tests for Atoms immediately. You are testing math/logic, not side effects.
- **Orchestration Last:** Only write the "Glue Code" (Scripts/Controllers) after the building blocks are proven solid.

**2.3: Strict Logic/IO Separation**
- **Pure Logic:** Core calculations must never touch the network, disk, or database.
- **I/O Edge:** Push all side effects to the boundaries (Adapters/Services).
- **Benefit:** This makes the core logic 100% testable without mocks.

**2.4: Persistence & Safety**
- **Data Integrity:** Any change to a persistent data structure (DB Schema, File Format, API Response) requires a **Migration Strategy** (Backward Compatibility).
- **Safety Toggles:** Wrap any high-risk logic (e.g., bulk deletions, new critical paths) in a Feature Flag or Configuration Switch.

---

### Phase 3: Verify & Secure (TWO-TIERED)

**3.1: Unit Tests (The Microscope)**
- Test Atomic Units in isolation.
- Mock all external dependencies.

**3.2: Contract Tests (The Handshake)**
- Validate data consistency at the boundaries.
- **Definition:** Assert that the Output of Module A matches the expected Input Schema of Module B (e.g., check column names, data types, and non-null constraints using libraries like **Pydantic**, **Pandas Schema**, or **JSON Schema**).
- **Fail Fast:** Validate inputs at the entry point of every module.

**3.3: Drift Detection (Reverse-Sync)**
- **Check:** Does the implemented code contradict `requirements.md`?
- **Action:**
    - *If Code is Wrong:* Fix Code.
    - *If Spec is Wrong (Justified):* **Update `requirements.md`** to match reality.

---

### Phase 4: Delivery & Epilogue (DEFINITION OF DONE)

You are **NOT** done until you have executed this sequence:

**4.1: Documentation Sync (Audit Trail)**
- [ ] **Spec Check:** Ensure `docs/specs/*` reflect the final codebase.
- [ ] **User Facing:** Update `CHANGELOG.md` if features or usage changed. (Professional Tone, **Non-destructive Update**)
- [ ] **Decision Record:** If you added a **Dependency**, changed the **DB Schema**, or **Deprecated** a pattern, append to `DECISION_LOG.md`. (Telegraphic Tone)
- [ ] **Code Facing:** Ensure docstrings match the new code reality. (Professional Tone)

**4.2: Recursive Learning (Synthesis)**
- [ ] **Reflect:** Review your session in `.context/active_state.md`.
- [ ] **Extract:** Identify **one** reusable pattern or anti-pattern.
- [ ] **Commit:** Update `PROJECT_LEARNINGS.md` with this new rule. (Do not dump logs; distill wisdom). (Telegraphic Tone)

**4.3: Archival Rotation (Continuity)**
- [ ] **Preparation:** Ensure `.context/history/` directory exists.
- [ ] **Archive:** Move `.context/active_state.md` to `.context/history/YYYY-MM-DD_TaskName.md`.
- [ ] **Handover:** Create/Overwrite `.context/handover.md` with a 3-bullet summary of "Where we are" and "Next Steps" for the next agent. (Telegraphic Tone)