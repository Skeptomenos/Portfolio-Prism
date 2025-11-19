# AI Agent Instructions

This document provides instructions for AI agents operating in this repository.

## Task Lifecycle & Learning Protocol (Phase 0) - CRITICAL

This protocol is the highest priority and governs the entire lifecycle of every task.

**1. Initialization:**
- On any new task, create a temporary log file (e.g., `.llm/logs/TASK_ID.md`).
- In the log, state the `Objective`, `Initial Plan`, and any `Assumptions`.
- **Crucially, you must read the permanent `docs/agent/project_learnings.md` file. Your plan MUST explicitly address how it will follow the 'Core Principles & Mandates' outlined within it.**

**2. Execution Loop:**
- Before every action, review the `Key Learnings & Constraints` in your current task log.
- After every action, log the command, its outcome, and key observations.
- If an action fails or an assumption is proven wrong, add a new, concise rule to the `Key Learnings & Constraints` section of your task log.
- **0.2.1: The OODA Loop for Debugging:** When an action fails (especially in web scraping), you MUST follow a strict OODA loop.
    - **Observe:** Your first and only action after a failure is to gather evidence. For scraping, this means saving a screenshot and the full page source. You must then analyze this evidence.
    - **Orient:** In your thought process, you must explicitly state your new orientation based *only* on the evidence from the screenshot/HTML. State what you saw and why your previous assumption was wrong.
    - **Decide:** Formulate a *new, single, testable hypothesis*. (e.g., "My new hypothesis is that the correct selector is `...`").
    - **Act:** Implement *only* the change required to test that single hypothesis. Do not add other changes.

**3. Finalization & Learning Persistence:**
- On task completion, review the learnings from your temporary log.
- Append any new, project-specific learnings to the permanent `docs/agent/project_learnings.md` file.
- Use the `save_memory` tool for any new global learnings.
- Delete the temporary log file.

## Core Principles

-   **Be Concise:** Be extremely concise. Sacrifice grammar for the sake of concision.
-   **Preserve Knowledge:** Never delete existing information or learnings from documentation. Knowledge can be updated, altered, and integrated, but it must not be removed. The goal is to build a cumulative, historical record of the project's journey.

## Setup & Execution

-   **Environment:** Use the existing `venv`. Activate with `source venv/bin/activate`.
-   **Dependencies:** Install with `pip install -r requirements.txt`. A `requirements.txt` should be created with `pandas` and `pdfplumber`.
-   **Execution:** The main script is `poc.py`.

## Debugging Methodology

-   **Reflect, Distill, Validate:** Before implementing a fix, follow this process:
    1.  Reflect on 5-7 different possible sources of the problem.
    2.  Distill those down to the 1-2 most likely sources.
    3.  Add temporary logging or debug prints to the code to validate your assumptions about the likely source.
    4.  Only after validating the root cause, proceed with implementing the actual code fix.

## Linting & Formatting

-   **Linter:** Use `ruff` for linting. Run `ruff check .`.
-   **Formatter:** Use `ruff` for formatting. Run `ruff format .`.

## Testing

-   **Framework:** Use `pytest`.
-   **Run all tests:** `pytest`
-   **Run a single test:** `pytest path/to/test_file.py::test_function_name`

## Code Style Guidelines

-   **Imports:** Use `isort` conventions (via `ruff`): sorted alphabetically, grouped by standard library, third-party, and local modules.
-   **Formatting:** Adhere to PEP 8, enforced by `ruff format`.
-   **Types:** Use type hints for all function signatures.
-   **Naming:** Use `snake_case` for variables and functions, `PascalCase` for classes.
-   **Error Handling:** Use `try...except` blocks for file I/O and API calls. Raise specific exceptions where appropriate.

## Project Structure

This project follows a structured layout. Adhere to this structure for all file operations.

-   `phases/`: Contains phase-specific code (completed/ for Phases 1-2, active/ for current Phase 3, shared/ for utilities).
-   `data/`: Contains input data (inputs/ for PDFs, database files).
-   `outputs/`: For all generated output files.
-   `debug/`: Contains debugging scripts and screenshots.
-   `tests/`: For test files.
-   `docs/`: Contains all markdown documentation, plans, and learnings.
-   `.opencode/`: Contains agent definitions.

## Documentation
- **QUICKSTART.md**: Setup and run guide.
- **TROUBLESHOOTING.md**: Common issues and fixes.
- **CHANGELOG.md**: Iterative changes log.
- **GLOSSARY.md**: Key terms.

## Agent System Extension

The project supports dynamic agent loading from `.opencode/agent/`. All agents defined in this folder are available for invocation using the "@" syntax (e.g., "@docs-validation"). This loads and executes the agent's prompt from its .md file.

**Example**: "@docs-validation Review the docs..." will run the docs-validation agent.

If an agent is not found, the system falls back to "general" with the agent's prompt incorporated.

## Custom Agents

This project contains custom agents to assist with development.

### @parser-generator

-   **Location:** `.opencode/agent/parser-generator.md`
-   **Purpose:** This agent is an expert in Python and regular expressions. Its sole task is to generate a robust `parse_description` function for the `pdf_parser.py` script.
-   **How to Use:** This agent should be used as part of the iterative development loop described in `docs/parser-development-plan.md`. When the test harness reveals failing examples of the `BESCHREIBUNG` string, update the agent's prompt with these new examples and invoke it to generate an improved function. The output should then be saved to `phases/shared/_parser_function.py`.

### @docs-validation

-   **Location:** `.opencode/agent/docs-validation.md`
-   **Purpose:** This agent reviews project documentation, summarizes learned information, and adds value through completeness metrics, consistency checks, insights, and link suggestions.
-   **How to Use:** Invoke via `subagent_type: docs-validation` to get a docs-only summary with value-added analysis. Use for doc health checks and session preparation.

## Mandatory AI Coding Directives

All AI agents must adhere strictly to the rules defined in `docs/AI_CODING_DIRECTIVES.md`. These directives are paramount for the project's success and must be integrated into every phase of your work.

**Enforcement and Implementation for AI Agents:**

Before initiating any significant action (e.g., proposing a plan, writing code, making file modifications), you **MUST** internally review your intended actions against the relevant directives. This is a continuous, iterative process.

### **Phase 1: Design & Architect (CRITICAL - Apply BEFORE planning or coding)**
*   **Decompose:** Break down the user's request into a detailed feature plan with clear sub-tasks. Use the `write_todos` tool to track these.
*   **Analyze Context:** Always use `codebase_investigator` for complex tasks or `search_file_content`/`glob` for targeted searches to understand existing architecture, patterns, and data models.
    *   **Prioritize Direct Data Sources (Project Learning):** Before designing any UI automation or web scraper, you MUST first investigate for APIs or direct download links (XLS, CSV). UI automation is the last resort.
*   **Conform to Project Structure (Project Learning):** All new modules must adhere to the established project structure and use a formal, package-based approach for imports. Ad-hoc `sys.path` modifications are forbidden.
*   **Design Data Schema:** For new entities, define clear, normalized schemas.
*   **Design API Contract:** For new services, define explicit, RESTful contracts.
*   **Design for Asynchronicity (BEST PRACTICE):** For long-running tasks, prefer event-driven or message queue patterns.
*   **Design for Scalability (IMPORTANT):** Design services to be stateless for horizontal scaling. Plan caching strategies.

### **Phase 2: Build & Implement (IMPORTANT - Apply DURING coding)**
*   **Search First (DRY):** Before writing new code, use `search_file_content` or `glob` to find and reuse existing components or patterns.
    *   **Consult the Tactical Playbook (Project Learning):** Before solving common problems (e.g., parsing complex Excel files, handling web modals), consult the `.llm/project_learnings.md` document for existing solutions.
*   **Separate Concerns:** Isolate logic (e.g., UI, business, data access) into distinct modules or functions.
*   **Small, Focused Functions (BEST PRACTICE):** Ensure each function performs one clear job.
*   **Analyze Performance:** Be mindful of potential performance bottlenecks (e.g., N+1 queries, excessive memory usage).
*   **Instrument for Observability (IMPORTANT):** Add structured logs for all new services and critical paths.

### **Phase 3: Verify & Secure (CRITICAL - Apply AFTER coding, BEFORE finalizing)**
*   **Write New Tests:** Proactively add unit, integration, and end-to-end tests for all new logic, covering edge cases and failure scenarios. Identify existing test frameworks (e.g., `pytest`) and commands.
    *   **Implement Integration Tests ('Test the Seams') (Project Learning):** In addition to unit tests, you MUST add integration tests that verify the data handoffs between major components.
*   **Handle All Errors:** Implement robust `try...except` blocks for all potential errors, especially I/O operations and external API calls.
*   **Sanitize All Inputs:** Assume all external data is malicious. Implement input sanitization to prevent security vulnerabilities.
*   **Mock External Systems:** In tests, mock all external services for speed and reliability.
*   **Pass CI Gates:** Before considering a task complete, identify and run project-defined linters, formatters, and type-checkers (e.g., `ruff check .`, `ruff format .`, `mypy`).

### **Phase 4: Deliver & Document (IMPORTANT - Apply AFTER verification, BEFORE completion)**
*   **Update Documentation:** If you modify or create a component, update its corresponding API docs, diagrams, and READMEs. Ensure `CHANGELOG.md` is updated for significant changes.
*   **Manage Database Changes (CRITICAL):** For any schema modification, generate a backward-compatible migration script (if applicable to the project's DB setup).
*   **Ensure Backward Compatibility (CRITICAL):** Avoid breaking changes to existing APIs or interfaces.
*   **Use Feature Flags (BEST PRACTICE):** For significant new features, wrap logic in a feature flag (if the project supports it).

**Compliance Checklist (Internal Agent Review - MUST be performed before any final output):**
*   [ ] **Design & Architect:** Have I decomposed the request, analyzed context, and considered schema/API design?
*   [ ] **Build & Implement:** Have I searched for reusable components and separated concerns?
*   [ ] **Verify & Secure:** Have I planned for new tests, error handling, and input sanitization?
*   [ ] **Deliver & Document:** Have I considered documentation updates and backward compatibility?

**Violations of these directives require explicit justification in your thought process.**

## Documentation Guidelines

- **Plan Creation Framework:** For creating plans, include Goal, Challenges, Approach/Tasks, Success Criteria, and Estimated Time. Use phases for multi-step plans (e.g., Phase 3).
- **Debugging/Troubleshooting Integration:** Add debugging steps in plans under "Detailed Steps" (numbered actions, validation, fallbacks). Include troubleshooting in dedicated docs (e.g., TROUBLESHOOTING.md) with Issue, Symptoms, Root Cause, Fix, Prevention.
