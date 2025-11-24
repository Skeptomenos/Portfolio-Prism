# Copilot Instructions for Portfolio-Prism

This document provides essential guidance for AI coding agents working on the Portfolio-Prism repository. Follow these instructions to ensure productivity and adherence to project conventions.

---

## Project Overview
Portfolio-Prism is a Python-based Proof of Concept (POC) for automating portfolio analysis. It processes Trade Republic PDFs to calculate "true exposure" by analyzing ETF holdings and underlying securities.

### Key Phases:
1. **Portfolio Ingestion**: Parse PDFs into trades.
2. **Security Mapping & Pricing**: Map ISINs to tickers and fetch prices.
3. **Holdings Acquisition**: Fetch ETF holdings (currently blocked).
4. **Aggregation**: Calculate true exposure.
5. **End-to-End POC**: Integrate all phases.

---

## Critical Files and Directories
- **`poc.py`**: Main entry point for the pipeline.
- **`phases/`**: Contains completed and active pipeline phases.
  - `completed/`: Phases 1-2 (working production code).
  - `active/`: Phase 3 (adapter integration in progress).
- **`debug/`**: Debugging scripts and saved evidence.
- **`tests/`**: Placeholder for test files (currently empty).
- **`.llm/`**: Logs and persistent learnings for AI agents.

---

## Development Workflow

### Environment Setup
1. Activate the virtual environment:
   ```bash
   source venv/bin/activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Initialize the database:
   ```bash
   python phases/shared/database.py
   ```

### Running the Pipeline
- **Phase 1**: Parse PDFs and calculate positions.
  ```bash
  python phases/completed/pdf_parser.py
  ```
- **Phase 2**: Map securities and fetch prices (requires `OPENFIGI_API_KEY` in `.env`).
  ```bash
  python phases/completed/phase2_pipeline.py
  ```
- **Phase 3**: Fetch ETF holdings (currently blocked).
  ```bash
  python phases/active/holdings_fetcher.py
  ```
- **End-to-End**: Run the full pipeline (requires completed Phase 3).
  ```bash
  python poc.py
  ```

### Testing and Quality
- Linting:
  ```bash
  ruff check .
  ```
- Formatting:
  ```bash
  ruff format .
  ```
- Run tests:
  ```bash
  pytest
  ```

---

## Project-Specific Conventions

### Code Style
- Use type hints for all function signatures.
- Follow `snake_case` for variables/functions and `PascalCase` for classes.
- Organize imports: standard library → third-party → local modules.
- Use `try/except` for I/O and API calls.

### Adapter Pattern
- Adapters for ETF holdings are in `phases/active/adapters/`.
- Each adapter implements `fetch_holdings(ticker: str) -> pd.DataFrame`.
- Proven adapters: `ishares.py`, `xtrackers.py`.
- Incomplete adapters: `amundi.py`, `vaneck.py`.

### Debugging
- Use the Inspector Spike Pattern for web scraping:
  1. Save rendered HTML.
  2. Analyze evidence before guessing selectors.
- Debug scripts are in `debug/` (e.g., `debug_preprocessor.py`).

---

## Known Issues
1. **Phase 3 Integration Blocker**: Proven adapters are not integrated into the pipeline.
2. **Duplicate Function**: `fetch_etf_holdings()` is defined twice in `holdings_fetcher.py`.
3. **Empty Tests**: The `tests/` directory lacks test coverage.
4. **Security**: Ensure `.env` is in `.gitignore`.

---

## Next Steps for AI Agents
1. Read `.llm/project_learnings.md` for critical context.
2. Address quick wins:
   - Fix duplicate function in `holdings_fetcher.py`.
   - Add basic tests to `tests/`.
   - Complete and validate `amundi.py` and `vaneck.py` adapters.
3. Bridge spike scripts in `holdings_engine/` to production adapters.

---

For further details, consult `docs/PROJECT_LEARNINGS.md` and `docs/agent/AI_CODING_DIRECTIVES.md`. Always log learnings to `.llm/project_learnings.md` after completing tasks.