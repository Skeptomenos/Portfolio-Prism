"""Tests for the aggregation module."""

import os
import unittest

import pandas as pd

from src.config import TRUE_EXPOSURE_REPORT
from src.core.aggregation import run_aggregation


class TestAggregation(unittest.TestCase):
    """Test suite for aggregation logic."""

    def test_aggregation_with_overlapping_indirect_holdings(self) -> None:
        """
        Tests the specific scenario where a security is held directly and also
        appears in multiple ETFs, verifying the aggregation logic correctly sums
        all sources of exposure. This is the regression test for Feedback #1.

        Updated to use valid ISINs for the new resolution architecture.
        """
        # 1. Define Input DataFrames with valid ISINs
        # US0378331005 = Apple Inc (valid ISIN)
        # US5949181045 = Microsoft Corp (valid ISIN)
        # US02079K3059 = Alphabet Inc (valid ISIN)
        # DE000A0F5UF5 = iShares NASDAQ-100 ETF (valid ETF ISIN)
        # IE00B53SZB19 = iShares NASDAQ 100 ETF (valid ETF ISIN)

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

        # ETF holdings with valid ISINs
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

        etf_holdings_map = {"DE000A0F5UF5": holdings1, "IE00B53SZB19": holdings2}

        # 2. Run the aggregation logic
        output_file = str(TRUE_EXPOSURE_REPORT)
        if os.path.exists(output_file):
            os.remove(output_file)

        run_aggregation(direct_positions, etf_positions, etf_holdings_map)

        self.assertTrue(os.path.exists(output_file))
        actual_df = pd.read_csv(output_file)

        # 3. Define Expected Outcome and Assert
        aapl_row = actual_df[actual_df["isin"] == "US0378331005"]
        self.assertFalse(aapl_row.empty)

        self.assertAlmostEqual(float(aapl_row["direct"].iloc[0]), 100.0, places=2)
        self.assertAlmostEqual(float(aapl_row["indirect"].iloc[0]), 200.0, places=2)
        self.assertAlmostEqual(
            float(aapl_row["total_exposure"].iloc[0]), 300.0, places=2
        )


if __name__ == "__main__":
    unittest.main()
