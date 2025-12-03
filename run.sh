#!/bin/bash
# run.sh - Portfolio Prism main entry point

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Set PYTHONPATH to current directory so 'src' is discoverable
export PYTHONPATH=$PYTHONPATH:.

# Check for Virtual Environment
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo -e "${YELLOW}Warning: 'venv' not found. Running with system python.${NC}"
fi

echo ""
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
            echo ""
            echo -e "${GREEN}Processing PDF exports...${NC}"
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
