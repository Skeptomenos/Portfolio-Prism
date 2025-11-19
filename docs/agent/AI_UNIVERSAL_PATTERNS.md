# AI Universal Patterns (All Platforms)

**Applies to:** OpenCode, Claude Code, Gemini CLI, and all AI agents

**Purpose:** Tool-agnostic methodology that all AI agents must follow, regardless of platform.

---

## Task Lifecycle & Learning Protocol (Phase 0) - CRITICAL

This protocol is the highest priority and governs the entire lifecycle of every task.

### **1. Initialization**

On any new task:
- **Create temporary log file**: `.llm/logs/{platform}/TASK_ID.md`
  - `{platform}` = `claude`, `gemini`, or `opencode`
  - `TASK_ID` = descriptive name (e.g., `fix-phase3-integration`)
- **In the log, state:**
  - **Objective**: What needs to be accomplished
  - **Initial Plan**: How you intend to solve it
  - **Assumptions**: What you believe to be true
- **MANDATORY**: Read `.llm/project_learnings.md` to inform your plan

### **2. Execution Loop**

During task execution:
- **Before every action**: Review "Key Learnings & Constraints" in your task log
- **After every action**: Log the command, outcome, and observations
- **On failure**: Add a new, concise rule to "Key Learnings & Constraints"
- **Follow OODA Loop** (see below) for debugging

### **3. Finalization & Learning Persistence**

On task completion:
- Review learnings from temporary log
- Append **new, project-specific learnings** to `.llm/project_learnings.md`
- Use your platform's memory tool if available
- Delete the temporary log file

---

## OODA Loop for Debugging (CRITICAL)

When an action fails (especially in web scraping), you MUST follow this strict loop:

### **Observe** (Evidence Gathering)
Your **first and only action** after failure:
- Save a screenshot (if UI-related)
- Save the full page source (if web scraping)
- Capture error output completely
- **DO NOT GUESS** - gather evidence first

### **Orient** (Analysis)
In your thought process, explicitly state:
- What the evidence shows
- Why your previous assumption was wrong
- What you learned from the screenshot/HTML/error

### **Decide** (Hypothesis Formation)
Formulate a **single, new, testable hypothesis**
- Example: "My new hypothesis is that the correct selector is `div.holdings-table`"
- **Only ONE hypothesis** - not multiple changes at once

### **Act** (Minimal Test)
Implement **only** the change required to test that hypothesis
- Do not add other changes
- Test the single hypothesis
- Return to Observe if it fails

**Anti-Pattern**: Guessing multiple changes simultaneously breaks the OODA loop and creates debugging chaos.

---

## Debugging Methodology: Reflect, Distill, Validate

Before implementing any fix, follow this process:

1. **Reflect** (Divergent Thinking)
   - List 5-7 different possible sources of the problem
   - Consider edge cases, assumptions, data quality, API issues

2. **Distill** (Convergent Thinking)
   - Narrow down to 1-2 most likely sources
   - Prioritize by probability and impact

3. **Validate** (Evidence-Based Confirmation)
   - Add temporary logging or debug prints
   - Gather evidence to confirm the root cause
   - **Only after validation**, proceed with the fix

4. **Fix** (Targeted Implementation)
   - Implement the minimal fix
   - Remove temporary debug code
   - Verify the fix resolves the issue

---

## 4-Phase Enforcement (CRITICAL)

All AI agents must follow this 4-phase checklist for every significant task.

### **Phase 1: Design & Architect** (Apply BEFORE planning or coding)

**Decompose:**
- Break down request into detailed feature plan with sub-tasks
- Use your platform's task management tool
- Create clear, actionable items

**Analyze Context:**
- Search existing codebase for similar patterns
- Use file search to find reusable components
- Understand existing architecture before writing new code
- **DRY Principle**: Don't Repeat Yourself

**Design Data Schema:**
- For new entities, define clear, normalized schemas
- Document table structures, foreign keys, indexes

**Design API Contract:**
- For new services, define explicit contracts
- Specify inputs, outputs, error handling

**Design for Asynchronicity:** (Best Practice)
- For long-running tasks, prefer event-driven patterns
- Consider message queues for background processing

**Design for Scalability:** (Important)
- Design stateless services for horizontal scaling
- Plan caching strategies (DB, API results)

### **Phase 2: Build & Implement** (Apply DURING coding)

**Search First:**
- Before writing new code, search for existing components
- Reuse patterns, utilities, and modules
- Maintain consistency with existing codebase

**Separate Concerns:**
- Isolate logic layers (UI, business, data access)
- Use distinct modules or functions
- Single Responsibility Principle

**Small, Focused Functions:** (Best Practice)
- Each function performs one clear job
- Easy to test, understand, and maintain
- Typical size: 10-30 lines

**Analyze Performance:**
- Be mindful of N+1 queries
- Avoid excessive memory usage
- Consider algorithmic complexity

**Instrument for Observability:** (Important)
- Add structured logs for critical paths
- Log entry/exit of complex functions
- Include context (IDs, timestamps, states)

### **Phase 3: Verify & Secure** (Apply AFTER coding, BEFORE finalizing)

**Write Tests:**
- Proactively add unit tests for new logic
- Cover edge cases and failure scenarios
- Add integration tests for multi-component features
- This project uses `pytest`

**Handle All Errors:**
- Implement `try...except` blocks for I/O operations
- Handle external API failures gracefully
- Raise specific exceptions, not generic ones
- Provide helpful error messages

**Sanitize All Inputs:**
- Assume all external data is potentially malicious
- Validate data types, ranges, formats
- Prevent SQL injection, XSS, command injection

**Mock External Systems:**
- In tests, mock external APIs and services
- Ensures tests are fast and reliable
- Reduces dependency on external availability

**Pass CI Gates:**
- Run linters: `ruff check .`
- Run formatters: `ruff format .`
- Run tests: `pytest`
- Fix all errors before considering task complete

### **Phase 4: Deliver & Document** (Apply AFTER verification, BEFORE completion)

**Update Documentation:**
- Update `CHANGELOG.md` for significant changes
- Update component docs if APIs changed
- Update README if setup/usage changed

**Manage Database Changes:** (Critical)
- For schema modifications, document the change
- Consider backward compatibility
- Note migration requirements

**Ensure Backward Compatibility:** (Critical)
- Avoid breaking changes to existing APIs
- Deprecate before removing
- Version APIs if breaking changes necessary

---

## Compliance Checklist (Self-Review)

Before any final output, confirm:

- [ ] **Design & Architect**: Have I decomposed the request, analyzed context, and designed schemas?
- [ ] **Build & Implement**: Have I searched for reusable components and separated concerns?
- [ ] **Verify & Secure**: Have I planned tests, error handling, and input sanitization?
- [ ] **Deliver & Document**: Have I updated documentation and ensured backward compatibility?

**Violations of these directives require explicit justification in your thought process.**

---

## Core Principles

### **Be Concise**
- Extremely concise communication
- Sacrifice grammar for brevity when appropriate
- Focus on actionable information

### **Preserve Knowledge**
- **Never delete** existing information or learnings from documentation
- Knowledge can be updated, altered, integrated, but not removed
- Goal: Build cumulative, historical record of project journey
- Exception: Deprecate outdated docs by moving to `docs/archive/`

### **Evidence Over Assumptions**
- Gather evidence before making decisions
- Use Inspector Spike pattern (see project learnings)
- Save screenshots, HTML sources, error logs
- Analyze evidence before formulating hypotheses

### **Iterative Improvement**
- Small, focused changes over large rewrites
- Test after each change
- Validate assumptions continuously
- Fail fast, learn fast

---

## Project-Specific Patterns

These patterns are specific to this portfolio analyzer project. See `.llm/project_learnings.md` for detailed explanations.

### **Inspector Spike Pattern** (Web Scraping)

Before debugging scraper failures:
1. Create dedicated inspector script (e.g., `debug/spike_amundi_inspector.py`)
2. Load the page with Selenium
3. Save complete rendered HTML to file (e.g., `outputs/amundi_page_source.html`)
4. Save screenshot (e.g., `outputs/amundi_screenshot.png`)
5. Analyze saved files to find correct selectors
6. Update scraper with validated selectors

**Never guess selectors - always use evidence.**

### **Feasibility Spike Pattern** (Risk Reduction)

Before building full architecture:
1. Identify risky technical assumption (e.g., "Can we download iShares holdings?")
2. Create small, focused spike script (e.g., `holdings_engine/spike_ishares_direct.py`)
3. Test only that assumption (no architecture, no polish)
4. Gather evidence (save outputs, screenshots)
5. If successful, build production version
6. If failed, try alternative approach

**Philosophy**: Replace assumptions with facts early.

### **"Before/After" Debug Views** (Complex Logic)

For complex preprocessing logic:
1. Create isolated debug script (e.g., `debug/debug_preprocessor.py`)
2. Print "Before" (raw input data)
3. Apply transformation logic
4. Print "After" (processed output)
5. Compare visually to identify bugs
6. Iterate until "After" is correct
7. Copy working logic to production

**Makes invisible bugs visible.**

### **Validation Automation** (Data Pipelines)

Every data pipeline step should:
1. Define validation rules (count comparisons, field integrity)
2. Implement in `phases/shared/validation.py`
3. Run automatically after each step
4. Generate report: `outputs/validation_report.txt`
5. Fail fast if validation fails

**Catches silent failures, prevents manual checking.**

---

## Web Scraping Hierarchy

**Layer 1: Direct File Download** (Simplest, Most Reliable)
- Use HTTP library to download file from stable URL
- Parse file locally (CSV, XLSX)
- ✅ Fast, no anti-bot issues, stable
- ❌ Requires predictable URL pattern

**Layer 2: API Interception** (Moderate Complexity)
- Use browser automation with network interception
- Extract JSON from concealed APIs
- ✅ More reliable than HTML scraping
- ❌ Requires page to make API calls

**Layer 3: Full UI Automation** (Complex, Fragile)
- Use browser automation to navigate UI
- Click elements, extract data
- ✅ Works when no other option exists
- ❌ Slow, fragile, anti-bot detection risk

**Always attempt Layer 1 first, only escalate if necessary.**

---

## Code Style Guidelines

### **Imports**
- Use `isort` conventions (via `ruff`)
- Sorted alphabetically
- Grouped: standard library → third-party → local modules

### **Formatting**
- Adhere to PEP 8
- Enforced by `ruff format`
- Line length: 88 characters

### **Type Hints**
- Use type hints for all function signatures
- Example: `def fetch_holdings(ticker: str) -> pd.DataFrame:`

### **Naming Conventions**
- Variables and functions: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Private members: `_leading_underscore`

### **Error Handling**
- Use `try...except` blocks for I/O and API calls
- Raise specific exceptions where appropriate
- Provide context in error messages

---

## Anti-Patterns to Avoid

❌ **Guess and Check**: Making random changes without evidence
❌ **Shotgun Debugging**: Changing multiple things at once
❌ **Copy-Paste Coding**: Duplicating code instead of extracting utilities
❌ **Premature Optimization**: Optimizing before measuring
❌ **Documentation Deletion**: Removing historical knowledge
❌ **Blind Editing**: Editing files without reading them first
❌ **Assumption-Based Planning**: Not reading project learnings before starting

---

**Last Updated**: 2025-11-16
**Version**: 1.0
**Status**: Active for Claude Code (testing), not yet deployed to OpenCode or Gemini CLI
