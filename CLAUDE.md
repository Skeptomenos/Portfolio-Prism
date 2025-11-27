# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## ⚠️ READ THESE FILES FIRST (MANDATORY)

Before starting ANY task, read in this exact order:

1. **`.context/active_state.md`** ← CRITICAL state file (read FIRST)
2. **`.context/handover.md`** ← Continuity file (read if active state is empty)
3. **`docs/PROJECT_LEARNINGS.md`** ← Permanent constraints
4. **`docs/agent/AI_CODING_DIRECTIVES.md`** ← The v2 Methodology (Phase 0-4)
5. **`docs/agent/CODING_STANDARDS.md`** ← Style, Security, & Testing Rules
6. **`CLAUDE.md`** ← Tool reference

**Why this order matters:**
- State files (`.context/*`) ensure you pick up exactly where the previous agent left off.
- `AI_CODING_DIRECTIVES.md` defines the mandatory workflow.
- `CODING_STANDARDS.md` ensures your code passes quality gates (Linting, Typing, Security).
- `PROJECT_LEARNINGS.md` contains the domain constraints you must obey.

**Skipping these files will result in a loss of context and violation of project mandates.**

---

## Claude Code Tool Reference

When universal patterns say "search codebase", "read file", "create task list", use these tools:

| Abstract Instruction | Claude Code Tool |
|---------------------|------------------|
| Create/update task list | `TodoWrite` |
| Read file | `Read` |
| Write file (create/overwrite) | `Write` |
| Edit file (find/replace) | `Edit` |
| Find files by pattern | `Glob` |
| Search file contents (regex) | `Grep` |
| Execute shell command | `Bash` |
| Explore codebase (complex) | `Task` with `subagent_type="Explore"` |
| Multi-step research | `Task` with `subagent_type="general-purpose"` |
| Fetch web content | `WebFetch` |
| Search web | `WebSearch` |

**Task Logs Location**: `.llm/logs/claude/TASK_ID.md`

---

## Project Overview

Portfolio Look-Through Analyzer - A Python POC automating portfolio analysis from Trade Republic PDFs to "true exposure" calculation by looking through ETF holdings to underlying securities.

**Current Status**: Phases 1-2 complete (PDF parsing, position tracking, ISIN mapping, pricing). Phase 3 (ETF holdings acquisition) blocked - proven adapters exist but not integrated into pipeline.

## Critical Operating Rules

### Before Any Task: Read Project Memory
**MANDATORY**: Read `.llm/project_learnings.md` before starting ANY task. Contains critical learnings including:
- "Free API Fallacy" - No free APIs for ETF holdings data
- "Scraper's Blindness" & OODA Loop - Evidence-based debugging (Observe → Orient → Decide → Act)
- Adapter Pattern is essential for heterogeneous data sources
- Inspector Spike Pattern - Save rendered HTML before debugging scrapers
- Hierarchy of scraping: Direct download → API interception → UI automation

### Task Lifecycle Protocol (Phase 0)
1. **Init**: Create temp log `.llm/logs/TASK_ID.md` with Objective, Plan, Assumptions
2. **Execute**: Log all commands and outcomes; on failure, add learning to log
3. **Finalize**: Persist learnings to `.llm/project_learnings.md`, delete temp log

### OODA Loop for Debugging (CRITICAL for Web Scraping)
On any failure:
1. **Observe**: Save screenshot + full page source (do NOT guess)
2. **Orient**: Analyze evidence, state why assumption was wrong
3. **Decide**: Formulate ONE testable hypothesis
4. **Act**: Test that single hypothesis only

### 4-Phase Enforcement
**Phase 1 - Design**: Decompose task, analyze context (search existing code), design schemas
**Phase 2 - Build**: Search for reusable components (DRY), separate concerns, small functions
**Phase 3 - Verify**: Write tests, handle errors, run linters (`ruff check .`, `ruff format .`)
**Phase 4 - Document**: Update CHANGELOG.md, ensure backward compatibility

## Development Commands

### Environment Setup
```bash
# Activate virtual environment (ALWAYS first step)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Running the Pipeline

**Full Pipeline (PDFs + Analysis)**
```bash
# Runs legacy DB setup + Core Pipeline
./run.sh
```

**Core Analysis Pipeline Only**
```bash
# Skips PDF parsing, runs logic on existing data
python -m scripts.run_pipeline
```

**PDF Parsing (Modern CSV Mode)**
```bash
# Incrementally parses PDFs to CSV
python -m scripts.parse_pdfs_to_csv --mode add_new

# Preview changes without saving
python -m scripts.parse_pdfs_to_csv --mode dry_run
```

**Phase 2: Security Mapping & Pricing**
```bash
# (Integrated into run_pipeline, but can be managed manually)
python -m scripts.manage_assets
```

### Testing & Quality
```bash
# Linting
ruff check .

# Formatting
ruff format .

# Tests
pytest
```

### Debugging
```bash
# Inspector pattern (for web scraping - creates evidence)
python debug/inspect_amundi.py
```

## Architecture

### Directory Structure
```
src/             - Main source code
  adapters/      - Provider-specific scrapers (ishares, xtrackers, etc.)
  core/          - Business logic (aggregation, reporting)
  data/          - Data access (market, state_manager)
  pdf_parser/    - PDF extraction logic
  utils/         - Shared utilities (logging, schemas)
config/          - Configuration files (JSON, CSV)
scripts/         - Executable scripts (entry points)
data/            - Input/Output data
  inputs/        - Trade Republic PDFs
  true_data/     - Source of Truth CSVs
  working/       - Intermediate files
outputs/         - Generated Reports
debug/           - Debug scripts & artifacts
docs/            - Documentation
```

### Critical Files
- `scripts/run_pipeline.py` - Main orchestration script
- `src/data/state_manager.py` - Loads portfolio state
- `src/pdf_parser/parser.py` - Core parsing logic
- `config/adapter_registry.json` - Maps ISINs to Adapters
- `.env` - API keys (ENSURE IN .gitignore - SECURITY CRITICAL)

### Import System (CRITICAL)

**Module Execution Rule**: Python import system requires running scripts as modules from the project root.
- **Correct**: `python -m scripts.run_pipeline`
- **Incorrect**: `python scripts/run_pipeline.py` (Will cause `ModuleNotFoundError`)

**sys.path**: The `run.sh` script automatically sets `PYTHONPATH=.`.

## Web Scraping Strategy

### Hierarchy of Techniques (Prefer simpler first)
1. **Layer 1**: Direct file download via `requests` (simplest, most reliable)
2. **Layer 2**: API interception via `selenium-wire` (moderate complexity)
3. **Layer 3**: Full UI automation via `selenium` + `undetected-chromedriver` (complex, fragile)

### Inspector Spike Pattern (For Layer 2-3)
Before debugging scraper failures:
1. Create dedicated inspector script
2. Load page and save complete rendered HTML
3. Analyze saved HTML to find correct selectors
4. NEVER guess selectors - always use evidence

### Anti-Bot Measures
- Standard Selenium detected by Cloudflare (confirmed via error screenshots)
- Use `undetected-chromedriver` for Layer 3
- Prioritize Layer 1 (direct downloads) to avoid anti-bot entirely

### Embedded JSON Technique (SPAs)
Modern financial sites embed data in `<script>` tags (e.g., `window.__NUXT__`):
1. Use headless browser for fully-rendered HTML
2. Extract JSON from script tag
3. Parse JSON directly (more robust than HTML scraping)

## PDF Parsing Architecture

### Multi-Page Handling
- **Anchor pages** (page 0): Find "UMSATZÜBERSICHT" text for y0
- **Continuation pages**: Use y0=0 (no header)
- Always check header presence per page

### German Number Format
```python
# Remove thousands separator, replace decimal comma
amount = amount_str.replace(".", "").replace(",", ".")
```

### Targeted Extraction (vs. Generic Table Tools)
1. Use `pdfplumber` to find visual anchor text
2. Define precise bounding box via anchor coordinates
3. Extract words + coordinates from cropped region only
4. Avoids errors from multi-table PDFs

## Translation Layer

PDFs in German → Stored in English for adaptability
- Headers: `HEADER_MAPPING` dict in `pdf_parser.py`
- Types: `TYPE_MAPPING` dict
- Uses `deep_translator` with fallback to original text

## Development Patterns

### "Before/After" Debug Views
For complex preprocessing logic:
1. Create isolated debug script
2. Print "Before" (raw input) and "After" (processed output)
3. Iterate until "After" is correct
4. Copy working logic to production

Example: `debug/debug_preprocessor.py` for PDF line grouping

### Feasibility Spikes
Before building full architecture:
1. Run small focused spike to prove core challenge solvable
2. Replace assumptions with facts
3. Example: `holdings_engine/spike_*.py` scripts

### Validation Automation
Standard pipeline step (see `phases/shared/validation.py`):
- Count comparisons (input vs. output)
- Field integrity checks
- Automated reports to `outputs/validation_report.txt`

## Configuration Files

### .env (REQUIRED - KEEP SECRET)
```
OPENFIGI_API_KEY="your_key"  # Required for Phase 2
# yfinance is free, no key needed
```

### requirements.txt
Core dependencies: `pandas`, `pdfplumber`, `openfigi`, `yfinance`, `selenium`, `undetected-chromedriver`, `beautifulsoup4`, `pytest`, `ruff`, `deep_translator`

## Performance Benchmarks
- PDF parsing: ~5s (45 trades)
- ISIN mapping: ~2s (14 ISINs via OpenFIGI)
- Price fetching: ~10s (14 tickers via yfinance with retries)
- Total Phase 2 pipeline: ~20s

## Documentation
- `QUICKSTART.md` - 10-minute setup guide
- `TROUBLESHOOTING.md` - Common issues and fixes
- `CHANGELOG.md` - 58 iteration entries with pivot points
- `GLOSSARY.md` - Domain terminology
- `poc-project-plan.md` - Master plan with current status
- `phase3-feedback.md` - Critical review of competing strategies
- `.llm/project_learnings.md` - **MUST READ FIRST** - Permanent learnings

## Custom Agents (OpenCode)
- `@parser-generator` - Generates `parse_description()` function for PDF parser
- `@docs-validation` - Reviews documentation for completeness and consistency

## Code Style
- Type hints for all function signatures
- `snake_case` for variables/functions, `PascalCase` for classes
- Try/except for I/O and API calls
- Imports: standard lib → third-party → local (via `ruff`)
- PEP 8 enforced by `ruff format`

## Next Session Handoff
1. Activate venv: `source venv/bin/activate`
2. Read: `.llm/project_learnings.md` (mandatory)
3. Review: `CHANGELOG.md` for recent changes
4. Current blocker: Phase 3 integration - bridge spike scripts to production adapters
5. Quick wins: Fix duplicate function, add basic tests, complete Amundi/VanEck adapters

## Completion Estimate
5-8 days focused development:
1. Bridge spikes → production (1-2 days)
2. Debug holdings DB population (1 day)
3. Add test coverage (1 day)
4. Complete/validate Amundi & VanEck (2-3 days)
5. End-to-end validation (1 day)
