# POC to MVP Migration Plan

> **Status:** Phase 1 Complete (pytr POC validated)  
> **Last Updated:** 2025-12-03  
> **Goal:** Enable friends & family to test the tool with minimal friction

---

## Current State (POC)

### What Works
- Full pipeline: PDF parsing → ETF decomposition → True Exposure calculation
- 11 ETF providers supported (iShares, Amundi, VanEck, Xtrackers, etc.)
- Live pricing via yfinance (no API key required)
- Interactive Streamlit dashboard
- Self-learning ISIN resolution (1099+ securities cached)

### Barriers for Non-Technical Users

| Barrier | Severity | Description |
|---------|----------|-------------|
| **Python Setup** | HIGH | venv, pip install, Python 3.9+ required |
| **Selenium/Chrome** | HIGH | Amundi adapter needs browser automation |
| **API Keys** | MEDIUM | Finnhub API key for ISIN resolution |
| **PDF Format** | MEDIUM | Only Trade Republic German "Kontoauszug" supported |
| **Interactive Prompts** | MEDIUM | Pipeline pauses for user input (new ETFs, tickers) |
| **No Documentation** | MEDIUM | README missing critical setup steps |
| **Manual Holdings** | LOW | Amundi ETFs need manual XLSX download |

---

## Target State (MVP)

### User Experience Goal
```
1. User installs Docker Desktop (one-time)
2. User runs: docker run -p 8501:8501 portfolio-prism
3. User opens browser: http://localhost:8501
4. User uploads portfolio CSV (ISIN, Quantity)
5. User sees True Exposure dashboard
```

### MVP Scope

#### In Scope
- [x] CSV-based portfolio input (bypass PDF parsing)
- [ ] Docker container with all dependencies baked in
- [ ] Web-based file upload (no CLI interaction)
- [ ] Pre-populated ETF holdings cache (top 20 ETFs)
- [ ] Graceful degradation without API keys
- [ ] User-friendly error messages

#### Out of Scope (Future)
- ~~Trade Republic API integration~~ → **Now in scope! (pytr POC validated)**
- Multi-broker PDF support
- User accounts / portfolio saving
- Mobile app

---

## Phase 1: pytr Integration (COMPLETED 2025-12-03)

### What Was Done
- Validated [pytr](https://github.com/pytr-org/pytr) as Trade Republic API client
- Successfully fetched live portfolio data (30 positions, €41,729)
- Integrated with existing pipeline (0.2% discrepancy vs pytr value)
- Documented workflow in README and test plan

### Key Findings
1. **pytr works reliably** - Fetches current holdings with ISIN + quantity
2. **Web login preferred** - 4-digit code required each session, keeps phone logged in
3. **Credentials file** - Stored in `~/.pytr/credentials`
4. **Format conversion** - Simple one-liner transforms pytr output to pipeline format
5. **Correct ISINs** - pytr provided 4 corrected ISINs vs PDF-derived data

### Workflow
```bash
# 1. Fetch portfolio (enter 4-digit code when prompted)
pytr portfolio --output /tmp/pytr_raw.csv

# 2. Convert to pipeline format
echo "ISIN,Quantity" > data/working/calculated_holdings.csv
tail -n +2 /tmp/pytr_raw.csv | cut -d';' -f2,3 | tr ';' ',' >> data/working/calculated_holdings.csv

# 3. Run pipeline
python -m scripts.run_pipeline
```

### Next Steps for Phase 2
- [ ] Create `scripts/fetch_tr.py` to wrap pytr workflow
- [ ] Add pytr to requirements.txt
- [ ] Handle session persistence (--save-cookies)
- [ ] Error handling for auth failures

---

## Architecture Decisions

### Decision 1: Input Method

**Options Considered:**

| Option | Pros | Cons |
|--------|------|------|
| **A. PDF Parsing** | Automatic, no user effort | Only Trade Republic, complex setup |
| **B. CSV Upload** | Works with any broker, simple | User must create CSV manually |
| **C. Broker API** | Fully automatic | Unofficial APIs, legal grey area |
| **D. Screenshot OCR** | Visual, intuitive | Unreliable, complex |

**Decision:** **Option B (CSV Upload)** for MVP
- Trade Republic doesn't provide portfolio export, only transaction PDFs
- CSV is universal - works with any broker
- Users can copy from broker app → Excel → CSV
- PDF parsing remains available as power-user feature

**CSV Format:**
```csv
ISIN,Quantity
IE00B4L5Y983,119.06
US67066G1040,10.18
DE000A0F5UF5,6.99
```

---

### Decision 2: Deployment Method

**Options Considered:**

| Option | Effort | User Experience | Control |
|--------|--------|-----------------|---------|
| **A. Streamlit Cloud** | Low | Link sharing, no install | Low (public URL) |
| **B. Docker Container** | Medium | `docker run` command | High |
| **C. PyInstaller (.exe/.dmg)** | High | Double-click to run | High |
| **D. Local Python install** | Low | Current state | Low |

**Decision:** **Option B (Docker Container)** for MVP
- Full control over environment (Python, Chrome, dependencies)
- API keys can be baked in (not exposed to users)
- Works on Mac, Windows, Linux
- Single command to run
- No Python knowledge required

**Docker Strategy:**
```dockerfile
FROM python:3.11-slim
# Install Chrome for Selenium (if keeping Amundi)
# Copy pre-built asset_universe.csv and ETF cache
# Bake in API keys as build args (not in image layers)
EXPOSE 8501
CMD ["streamlit", "run", "src/dashboard/app.py"]
```

---

### Decision 3: API Key Handling

**Options Considered:**

| Option | Security | User Experience |
|--------|----------|-----------------|
| **A. User provides own keys** | High | Friction (registration required) |
| **B. Bake keys into Docker** | Medium | Zero friction |
| **C. Proxy through your server** | High | Requires hosting |
| **D. Remove API dependency** | High | Limited functionality |

**Decision:** **Option B (Bake keys)** for MVP with friends/family
- Finnhub free tier: 60 calls/min (sufficient for personal use)
- Keys are in Docker image but not easily extractable
- For public release, switch to Option A or C

**Implementation:**
```dockerfile
ARG FINNHUB_API_KEY
ENV FINNHUB_API_KEY=$FINNHUB_API_KEY
```

Build command (not shared):
```bash
docker build --build-arg FINNHUB_API_KEY=xxx -t portfolio-prism .
```

---

### Decision 4: Selenium/Amundi Handling

**Options Considered:**

| Option | Complexity | Reliability |
|--------|------------|-------------|
| **A. Keep Selenium in Docker** | High | Medium (Chrome updates) |
| **B. Pre-cache Amundi ETFs** | Low | High (static data) |
| **C. Manual upload only** | Low | High |
| **D. Remove Amundi support** | Low | N/A |

**Decision:** **Option B + C (Pre-cache + Manual upload)**
- Pre-download holdings for common Amundi ETFs (LU0908500753, FR0010361683, etc.)
- Add "Upload ETF Holdings" button in dashboard for missing ETFs
- Remove Selenium dependency entirely (simplifies Docker)

---

## Implementation Phases

### Phase 1: Documentation (1 day) - CURRENT
- [x] Create MVP-plan.md (this document)
- [x] Create .env.example
- [ ] Restructure README.md
- [ ] Update QUICKSTART.md

### Phase 2: CSV Input Mode (1-2 days)
- [ ] Add "Upload Portfolio" tab to dashboard
- [ ] Validate CSV format (ISIN checksum, numeric quantities)
- [ ] Create portfolio_template.csv with instructions
- [ ] Support paste-from-clipboard (for mobile users)
- [ ] Auto-detect common broker formats

### Phase 3: Remove Selenium Dependency (1 day)
- [ ] Pre-cache top 20 ETF holdings in `data/working/cache/`
- [ ] Add "Upload ETF Holdings" modal in dashboard
- [ ] Make Amundi adapter gracefully skip if no data
- [ ] Remove selenium from requirements.txt

### Phase 4: Reduce API Dependency (1 day)
- [ ] Expand asset_universe.csv (1099 → 2000+ securities)
- [ ] Add `--offline` mode flag
- [ ] Graceful degradation: skip enrichment if no API key
- [ ] Cache FX rates locally

### Phase 5: Docker Container (2-3 days)
- [ ] Create Dockerfile
- [ ] Create docker-compose.yml
- [ ] Test on Mac, Windows, Linux
- [ ] Create build script with API key injection
- [ ] Write Docker usage instructions
- [ ] Publish to Docker Hub (private or public)

### Phase 6: UX Polish (1-2 days)
- [ ] Add loading spinners during pipeline
- [ ] Create sample portfolio for demo mode
- [ ] Improve error messages ("ISIN not found" → "Did you mean...?")
- [ ] Add "Export Results" button (CSV, Excel)
- [ ] Add tooltips and help text

---

## File Changes Required

### New Files
- `docs/plans/MVP-plan.md` (this file)
- `.env.example`
- `Dockerfile`
- `docker-compose.yml`
- `data/templates/portfolio_template.csv`
- `src/dashboard/tabs/upload.py`

### Modified Files
- `README.md` - Restructure for users
- `QUICKSTART.md` - Align with README
- `requirements.txt` - Remove selenium (optional)
- `src/dashboard/app.py` - Add upload tab
- `src/adapters/amundi.py` - Graceful skip mode

### Files to Pre-populate
- `data/working/cache/adapter_cache/` - Top 20 ETF holdings
- `config/asset_universe.csv` - Expand to 2000+ securities

---

## Testing Plan

### Test Users
1. **Techy friend** - Can use current state with better docs
2. **Semi-technical family** - Needs Docker, clear instructions
3. **Non-technical family** - Needs hosted solution (future)

### Test Scenarios
1. Fresh install on Mac (Docker)
2. Fresh install on Windows (Docker)
3. Upload CSV with 10 positions
4. Upload CSV with 50 positions (includes unknown ETFs)
5. Run without API keys (offline mode)
6. Handle Amundi ETF (manual upload flow)

---

## Open Questions

1. **Which brokers do test users have?**
   - Trade Republic → CSV creation guide needed
   - Scalable Capital → Different format?
   - Interactive Brokers → API available?

2. **Do test users own Amundi ETFs?**
   - If yes: Need pre-cache or manual upload
   - If no: Can remove Selenium entirely

3. **Hosting for non-technical users?**
   - Streamlit Cloud (free, public URL)
   - Personal server (more control)
   - Skip for MVP?

4. **Open source or private?**
   - Private: Bake API keys, share Docker image
   - Public: Users provide own keys, GitHub release

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Time to first dashboard | < 10 minutes |
| Setup steps | < 5 commands |
| User questions during setup | 0 |
| Pipeline success rate | > 95% |
| Positions correctly valued | > 98% |

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-03 | Initial draft based on POC analysis |
