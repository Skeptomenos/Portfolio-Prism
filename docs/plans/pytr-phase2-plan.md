# pytr Integration Phase 2: Deep Integration Plan

> **Status:** Ready for Implementation  
> **Created:** 2025-12-03  
> **Prerequisite:** Phase 1 POC validated (commit f9347f8)

---

## Objective

Transform the manual pytr workflow into a seamless, user-friendly experience integrated into `run.sh`.

**Current (Phase 1):**
```bash
# 3 manual steps
pytr portfolio --output /tmp/pytr_raw.csv
echo "ISIN,Quantity" > data/working/calculated_holdings.csv
tail -n +2 /tmp/pytr_raw.csv | cut -d';' -f2,3 | tr ';' ',' >> data/working/calculated_holdings.csv
python -m scripts.run_pipeline
```

**Target (Phase 2):**
```bash
# 1 command, interactive menu
bash run.sh
# Select [1] API → enter 4-digit code → done
```

---

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Credential source | `.env` with interactive first-run setup | Consolidates all secrets in one place |
| Session persistence | Save cookies to reduce auth prompts | Better UX, less friction |
| Fallback behavior | Fail explicitly, suggest PDF | Clear separation, user decides |
| Integration level | Standalone script + integrated in run.sh | Flexibility for power users |
| Script name | `fetch_tr_api.py` | Clear purpose, matches existing naming |
| Default in run.sh | API (option 1) | Recommended path for TR users |

---

## Implementation Checklist

### Phase 2.1: Dependencies & Configuration

- [ ] **Add pytr to requirements.txt**
  ```
  pytr>=0.4.2
  ```

- [ ] **Update .env.example**
  ```bash
  # Trade Republic API Credentials (for pytr integration)
  # Stored locally, NEVER uploaded or shared.
  TR_PHONE_NO=
  TR_PIN=
  TR_SAVE_SESSION=true
  ```

- [ ] **Verify .gitignore**
  - Confirm `.env` is ignored
  - Confirm `~/.pytr/` is ignored (or document it)

### Phase 2.2: Create `scripts/fetch_tr_api.py`

- [ ] **Credential management**
  - Load from `.env` (TR_PHONE_NO, TR_PIN)
  - If missing: display privacy notice, prompt user, save to `.env`
  - Support `--reconfigure` flag to force update credentials in `.env` (even if they exist)

- [ ] **Privacy notice (first run)**
  ```
  ╔════════════════════════════════════════════════════════════════╗
  ║  TRADE REPUBLIC CREDENTIALS                                    ║
  ╠════════════════════════════════════════════════════════════════╣
  ║  Your phone number and PIN will be stored in .env              ║
  ║  This file is LOCAL ONLY and listed in .gitignore              ║
  ║  Your credentials are NEVER uploaded or shared with anyone.    ║
  ╚════════════════════════════════════════════════════════════════╝
  ```

- [ ] **pytr integration**
  - Use pytr as Python library (not CLI subprocess)
  - Web login with session cookies stored in `~/.pytr/cookies/`
  - Handle 4-digit code prompt interactively

- [ ] **Data conversion**
  - **Auto-backup** previous `calculated_holdings.csv` with timestamp (e.g., `calculated_holdings.2025-12-03_143022.csv.bak`) before overwriting
  - Convert pytr format (semicolon) to pipeline format (comma)
  - Extract only ISIN and quantity columns

- [ ] **Error handling**
  | Error | Message | Suggestion |
  |-------|---------|------------|
  | Invalid credentials | "Authentication failed" | Check TR_PHONE_NO and TR_PIN in .env |
  | Rate limited | "Too many requests" | Wait and retry automatically |
  | Network error | "Connection failed" | Check internet connection |
  | Session expired | "Session expired" | Delete cookies, retry with new code |
  | pytr not installed | "pytr not found" | Run: pip install pytr |

- [ ] **Fallback messaging**
  ```
  ❌ pytr failed: {error}
  
  💡 Alternative: Use PDF export instead
     1. Download 'Kontoauszug' PDF from Trade Republic
     2. Place in data/inputs/portfolio/
     3. Run: bash run.sh (select PDF option)
  ```

- [ ] **Success output**
  ```
  ✅ Fetched 30 positions from Trade Republic
     Total value: €41,729.37
     Saved to: data/working/calculated_holdings.csv
  ```

### Phase 2.3: Update `run.sh`

- [ ] **Interactive menu**
  ```
  ========================================
    Portfolio Prism - True Exposure Tool
  ========================================
  
  How would you like to fetch your portfolio?
  
    [1] Trade Republic API (recommended)
        Fetches live data directly from your TR account
  
    [2] PDF Export
        Uses downloaded 'Kontoauszug' PDFs
  
  Select option [1/2] (default: 1): 
  ```

- [ ] **Option 1: API flow**
  - Run `python scripts/fetch_tr_api.py`
  - On failure: offer fallback to PDF
  - On success: continue to pipeline

- [ ] **Option 2: PDF flow**
  - Run existing PDF parser
  - Continue to pipeline

- [ ] **Pipeline execution**
  - Run `python -m scripts.run_pipeline`
  - Display completion message with dashboard instructions

### Phase 2.4: Update Documentation

- [ ] **README.md**
  - Update Quickstart to show new `run.sh` flow
  - Move PDF instructions to "Alternative" section
  - Add troubleshooting for pytr errors

- [ ] **MVP-plan.md**
  - Mark Phase 2 complete when done

---

## File Changes

| File | Action | Lines Changed (Est.) |
|------|--------|---------------------|
| `scripts/fetch_tr_api.py` | Create | ~200 |
| `run.sh` | Modify | ~50 |
| `requirements.txt` | Modify | +1 |
| `.env.example` | Modify | +5 |
| `README.md` | Modify | ~30 |

---

## Script Structure: `fetch_tr_api.py`

```python
#!/usr/bin/env python3
"""
Fetch portfolio from Trade Republic via pytr API.

Usage:
    python scripts/fetch_tr_api.py              # Normal fetch
    python scripts/fetch_tr_api.py --reconfigure  # Update credentials

First run: Prompts for phone number and PIN, saves to .env
Subsequent runs: Uses saved credentials, may need 4-digit code
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Constants
PROJECT_ROOT = Path(__file__).parent.parent
ENV_FILE = PROJECT_ROOT / ".env"
HOLDINGS_FILE = PROJECT_ROOT / "data/working/calculated_holdings.csv"
BACKUP_DIR = PROJECT_ROOT / "data/working"

def display_privacy_notice():
    """Show privacy notice before collecting credentials."""
    pass

def load_credentials():
    """Load TR_PHONE_NO and TR_PIN from .env."""
    pass

def prompt_and_save_credentials():
    """Prompt user for credentials and save to .env."""
    pass

def backup_holdings():
    """Backup existing calculated_holdings.csv with timestamp if it exists.
    
    Creates: calculated_holdings.YYYY-MM-DD_HHMMSS.csv.bak
    """
    pass

def fetch_portfolio(phone: str, pin: str) -> list:
    """
    Fetch portfolio using pytr library.
    
    Returns list of dicts: [{"isin": "...", "quantity": ...}, ...]
    """
    pass

def save_holdings(positions: list):
    """Save positions to calculated_holdings.csv in pipeline format."""
    pass

def main():
    """Main entry point."""
    # 1. Check for --reconfigure flag
    # 2. Load or prompt credentials
    # 3. Backup existing holdings
    # 4. Fetch portfolio via pytr
    # 5. Convert and save
    # 6. Print summary

if __name__ == "__main__":
    main()
```

---

## run.sh Structure

```bash
#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "========================================"
echo "  Portfolio Prism - True Exposure Tool"
echo "========================================"
echo ""
echo "How would you like to fetch your portfolio?"
echo ""
echo "  [1] Trade Republic API (recommended)"
echo "      Fetches live data directly from your TR account"
echo ""
echo "  [2] PDF Export"
echo "      Uses downloaded 'Kontoauszug' PDFs"
echo ""
# Wait indefinitely for user input (no timeout)
read -p "Select option [1/2] (default: 1): " choice
choice=${choice:-1}

# Activate virtual environment
source venv/bin/activate

if [ "$choice" = "1" ]; then
    echo ""
    echo -e "${GREEN}Fetching portfolio via Trade Republic API...${NC}"
    if python scripts/fetch_tr_api.py; then
        echo ""
    else
        echo ""
        echo -e "${YELLOW}API fetch failed.${NC}"
        read -p "Try PDF export instead? [y/N]: " fallback
        if [[ "$fallback" =~ ^[Yy]$ ]]; then
            python -m scripts.parse_pdfs_to_csv --mode add_new
        else
            echo -e "${RED}Exiting.${NC}"
            exit 1
        fi
    fi
elif [ "$choice" = "2" ]; then
    echo ""
    echo -e "${GREEN}Processing PDF exports...${NC}"
    python -m scripts.parse_pdfs_to_csv --mode add_new
else
    echo -e "${RED}Invalid option. Exiting.${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}Running analysis pipeline...${NC}"
python -m scripts.run_pipeline

echo ""
echo "========================================"
echo -e "${GREEN}Done!${NC}"
echo "View dashboard: ./run_dashboard.sh"
echo "========================================"
```

---

## Testing Plan

### Test Cases

1. **First run (no credentials)**
   - Should display privacy notice
   - Should prompt for phone and PIN
   - Should save to .env
   - Should fetch portfolio successfully

2. **Subsequent run (credentials exist, session valid)**
   - Should use saved credentials
   - Should skip 4-digit code (session cookies)
   - Should fetch portfolio successfully

3. **Session expired**
   - Should prompt for new 4-digit code
   - Should update session cookies
   - Should fetch portfolio successfully

4. **Invalid credentials**
   - Should display clear error
   - Should suggest checking .env
   - Should offer PDF fallback

5. **Network error**
   - Should display connection error
   - Should suggest checking internet
   - Should offer PDF fallback

6. **--reconfigure flag**
   - Should prompt for new credentials
   - Should overwrite existing in .env

7. **run.sh option 1 (API)**
   - Should run fetch_tr_api.py
   - Should continue to pipeline on success

8. **run.sh option 2 (PDF)**
   - Should run PDF parser
   - Should continue to pipeline

9. **run.sh fallback**
   - API fails → prompt for PDF → runs PDF parser

---

## Open Questions (Resolved)

| Question | Decision |
|----------|----------|
| Session cookie location | Store in `~/.pytr/cookies/` directory |
| Backup behavior | Auto-backup previous `calculated_holdings.csv` with timestamp before overwriting |
| run.sh timeout | Wait indefinitely for user input (no timeout) |
| Credential update | Support `--reconfigure` flag to update credentials in `.env` |

---

## Success Criteria

- [ ] `bash run.sh` works end-to-end with API option
- [ ] First-run credential setup is smooth and clear
- [ ] Session persistence reduces 4-digit code prompts
- [ ] Error messages are helpful and actionable
- [ ] PDF fallback works when API fails
- [ ] README accurately describes new workflow

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-03 | Initial plan created |
