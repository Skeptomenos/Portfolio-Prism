#!/usr/bin/env python3
"""
Unified Pipeline Entry Point

Orchestrates the complete end-to-end flow:
1. Parse PDFs -> Calculate current positions
2. Run Pipeline -> Enrich and Aggregate data
3. Validate -> Compare against ground truth

Usage:
    python -m scripts.run_full_pipeline
"""

import sys
from src.utils.logging_config import get_logger

# Import steps
from scripts.parse_pdfs_to_csv import main as run_pdf_parser
from scripts.run_pipeline import run_pipeline
from scripts.validate_pipeline import main as run_validation

logger = get_logger(__name__)


def main():
    print("=" * 80)
    print("🚀 STARTING FULL PIPELINE EXECUTION")
    print("=" * 80)

    # --- STEP 1: PDF PARSING ---
    print("\n[STEP 1/3] Parsing PDFs and Calculating Positions...")
    try:
        # We need to simulate command line args for the parser script
        # Default mode is 'add_new', but we might want 'merge' to ensure updates
        # For now, let's stick to default behavior which is interactive/cli based
        # But here we are calling the main function directly.
        # The parser's main() uses argparse, so we need to patch sys.argv or refactor

        # Simpler approach: Call the logic functions directly if possible,
        # or just invoke main() with patched args.

        original_argv = sys.argv
        sys.argv = ["parse_pdfs_to_csv.py", "--mode", "merge"]  # Force update/merge
        run_pdf_parser()
        sys.argv = original_argv

        print("✅ Step 1 Complete: Positions calculated.")
    except Exception as e:
        logger.error(f"❌ Step 1 Failed: {e}")
        sys.exit(1)

    # --- STEP 2: PIPELINE EXECUTION ---
    print("\n[STEP 2/3] Running Enrichment and Aggregation Pipeline...")
    try:
        run_pipeline()
        print("✅ Step 2 Complete: Reports generated.")
    except Exception as e:
        logger.error(f"❌ Step 2 Failed: {e}")
        sys.exit(1)

    # --- STEP 3: VALIDATION ---
    print("\n[STEP 3/3] Validating Output against Ground Truth...")
    try:
        exit_code = run_validation()
        if exit_code == 0:
            print("✅ Step 3 Complete: Validation Passed!")
        else:
            print("⚠️ Step 3 Complete: Validation Warnings Found (see report above).")
            # We don't exit with error here, just warn
    except Exception as e:
        logger.error(f"❌ Step 3 Failed: {e}")
        sys.exit(1)

    print("\n" + "=" * 80)
    print("🏁 FULL PIPELINE EXECUTION FINISHED")
    print("=" * 80)


if __name__ == "__main__":
    main()
