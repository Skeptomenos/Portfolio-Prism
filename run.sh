#!/bin/bash
# run.sh

# Set PYTHONPATH to current directory so 'src' is discoverable
export PYTHONPATH=$PYTHONPATH:.

# Check for Virtual Environment
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "Warning: 'venv' not found. Running with system python."
fi

echo "--- Portfolio Master Pipeline ---"
echo "1. Running Database Setup (Parsing PDFs - CSV Mode)..."
# python -m scripts.setup_db_legacy
python -m scripts.parse_pdfs_to_csv --mode add_new

echo "2. Running Core Pipeline..."
python -m scripts.run_pipeline

echo "--- Done ---"
