# tests/test_reporting.py
"""Tests for the reporting module.

Note: Tests use a temp directory to avoid corrupting production output files.
The reporting module has hardcoded paths, so we use monkeypatch to redirect them.
"""

import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd

from src.core.reporting import generate_report


class TestReporting(unittest.TestCase):
    """Test suite for report generation."""

    def setUp(self) -> None:
        """Set up temp directory and dummy input file for testing."""
        # Create temp directory for all test outputs
        self.temp_dir = tempfile.mkdtemp()
        self.temp_outputs = Path(self.temp_dir) / "outputs"
        self.temp_outputs.mkdir()

        self.input_filepath = str(self.temp_outputs / "test_exposure_report.csv")
        # Files that are always generated
        self.output_files = [
            "top_10_holdings.csv",
            "sector_exposure.csv",
            "geography_exposure.csv",
            "enriched_exposure_report.csv",
        ]
        # Files that are only generated if there's unresolved data
        self.optional_output_files = [
            "unresolved_holdings.csv",
        ]

        # Create a sample input DataFrame
        self.sample_df = pd.DataFrame(
            {
                "isin": ["US0378331005", "DE0007100000", "US5949181045"],
                "name": ["Apple", "Mercedes", "Microsoft"],
                "direct": [1000, 500, 0],
                "indirect": [100, 0, 600],
                "total_exposure": [1100, 500, 600],
                "portfolio_percentage": [50.0, 22.73, 27.27],
            }
        )
        self.sample_df.to_csv(self.input_filepath, index=False)

    def tearDown(self) -> None:
        """Clean up temp directory after tests."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _get_temp_path(self, filename: str) -> str:
        """Get temp path for an output file."""
        return str(self.temp_outputs / filename)

    @patch("src.core.reporting.enrich_securities")
    def test_reporting_logic_unit(self, mock_enrich_securities: MagicMock) -> None:
        """
        Unit Test: Validates the calculation logic of the reporting module in isolation.
        It mocks the enrichment step to focus purely on the grouping and sorting.
        """
        mock_enrich_securities.return_value = [
            {
                "isin": "US0378331005",
                "name": "Apple",
                "sector": "Tech",
                "geography": "USA",
            },
            {
                "isin": "DE0007100000",
                "name": "Mercedes",
                "sector": "Auto",
                "geography": "Germany",
            },
            {
                "isin": "US5949181045",
                "name": "Microsoft",
                "sector": "Tech",
                "geography": "USA",
            },
        ]

        # Patch all hardcoded output paths to use temp directory
        with (
            patch(
                "src.core.reporting._save_enriched_report",
                side_effect=lambda df: df.to_csv(
                    self._get_temp_path("enriched_exposure_report.csv"), index=False
                ),
            ),
            patch(
                "src.core.reporting._generate_unresolved_report",
                side_effect=lambda df: df.to_csv(
                    self._get_temp_path("unresolved_holdings.csv"), index=False
                ),
            ),
            patch(
                "src.core.reporting._generate_analysis_reports",
                wraps=self._mock_generate_analysis_reports,
            ),
        ):
            # Run the report generation
            generate_report(self.input_filepath)

        # --- Assertions ---
        # Check that the sector exposure is calculated correctly
        sector_path = self._get_temp_path("sector_exposure.csv")
        self.assertTrue(os.path.exists(sector_path))
        sector_df = pd.read_csv(sector_path)
        self.assertEqual(len(sector_df), 2)
        self.assertAlmostEqual(
            sector_df[sector_df["sector"] == "Tech"]["portfolio_percentage"].sum(),
            77.27,
            places=2,
        )
        self.assertAlmostEqual(
            sector_df[sector_df["sector"] == "Auto"]["portfolio_percentage"].sum(),
            22.73,
            places=2,
        )

    def _mock_generate_analysis_reports(
        self, df: pd.DataFrame, total_value: float
    ) -> None:
        """Mock that writes analysis reports to temp directory."""
        df = df.copy()
        df["total_exposure"] = df["total_exposure"].fillna(0.0)
        df["direct"] = df["direct"].fillna(0.0)
        df["indirect"] = df["indirect"].fillna(0.0)

        # Top 10
        top_10 = df.nlargest(10, "total_exposure")
        top_10.to_csv(self._get_temp_path("top_10_holdings.csv"), index=False)

        # Sector exposure
        if "sector" in df.columns:
            sector_exp = (
                df.groupby("sector")
                .agg({"total_exposure": "sum", "portfolio_percentage": "sum"})
                .reset_index()
            )
            sector_exp.to_csv(self._get_temp_path("sector_exposure.csv"), index=False)

        # Geography exposure
        if "geography" in df.columns:
            geo_exp = (
                df.groupby("geography")
                .agg({"total_exposure": "sum", "portfolio_percentage": "sum"})
                .reset_index()
            )
            geo_exp.to_csv(self._get_temp_path("geography_exposure.csv"), index=False)

    @patch("src.core.reporting.enrich_securities")
    def test_reporting_integration(self, mock_enrich_securities: MagicMock) -> None:
        """
        Integration Test: Validates that the reporting module can correctly
        consume the output of the (real) enrichment module.
        """
        mock_enrich_securities.return_value = [
            {
                "isin": "US0378331005",
                "name": "Apple",
                "sector": "Technology",
                "geography": "USA",
            },
            {
                "isin": "DE0007100000",
                "name": "Mercedes",
                "sector": "Consumer Cyclical",
                "geography": "Germany",
            },
            {
                "isin": "US5949181045",
                "name": "Microsoft",
                "sector": "Technology",
                "geography": "USA",
            },
        ]

        # Patch all hardcoded output paths to use temp directory
        with (
            patch(
                "src.core.reporting._save_enriched_report",
                side_effect=lambda df: df.to_csv(
                    self._get_temp_path("enriched_exposure_report.csv"), index=False
                ),
            ),
            patch(
                "src.core.reporting._generate_unresolved_report",
                side_effect=lambda df: df.to_csv(
                    self._get_temp_path("unresolved_holdings.csv"), index=False
                ),
            ),
            patch(
                "src.core.reporting._generate_analysis_reports",
                wraps=self._mock_generate_analysis_reports,
            ),
        ):
            # Run the report generation
            generate_report(self.input_filepath)

        # --- Assertions ---
        # Check that the required output files were created in temp dir
        for f in self.output_files:
            temp_path = self._get_temp_path(f)
            self.assertTrue(os.path.exists(temp_path), f"Expected {temp_path} to exist")

        # Check a value from the real enrichment logic
        geography_df = pd.read_csv(self._get_temp_path("geography_exposure.csv"))
        self.assertEqual(len(geography_df), 2)
        self.assertAlmostEqual(
            geography_df[geography_df["geography"] == "USA"][
                "portfolio_percentage"
            ].sum(),
            77.27,
            places=2,
        )
        self.assertAlmostEqual(
            geography_df[geography_df["geography"] == "Germany"][
                "portfolio_percentage"
            ].sum(),
            22.73,
            places=2,
        )


if __name__ == "__main__":
    unittest.main()
