"""
Unit and Integration Tests for the aggregation module.

This test suite verifies:
1. Individual module behavior (unit tests)
2. End-to-end aggregation behavior (integration test)
"""

import os
import unittest

import pandas as pd

from src.core.aggregation.classification import classify_etf_holdings
from src.core.aggregation.direct import process_direct_holdings
from src.core.aggregation.grouping import (
    aggregate_indirect_holdings,
    calculate_indirect_values,
    generate_group_id,
    normalize_special_assets,
)
from src.core.aggregation.output import finalize_and_save
from src.models import AggregatedExposure


class TestDirectModule(unittest.TestCase):
    """Tests for direct.py module."""

    def test_process_direct_holdings_adds_records(self) -> None:
        """Direct holdings are added to exposures with correct values."""
        direct_positions = pd.DataFrame(
            {
                "isin": ["US0378331005", "DE0007164600"],
                "name": ["Apple Inc.", "SAP SE"],
                "market_value": [1000.0, 500.0],
            }
        )
        exposures = AggregatedExposure()

        process_direct_holdings(direct_positions, exposures)

        self.assertEqual(len(exposures.records), 2)
        apple = exposures.get_record("US0378331005")
        self.assertIsNotNone(apple)
        self.assertEqual(apple.direct, 1000.0)
        self.assertEqual(apple.name, "Apple Inc.")

    def test_process_direct_holdings_empty_df(self) -> None:
        """Empty DataFrame results in no records."""
        direct_positions = pd.DataFrame(columns=["isin", "name", "market_value"])
        exposures = AggregatedExposure()

        process_direct_holdings(direct_positions, exposures)

        self.assertEqual(len(exposures.records), 0)


class TestClassificationModule(unittest.TestCase):
    """Tests for classification.py module."""

    def test_classify_etf_holdings_adds_asset_class(self) -> None:
        """Holdings get asset_class column after classification."""
        holdings = pd.DataFrame(
            {
                "ticker": ["AAPL", "USD CASH", "CALL 100"],
                "name": ["Apple Inc.", "US Dollar", "Call Option"],
            }
        )

        result = classify_etf_holdings(holdings)

        self.assertIn("asset_class", result.columns)
        self.assertEqual(len(result), 3)

    def test_classify_identifies_cash(self) -> None:
        """Cash holdings are identified correctly."""
        holdings = pd.DataFrame(
            {
                "ticker": ["USD CASH"],
                "name": ["US Dollar Cash"],
            }
        )

        result = classify_etf_holdings(holdings)

        self.assertEqual(result["asset_class"].iloc[0], "Cash")


class TestGroupingModule(unittest.TestCase):
    """Tests for grouping.py module."""

    def test_calculate_indirect_values(self) -> None:
        """Indirect values are calculated correctly from weights."""
        holdings = pd.DataFrame(
            {
                "ticker": ["AAPL", "MSFT"],
                "weight_percentage": [10.0, 5.0],
            }
        )
        etf_value = 10000.0

        result = calculate_indirect_values(holdings, etf_value)

        self.assertEqual(result["indirect"].iloc[0], 1000.0)  # 10% of 10000
        self.assertEqual(result["indirect"].iloc[1], 500.0)  # 5% of 10000

    def test_calculate_indirect_values_german_format(self) -> None:
        """German number format (comma as decimal) is handled."""
        holdings = pd.DataFrame(
            {
                "ticker": ["AAPL"],
                "weight_percentage": ["10,5"],  # German format
            }
        )
        etf_value = 1000.0

        result = calculate_indirect_values(holdings, etf_value)

        self.assertAlmostEqual(result["indirect"].iloc[0], 105.0, places=2)

    def test_generate_group_id_with_valid_isin(self) -> None:
        """Valid ISIN is used as group ID."""
        row = pd.Series({"isin": "US0378331005", "ticker": "AAPL", "name": "Apple"})

        result = generate_group_id(row)

        self.assertEqual(result, "US0378331005")

    def test_generate_group_id_fallback(self) -> None:
        """Fallback ID is generated when ISIN is invalid.

        Updated for new UNRESOLVED:{ticker}:{hash} format (ADR-004).
        """
        row = pd.Series({"isin": "N/A", "ticker": "AAPL", "name": "Apple Inc."})

        result = generate_group_id(row)

        # New format: UNRESOLVED:{ticker}:{10-digit-hash}
        self.assertTrue(result.startswith("UNRESOLVED:AAPL:"))
        # Hash is 10 digits
        hash_part = result.split(":")[-1]
        self.assertEqual(len(hash_part), 10)
        self.assertTrue(hash_part.isdigit())

    def test_normalize_special_assets_cash(self) -> None:
        """Cash holdings are normalized to CASH_USD."""
        holdings = pd.DataFrame(
            {
                "isin": ["some_random_id"],
                "name": ["US Dollar"],
                "asset_class": ["Cash"],
            }
        )

        result = normalize_special_assets(holdings)

        self.assertEqual(result["isin"].iloc[0], "CASH_USD")
        self.assertEqual(result["name"].iloc[0], "Cash & Equivalents")

    def test_aggregate_indirect_holdings(self) -> None:
        """Indirect holdings from multiple ETFs are summed correctly."""
        # Same security appearing in two ETFs
        all_holdings = pd.DataFrame(
            {
                "isin": ["US0378331005", "US0378331005"],
                "name": ["Apple", "Apple Inc."],
                "asset_class": ["Equity", "Equity"],
                "indirect": [100.0, 150.0],
            }
        )
        exposures = AggregatedExposure()

        aggregate_indirect_holdings(all_holdings, exposures)

        apple = exposures.get_record("US0378331005")
        self.assertIsNotNone(apple)
        self.assertEqual(apple.indirect, 250.0)


class TestOutputModule(unittest.TestCase):
    """Tests for output.py module."""

    def test_finalize_and_save_creates_file(self) -> None:
        """Output file is created with correct columns."""
        exposures = AggregatedExposure()
        record = exposures.get_or_create_record("ISIN123", "Test Stock", "Equity")
        record.direct = 100.0

        test_output = "/tmp/test_aggregation_output.csv"
        result = finalize_and_save(exposures, test_output)

        self.assertTrue(os.path.exists(test_output))
        self.assertIn("isin", result.columns)
        self.assertIn("total_exposure", result.columns)
        self.assertIn("portfolio_percentage", result.columns)

        # Cleanup
        os.remove(test_output)

    def test_finalize_and_save_empty_exposures(self) -> None:
        """Empty exposures produce empty DataFrame."""
        exposures = AggregatedExposure()
        test_output = "/tmp/test_empty_output.csv"

        result = finalize_and_save(exposures, test_output)

        self.assertTrue(result.empty)
        self.assertTrue(os.path.exists(test_output))

        # Cleanup
        os.remove(test_output)


class TestAggregationIntegration(unittest.TestCase):
    """
    Integration test for the aggregation module end-to-end.
    """

    def test_run_aggregation_overlapping_holdings(self) -> None:
        """
        Test that overlapping indirect holdings (same security in multiple ETFs)
        are correctly summed.

        This is a regression test for the core aggregation logic.
        Updated to use valid ISINs for the new resolution architecture.
        """
        from src.core.aggregation import run_aggregation

        # Test data with valid ISINs
        # US0378331005 = Apple Inc
        # US5949181045 = Microsoft Corp
        # US02079K3059 = Alphabet Inc
        # DE000A0F5UF5 = iShares NASDAQ-100 ETF
        # IE00B53SZB19 = iShares NASDAQ 100 ETF

        direct_positions = pd.DataFrame(
            {
                "isin": ["US0378331005"],
                "name": ["Apple Inc."],
                "market_value": [100.00],
            }
        )
        etf_positions = pd.DataFrame(
            {
                "isin": ["DE000A0F5UF5", "IE00B53SZB19"],
                "name": ["Tech 1", "Tech 2"],
                "market_value": [1000.00, 2000.00],
            }
        )
        holdings1 = pd.DataFrame(
            {
                "isin": ["US0378331005", "US5949181045"],
                "name": ["Apple", "Microsoft"],
                "weight_percentage": [10.0, 20.0],
            }
        )
        holdings2 = pd.DataFrame(
            {
                "isin": ["US0378331005", "US02079K3059"],
                "name": ["Apple", "Google"],
                "weight_percentage": [5.0, 15.0],
            }
        )
        etf_holdings_map = {
            "DE000A0F5UF5": holdings1,
            "IE00B53SZB19": holdings2,
        }

        # Run aggregation
        result_df = run_aggregation(direct_positions, etf_positions, etf_holdings_map)

        # Check Apple values (US0378331005)
        aapl_row = result_df[result_df["isin"] == "US0378331005"]
        self.assertFalse(aapl_row.empty, "Apple (US0378331005) should exist in output")

        # Direct = 100
        self.assertAlmostEqual(
            aapl_row["direct"].iloc[0],
            100.0,
            places=2,
            msg="Direct value should be 100",
        )

        # Indirect = 10% of 1000 + 5% of 2000 = 100 + 100 = 200
        self.assertAlmostEqual(
            aapl_row["indirect"].iloc[0],
            200.0,
            places=2,
            msg="Indirect value should be 200",
        )

        # Total = 300
        self.assertAlmostEqual(
            aapl_row["total_exposure"].iloc[0],
            300.0,
            places=2,
            msg="Total exposure should be 300",
        )


if __name__ == "__main__":
    unittest.main()
