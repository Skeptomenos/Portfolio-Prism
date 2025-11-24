# AI Architect Directives v2 (State-Aware & First Principles)

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
> *   **Exceptions:** Maintain professional, complete sentences for **Code Docstrings** and **User-Facing Docs** (README, CHANGELOG).

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
- **Check Constraints:** Read `docs/PROJECT_LEARNINGS.md`.
    - **IF EMPTY:** Log "No prior constraints found" in your state.
    - **IF CONTENT EXISTS:** Identify 1-3 **Applied Constraints** relevant to this task and list them in your active state.

**Template for `.context/active_state.md`:**
```markdown
# 🟢 Active Session State
**Objective:** [Concise Goal]
**Status:** [Planning | In Progress | Debugging]

## 🛡️ Applied Constraints
- [Constraint 1 from PROJECT_LEARNINGS.md]

## 📝 Plan & Progress
- [ ] 1. [Step 1]
- [ ] 2. [Step 2]

## 🧠 Context & Learnings
*   [Telegraphic Notes: Errors, findings, scratchpad]
```

**0.2: State Maintenance (The Heartbeat)**
- **Update Strategy:** You must update `.context/active_state.md` **at the end of every logical block of work** (e.g., after planning, after coding a module, after testing).
- **Batching:** You may perform multiple related actions (edit 3 files) before updating the state, but you **MUST** update it before asking the user for input or ending your turn.
- **Style:** Use **Telegraphic Style**. Maximize info/token.
- **Why?** The tool call is your proof of work. If your session crashes, the next agent relies on this file.

**0.3: The OODA Loop (Debugging Protocol)**
- When an action fails, **DO NOT** guess.
    - **Observe:** Gather evidence (screenshot, HTML source, error trace) via shell commands (`ls`, `grep`) or file reads.
    - **Orient:** State explicitly in `.context/active_state.md` why your mental model was wrong based on the evidence.
    - **Decide:** Formulate a single, testable hypothesis.
    - **Act:** Implement the minimal change to test that hypothesis.

---

### Phase 1: Analysis & Architecture (FIRST PRINCIPLES)

Do not plan the solution until you have deconstructed the problem.

**1.1: Recursive Decomposition (The Knife)**
- **Complexity Threshold:** IF the task is simple (< 50 lines of code, single script), **SKIP** decomposition and proceed to Implementation.
- **Deconstruct:** Break complex requests down into **Atomic Units**.
- **Definition:** An Atomic Unit is a problem so small that it:
    1.  Has zero external dependencies (Pure Logic).
    2.  Can be solved with a single function/class.
    3.  Can be verified with a single unit test.
- **The 'Why' Test:** For every component, ask "Why does this exist?" The answer must be "to transform Input A to Output B."

**1.2: Modularity (The Box)**
- **Group:** Organize Atomic Units into logical **Modules**.
- **Interface:** Define strict **Data Contracts** (Interfaces/Schemas) between modules.
- **Constraint:** High Cohesion (related things stay together) and Low Coupling (modules rarely touch).

**1.3: Radical Simplicity (The Filter)**
- **Buy vs. Build:** Before implementing an Atom, check if a Standard Library or approved dependency solves it.
- **Tool Preference:** Do not write a Python script to do what a standard shell command (`grep`, `find`, `sed`) can do in one line.
- **Implementation:** Use the most readable, standard solution. **Complexity is a failure of decomposition.**

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

---

### Phase 2: Build & Implement (BOTTOM-UP)

**2.1: Construction Order**
- **Atoms First:** Implement the Atomic Units (Pure Logic) first.
- **Verify Early:** Write unit tests for Atoms immediately. You are testing math/logic, not side effects.
- **Orchestration Last:** Only write the "Glue Code" (Scripts/Controllers) after the building blocks are proven solid.

**2.2: Strict Logic/IO Separation**
- **Pure Logic:** Core calculations must never touch the network, disk, or database.
- **I/O Edge:** Push all side effects to the boundaries (Adapters/Services).
- **Benefit:** This makes the core logic 100% testable without mocks.

**2.3: Persistence & Safety**
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

---

### Phase 4: Delivery & Epilogue (DEFINITION OF DONE)

You are **NOT** done until you have executed this sequence:

**4.1: Documentation Sync (Audit Trail)**
- [ ] **User Facing:** Update `CHANGELOG.md` if features or usage changed. (Professional Tone)
- [ ] **Dev Facing:** Append to `docs/DECISION_LOG.md` if you made architectural trade-offs. (Telegraphic Tone)
- [ ] **Code Facing:** Ensure docstrings match the new code reality. (Professional Tone)

**4.2: Recursive Learning (Synthesis)**
- [ ] **Reflect:** Review your session in `.context/active_state.md`.
- [ ] **Extract:** Identify **one** reusable pattern or anti-pattern.
- [ ] **Commit:** Update `docs/PROJECT_LEARNINGS.md` with this new rule. (Do not dump logs; distill wisdom). (Telegraphic Tone)

**4.3: Archival Rotation (Continuity)**
- [ ] **Preparation:** Ensure `.context/history/` directory exists.
- [ ] **Archive:** Move `.context/active_state.md` to `.context/history/YYYY-MM-DD_TaskName.md`.
- [ ] **Handover:** Create/Overwrite `.context/handover.md` with a 3-bullet summary of "Where we are" and "Next Steps" for the next agent. (Telegraphic Tone)