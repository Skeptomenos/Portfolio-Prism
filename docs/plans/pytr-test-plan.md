# pytr Integration Test Plan

> **Status:** Ready for Testing  
> **Created:** 2025-12-03  
> **Objective:** Validate pytr as alternative input method to PDF parsing

---

## Overview

This test plan validates using [pytr](https://github.com/pytr-org/pytr) to fetch portfolio data directly from Trade Republic's API, replacing the current PDF parsing workflow.

### Why pytr?

| Current (PDF) | With pytr |
|---------------|-----------|
| Download PDF manually | Run single command |
| Parse German text with regex | Get structured data via API |
| Calculate holdings from transactions | Get current holdings directly |
| ~30 seconds processing | ~5 seconds API call |

### Risk Assessment

- **API Stability:** Unofficial API, could break if TR changes endpoints
- **Mitigation:** Keep PDF parsing as fallback (already implemented)
- **Decision:** Risk accepted for POC testing

---

## Prerequisites

### 1. Install pytr

```bash
cd /Users/davidhelmus/Repos/portfolio-master/POC
source venv/bin/activate
pip install pytr
```

### 2. Have Ready

- [ ] Trade Republic phone number (format: `+49XXXXXXXXX`)
- [ ] Trade Republic PIN (4 digits)
- [ ] Access to Trade Republic app (for 4-digit verification code)

---

## Test Procedure

### Step 1: Backup Current Data

```bash
cd /Users/davidhelmus/Repos/portfolio-master/POC

# Backup current holdings
cp data/working/calculated_holdings.csv data/working/calculated_holdings.csv.backup.pre_pytr

# Verify backup
ls -la data/working/calculated_holdings.csv*
```

### Step 2: Login to Trade Republic

```bash
# Replace with your actual phone number and PIN
pytr login --phone_no +49XXXXXXXXX --pin XXXX
```

**Expected behavior:**
1. pytr will initiate web login
2. You'll receive a 4-digit code in your Trade Republic app (or via SMS)
3. Enter the code when prompted
4. Login successful message

**Troubleshooting:**
- If login fails, try again (first attempt sometimes fails)
- If you get "device reset" prompt, choose web login (keeps phone logged in)

### Step 3: Fetch Portfolio

```bash
# Fetch portfolio to temporary file
pytr portfolio --output /tmp/pytr_raw.csv

# Check what we received
echo "=== Raw pytr output ==="
cat /tmp/pytr_raw.csv

echo ""
echo "=== Row count ==="
wc -l /tmp/pytr_raw.csv
```

**Expected output format:**
```csv
Name;ISIN;quantity;price;avgCost;netValue
iShares Core MSCI World;IE00B4L5Y983;119.062305;109.54;85.23;13041.49
...
```

**Verify:**
- [ ] File contains your positions
- [ ] ISIN column has valid ISINs
- [ ] quantity column has your share counts
- [ ] Row count matches your expected position count (~30 positions)

### Step 4: Convert to Pipeline Format

```bash
# Convert pytr output to our format
# - Extract ISIN (column 2) and quantity (column 3)
# - Change delimiter from semicolon to comma
# - Rename 'quantity' to 'Quantity' via header replacement

echo "ISIN,Quantity" > data/working/calculated_holdings.csv
tail -n +2 /tmp/pytr_raw.csv | cut -d';' -f2,3 | tr ';' ',' >> data/working/calculated_holdings.csv

# Verify conversion
echo "=== Converted output ==="
head -10 data/working/calculated_holdings.csv

echo ""
echo "=== Row count (should match pytr output minus header) ==="
wc -l data/working/calculated_holdings.csv
```

**Expected output:**
```csv
ISIN,Quantity
IE00B4L5Y983,119.062305
IE00B3WJKG14,250.847462
...
```

### Step 5: Compare with Backup

```bash
# Compare position counts
echo "=== Position count comparison ==="
echo "Backup (PDF-derived):" $(tail -n +2 data/working/calculated_holdings.csv.backup.pre_pytr | wc -l)
echo "pytr (API-derived):  " $(tail -n +2 data/working/calculated_holdings.csv | wc -l)

# Compare ISINs
echo ""
echo "=== ISINs only in backup (missing from pytr) ==="
comm -23 <(cut -d',' -f1 data/working/calculated_holdings.csv.backup.pre_pytr | sort) \
         <(cut -d',' -f1 data/working/calculated_holdings.csv | sort)

echo ""
echo "=== ISINs only in pytr (new positions) ==="
comm -13 <(cut -d',' -f1 data/working/calculated_holdings.csv.backup.pre_pytr | sort) \
         <(cut -d',' -f1 data/working/calculated_holdings.csv | sort)
```

**Expected:**
- Position counts should be similar (may differ if you traded recently)
- Same ISINs should appear in both files
- Quantities may differ due to:
  - Trades since last PDF export
  - Rounding differences (pytr uses 6 decimals)

### Step 6: Run Pipeline

```bash
# Run the pipeline with pytr-derived holdings
python -m scripts.run_pipeline
```

**Expected:**
- Pipeline should complete successfully
- Should skip PDF parsing (no PDFs needed)
- Should generate reports in `outputs/`

**Watch for:**
- [ ] No errors during execution
- [ ] Portfolio value looks reasonable
- [ ] ETF decomposition works

### Step 7: Verify Dashboard

```bash
# Start dashboard
./run_dashboard.sh
```

Open http://localhost:8501 and verify:
- [ ] Portfolio value displays correctly
- [ ] All positions appear
- [ ] True exposure calculation works
- [ ] No obvious errors or missing data

### Step 8: Validate Results (Optional)

```bash
# Run validation against ground truth
python3 scripts/validate_portfolio.py
```

**Expected:**
- Most positions should PASS (within 2% of ground truth)
- Any WARN/FAIL positions should be investigated

---

## Success Criteria

| Criteria | Target | How to Verify |
|----------|--------|---------------|
| pytr login works | Success | No auth errors |
| Portfolio fetch returns data | All positions | Row count matches expected |
| Format conversion works | Valid CSV | Pipeline reads without error |
| Pipeline completes | No errors | Exit code 0 |
| Dashboard loads | All tabs work | Visual inspection |
| Position count matches | ±2 positions | Compare with backup |
| Portfolio value reasonable | ±5% of GT | Check dashboard total |

---

## Rollback Procedure

If testing fails, restore the backup:

```bash
cp data/working/calculated_holdings.csv.backup.pre_pytr data/working/calculated_holdings.csv
```

---

## Post-Test Actions

### If Test Succeeds

1. Document any differences between pytr and PDF-derived data
2. Create convenience script for pytr workflow
3. Update README with pytr as recommended method
4. Consider adding pytr to requirements.txt

### If Test Fails

1. Document failure mode and error messages
2. Check pytr GitHub issues for known problems
3. Fall back to PDF workflow
4. Reassess integration approach

---

## Convenience Script (For After Successful Test)

If testing succeeds, create this script for future use:

**File:** `scripts/fetch_tr.sh`
```bash
#!/bin/bash
# Fetch portfolio from Trade Republic via pytr
# Usage: ./scripts/fetch_tr.sh

set -e

echo "Fetching portfolio from Trade Republic..."
pytr portfolio --output /tmp/pytr_raw.csv

echo "Converting to pipeline format..."
echo "ISIN,Quantity" > data/working/calculated_holdings.csv
tail -n +2 /tmp/pytr_raw.csv | cut -d';' -f2,3 | tr ';' ',' >> data/working/calculated_holdings.csv

echo "Done! Fetched $(tail -n +2 data/working/calculated_holdings.csv | wc -l) positions."
echo ""
echo "Run pipeline with: python -m scripts.run_pipeline"
```

---

## Data Format Reference

### pytr Output
```
Name;ISIN;quantity;price;avgCost;netValue
```
- Delimiter: Semicolon (`;`)
- Columns: 6
- Quantity precision: 6 decimals

### Pipeline Input
```
ISIN,Quantity
```
- Delimiter: Comma (`,`)
- Columns: 2
- Quantity precision: Any (6 sufficient)

### Conversion Command
```bash
echo "ISIN,Quantity" > output.csv
tail -n +2 pytr_raw.csv | cut -d';' -f2,3 | tr ';' ',' >> output.csv
```

---

## Notes

- pytr stores credentials in `~/.pytr/credentials`
- Session cookies can be saved with `--save-cookies` flag
- Web login keeps you logged in on phone app
- App login (device reset) would log you out of phone

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-03 | Initial test plan created |
