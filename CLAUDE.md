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

# Initialize database
python phases/shared/database.py
```

### Running the Pipeline

**Phase 1: PDF Parsing & Position Keeping**
```bash
# Parse PDFs (place PDFs in data/inputs/ first)
python phases/completed/pdf_parser.py

# Test mode (validates parser against known data)
python phases/completed/pdf_parser.py --test

# Calculate positions
python phases/completed/position_keeper.py
```

**Phase 2: Security Mapping & Pricing**
```bash
# Requires OPENFIGI_API_KEY in .env
python phases/completed/phase2_pipeline.py
```

**Phase 3: Holdings Acquisition (BLOCKED)**
```bash
# Current blocker: Run individual adapters but pipeline integration incomplete
# Proven working: iShares and Xtrackers direct downloads
python phases/active/holdings_fetcher.py  # Dispatcher (needs debugging)
```

**End-to-End POC**
```bash
# Requires completed Phase 3 data
python poc.py
```

### Testing & Quality
```bash
# Linting
ruff check .

# Formatting
ruff format .

# Tests (currently empty - KNOWN GAP)
pytest
pytest path/to/test_file.py::test_function_name
```

### Debugging
```bash
# Debug preprocessor (for PDF parsing issues)
python debug/debug_preprocessor.py

# Inspector pattern (for web scraping - creates evidence)
python debug/spike_ishares_inspector.py  # Example
```

## Architecture

### 5-Phase Pipeline
```
Phase 1: Portfolio Ingestion (PDF → trades) ✅
Phase 2: Security Mapping & Pricing (ISIN → ticker → price) ✅
Phase 3: Holdings Ingestion (ETF ticker → holdings CSV/XLSX) 🔴 BLOCKED
Phase 4: Aggregation (Calculate true exposure) ⏸️ Ready
Phase 5: POC Script (End-to-end) ⏸️ Ready
```

### Directory Structure
```
phases/
  completed/     - Phases 1-2 (working production code)
  active/        - Phase 3 (blocked integration)
    adapters/    - Provider-specific scrapers (ishares, xtrackers, amundi, vaneck)
  shared/        - Utilities (database, validation, parser)
data/
  inputs/        - Trade Republic PDFs go here
  portfolio.db   - SQLite DB (14 securities, 0 holdings - empty due to Phase 3)
outputs/         - Generated CSVs (Reports)
holdings_engine/ - Spike scripts (feasibility testing - proven working)
debug/           - Debug scripts, screenshots, saved HTML
.llm/            - Learning persistence and task logs
```

### Critical Files
- `poc.py` - Main entry point (76 lines, orchestrates all phases)
- `phases/shared/database.py` - SQLite schema (securities, holdings, metadata)
- `phases/active/holdings_fetcher.py` - Adapter dispatcher (HAS DUPLICATE FUNCTION BUG lines 29-50 & 53-74)
- `phases/shared/_parser_function.py` - ISIN/name/quantity extraction from descriptions
- `.env` - API keys (ENSURE IN .gitignore - SECURITY CRITICAL)

### Adapter Pattern (Phase 3)
**Dispatcher**: `holdings_fetcher.py` routes ticker → adapter via `PROVIDER_ADAPTER_MAP`

**Adapters**: Each in `phases/active/adapters/`
- `ishares.py` - Layer 1 (direct CSV download) - ✅ PROVEN VIABLE
- `xtrackers.py` - Layer 1 (direct download) - ✅ PROVEN VIABLE
- `amundi.py` - Layer 3 (Selenium) - ⚠️ Incomplete/untested
- `vaneck.py` - Layer 3 (Selenium) - ⚠️ Incomplete/untested

**Interface**: Each adapter exports `fetch_holdings(ticker: str) -> pd.DataFrame` with columns: `ticker`, `name`, `weight_percentage`

### Database Schema
**Securities Table**: `isin` (PK), `name`, `ticker`, `provider`, `asset_type`, `exchange`, `sector`, `links`, `price`, `last_updated`

**Holdings Table**: `isin` (FK), `holding_ticker`, `holding_name`, `weight_percentage`, `last_updated`

**Current State**: 14 securities, 0 holdings (empty - Phase 3 blocker)

## Known Issues

### Critical
1. **Phase 3 Integration Blocker**: Spike scripts in `holdings_engine/` successfully download holdings, but production adapters in `phases/active/adapters/` don't populate database. Root cause: disconnect between proven spikes and production pipeline.
2. **Duplicate Function**: `fetch_etf_holdings()` defined twice in `holdings_fetcher.py:29-50` and `:53-74`
3. **No Tests**: Empty `tests/` directory despite `pytest` in requirements
4. **Security**: Verify `.env` in `.gitignore` (contains real API keys)

### Moderate
5. **Untested Adapters**: Amundi and VanEck never validated with Inspector Spike
6. **Documentation Conflicts**: Multiple competing plans (needs deprecation per feedback)
7. **Incomplete Migration**: Root-level test files not in `tests/` directory

## Import System (CRITICAL)

**Single Entry Point Rule**: Python import system requires running from project root. All execution originates from `poc.py` at root level.

**Correct sys.path Setup** (already in `poc.py`):
```python
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
```

**DO NOT** run scripts from subdirectories - causes unsolvable import errors.

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
