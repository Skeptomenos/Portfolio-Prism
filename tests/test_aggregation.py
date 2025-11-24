import unittest
import pandas as pd
from pandas.testing import assert_frame_equal
import sys
import os



from src.core.aggregation import run_aggregation

from unittest import mock

class TestAggregation(unittest.TestCase):

    @mock.patch('phases.active.aggregation.fetch_etf_holdings')
    def test_aggregation_with_overlapping_indirect_holdings(self, mock_fetch_holdings):
        """
        Tests the specific scenario where a security is held directly and also
        appears in multiple ETFs, verifying the aggregation logic correctly sums
        all sources of exposure. This is the regression test for Feedback #1.
        """
        # 1. Define Input DataFrames
        direct_positions = pd.DataFrame({'isin': ['AAPL'], 'name': ['Apple Inc.'], 'market_value': [100.00]})
        etf_positions = pd.DataFrame({'isin': ['TechETF1', 'TechETF2'], 'name': ['Tech 1', 'Tech 2'], 'market_value': [1000.00, 2000.00]})
        
        holdings1 = pd.DataFrame({'isin': ['AAPL', 'MSFT'], 'name': ['Apple', 'Microsoft'], 'weight_percentage': [10.0, 20.0]})
        holdings2 = pd.DataFrame({'isin': ['AAPL', 'GOOG'], 'name': ['Apple', 'Google'], 'weight_percentage': [5.0, 15.0]})

        etf_holdings_map = {
            'TechETF1': holdings1,
            'TechETF2': holdings2
        }

        # 2. Run the aggregation logic
        output_file = os.path.join(project_root, 'outputs', 'true_exposure_report.csv')
        if os.path.exists(output_file):
            os.remove(output_file)
        
        run_aggregation(direct_positions, etf_positions, etf_holdings_map)
        
        self.assertTrue(os.path.exists(output_file))
        actual_df = pd.read_csv(output_file)

        # 3. Define Expected Outcome and Assert
        aapl_row = actual_df[actual_df['isin'] == 'AAPL']
        self.assertFalse(aapl_row.empty)
        
        self.assertAlmostEqual(aapl_row['direct'].iloc[0], 100.0, places=2)
        self.assertAlmostEqual(aapl_row['indirect'].iloc[0], 200.0, places=2)
        self.assertAlmostEqual(aapl_row['total_exposure'].iloc[0], 300.0, places=2)

if __name__ == '__main__':
    unittest.main()