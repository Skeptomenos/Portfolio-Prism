# Quickstart Guide

Get your portfolio analysis running in minutes.

## Option A: Docker (Recommended for Friends)

The easiest way to run Portfolio Prism - no Python installation required.

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running

### 1. Create a Project Folder

```bash
mkdir portfolio-prism && cd portfolio-prism
```

### 2. Download Docker Compose File

```bash
curl -O https://raw.githubusercontent.com/Skeptomenos/Portfolio-Prism/main/docker-compose.yml
```

Or create `docker-compose.yml` manually:

```yaml
version: '3.8'
services:
  portfolio-prism:
    image: ghcr.io/skeptomenos/portfolio-prism:latest
    ports:
      - "8501:8501"
    volumes:
      - ./data:/app/data
      - ./config:/app/config
    environment:
      - DOCKER_MODE=true
    restart: unless-stopped
```

### 3. Add Your Data

Create the required folders and add your files:

```bash
mkdir -p data/inputs/portfolio
mkdir -p data/inputs/manual_holdings
```

**Portfolio PDFs:** Place your Trade Republic PDF exports in:
```
data/inputs/portfolio/
```

**ETF Holdings (Optional):** For Amundi ETFs, download the holdings XLSX and save as:
```
data/inputs/manual_holdings/{ISIN}.xlsx
```

### 4. Start the Dashboard

```bash
docker compose up -d
```

### 5. Open the Dashboard

Visit [http://localhost:8501](http://localhost:8501) in your browser.

### Updating

To get the latest version:

```bash
docker compose pull
docker compose up -d
```

---

## Option B: Local Python Installation

For developers or those who want to modify the code.

### Prerequisites
- Python 3.9+
- `pip`

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/Skeptomenos/Portfolio-Prism.git
cd Portfolio-Prism/POC

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install the package
pip install -e .

# Install Playwright browser (for Vanguard/Amundi ETFs)
playwright install chromium
```

### 2. Setup Data

**Portfolio PDFs:** Place Trade Republic exports in:
```
data/inputs/portfolio/
```

**ETF Holdings (Amundi):** Download and save as:
```
data/inputs/manual_holdings/{ISIN}.xlsx
```

### 3. Run the Pipeline

```bash
bash run.sh
```

### 4. View Dashboard

```bash
./run_dashboard.sh
```

Visit [http://localhost:8501](http://localhost:8501)

---

## Managing ETF Holdings (Docker Mode)

In Docker mode, some ETF providers (Amundi) require manual file uploads since browser automation isn't available.

### Using the Dashboard

1. Go to the **Data Manager** tab
2. Scroll to **Holdings Cache Management**
3. Click **Sync Community Data** to download pre-cached ETF holdings
4. For missing ETFs, use the **Manual Holdings Upload** widget:
   - Upload CSV/XLSX from the provider
   - Enter the ETF ISIN
   - Click **Save to Cache**

### Supported Formats

The upload widget auto-normalizes files from:
- iShares
- Amundi
- Vanguard
- Xtrackers
- VanEck

Files should contain at minimum:
- Name/Security column
- Weight/Allocation column
- ISIN column (optional but recommended)

---

## Troubleshooting

### "No holdings data for {ISIN}"

1. Check if the ETF is in community data: **Data Manager → Sync Community Data**
2. Upload manually: Download holdings from provider website, upload in Data Manager

### Dashboard won't start

```bash
# Check if port 8501 is in use
lsof -i :8501

# Restart container
docker compose restart
```

### Container logs

```bash
docker compose logs -f
```

---

## Output Files

After running the pipeline, find your results in:

| File | Description |
|------|-------------|
| `outputs/true_exposure_report.csv` | Full look-through exposure |
| `outputs/data_quality_report.txt` | Missing data details |
| `outputs/trades.csv` | Parsed transaction history |
