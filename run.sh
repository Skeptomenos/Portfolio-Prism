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
echo "1. Running Database Setup (Parsing PDFs)..."
python scripts/setup_db.py

echo "2. Running Core Pipeline..."
python scripts/run_pipeline.py

echo "--- Done ---"
