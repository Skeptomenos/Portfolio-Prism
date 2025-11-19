# AI Architect Directives

### Phase 0: Task Management & Learning (CRITICAL)

This phase governs the entire task lifecycle.

**0.1: Initialization**
- On a new task, create a unique, temporary log file (e.g., `.llm/logs/TASK_ID.md`).
- In the log, state the `Objective`, `Initial Plan`, and any `Assumptions`.
- Read the permanent `docs/agent/project_learnings.md` file (if it exists) and the agent's global memory to inform the plan.

**0.2: Execution Loop**
- Before every action (writing code, running a command), review the `Key Learnings & Constraints` section of the *current task's log*.
- After every action, log the command, its outcome, and any key observations.
- If an action fails or an assumption is invalidated, add a concise rule to the `Key Learnings & Constraints` section.
- If the plan changes, log the reason for the `Pivot` and the new plan.

**0.2.1: The OODA Loop for Debugging:** When an action fails (especially in web scraping), you MUST follow a strict OODA loop.
    - **Observe:** Your first and only action after a failure is to gather evidence. For scraping, this means saving a screenshot and the full page source. You must then analyze this evidence.
    - **Orient:** In your thought process, you must explicitly state your new orientation based *only* on the evidence from the screenshot/HTML. State what you saw and why your previous assumption was wrong.
    - **Decide:** Formulate a *new, single, testable hypothesis*. (e.g., "My new hypothesis is that the correct selector is `...`").
    - **Act:** Implement *only* the change required to test that single hypothesis. Do not add other changes.

**0.3: Finalization & Learning Persistence**
- On task completion, review the `Key Learnings & Constraints` section of the temporary log.
- For each learning, decide its scope:
    - **Project-Specific:** Append it to the permanent `docs/agent/project_learnings.md` file.
    - **Global (Tool/Language Fact):** Use the `save_memory` tool to persist it.
- Present a final summary of the work completed.
- Delete the temporary log file.

---

### Phase 1: Design & Architect (IMPORTANT)
- **Decompose:** Break the request into a feature plan and log it.
- **Analyze Context:** Understand existing architecture, patterns, and data models.
- **Design Data Schema:** Define clear, normalized schemas for new entities.
- **Design API Contract:** Define explicit, RESTful contracts for new services.
- **Design for Scalability:** Design services to be stateless. Plan caching strategies.
- **Design for Asynchronicity (BEST PRACTICE):** For long-running tasks, prefer event-driven patterns.

### Phase 2: Build & Implement (IMPORTANT)
- **Search First (DRY):** Before writing, search for reusable components.
- **Separate Concerns:** Isolate logic (UI vs. business vs. data access).
- **Small, Focused Functions (BEST PRACTICE):** One job per function.
- **Analyze Performance:** Avoid N+1 queries. Use efficient algorithms.
- **Instrument for Observability:** Add structured logs, metrics, and traces for all new services.

### Phase 3: Verify & Secure (CRITICAL)
- **Write New Tests:** Add comprehensive tests for all new logic, including edge cases.
- **Handle All Errors:** Gracefully handle all potential errors.
- **Sanitize All Inputs:** Never trust external data.
- **Mock External Systems:** In tests, mock all external services (APIs, DBs) for speed and reliability.
- **Pass CI Gates:** Final code must pass all project-defined linters, builds, and security scans.

### Phase 4: Deliver & Document (IMPORTANT)
- **Update Documentation:** Update corresponding API docs, diagrams, and READMEs.
- **Document Concisely (IMPORTANT):** All documentation must follow strict, concise formats.
    - **Function/Method Docs:** Use JSDoc/equivalent. One sentence summary (max 15 words). Bulleted list for `@param`/`@returns`. No paragraphs.
    - **README/Wiki Updates:** Use bullet points or short, declarative sentences. Max 2 sentences per paragraph.
    - **Anti-Pattern:** Avoid conversational, narrative, or verbose explanations.
- **Manage Database Changes (CRITICAL):** Generate a backward-compatible migration script for any schema modification.
- **Ensure Backward Compatibility (CRITICAL):** Do not make breaking changes to public APIs without a versioning strategy.
- **Use Feature Flags (BEST PRACTICE):** Wrap significant new features in a feature flag.
 