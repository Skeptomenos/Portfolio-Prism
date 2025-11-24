# Handover: 2025-11-24 - Codebase Modernization

## Executive Summary
We have transformed the codebase from a "Script Collection" to a **Standard Python Package**. The project now uses `pyproject.toml`, centralized configuration (`src/config.py`), and modular adapters. The "Amundi Monolith" has been refactored into testable components.

## Current State (Green)
- **Packaging:** Project is installed via `pip install -e .`. No more `sys.path` hacks.
- **Config:** All paths are in `src/config.py`.
- **Quality:** Core modules (`aggregation`, `enrichment`) have Type Hints.
- **Tests:** All tests pass (`pytest`). Legacy tests were removed.

## Architecture Changes
1.  **`pyproject.toml`**: Defines dependencies and package structure.
2.  **`src/config.py`**: Single source of truth for file paths.
3.  **`src/adapters/amundi.py`**: Split into `_fetch_manual`, `_fetch_selenium`, `_parse_downloaded`.

## Immediate Next Steps
1.  **Revive Automation:** The PDF Parser (`scripts/setup_db.py`) is still disconnected from the CSV state (as noted in previous handover).
2.  **Enhance Universe:** Add CLI for `asset_universe.csv` management.

## Command to Run
```bash
source venv/bin/activate
pip install -e .  # Ensure package is installed
python scripts/run_pipeline.py
```
