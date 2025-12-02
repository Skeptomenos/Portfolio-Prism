# [Project Name]

> **Root File:** Auto-loaded by AI CLI tools. Keep concise (<80 lines).

## Overview

[2-3 sentences: What is this? What problem does it solve?]

## Tech Stack

- **Language:** [e.g., Python 3.11+]
- **Framework:** [e.g., FastAPI]
- **Database:** [e.g., PostgreSQL]

## Structure

```
src/           # Source code
tests/         # Tests
docs/specs/    # Specifications
.context/      # AI session state
coding/        # AI framework
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
# Build: [cmd]    Test: [cmd]    Lint: [cmd]    Run: [cmd]
```

## Constraints

- [Project-specific constraint 1]
- [Project-specific constraint 2]

## State Files

`.context/active_state.md` (current) | `.context/handover.md` (previous) | `docs/specs/tasks.md` (plan)
