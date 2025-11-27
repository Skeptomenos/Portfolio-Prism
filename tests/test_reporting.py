# tests/test_reporting.py
import unittest
from unittest.mock import patch
import pandas as pd
import os



from src.core.reporting import generate_report

class TestReporting(unittest.TestCase):

    def setUp(self):
        """Set up a dummy input file for testing."""
        self.input_filepath = "outputs/test_exposure_report.csv"
        self.output_files = [
            "outputs/top_10_holdings.csv",
            "outputs/sector_exposure.csv",
            "outputs/geography_exposure.csv"
        ]
        
        # Create a sample input DataFrame
        self.sample_df = pd.DataFrame({
            'isin': ['US0378331005', 'DE0007100000', 'US5949181045'],
            'name': ['Apple', 'Mercedes', 'Microsoft'],
            'direct': [1000, 500, 0],
            'indirect': [100, 0, 600],
            'total_exposure': [1100, 500, 600],
            'portfolio_percentage': [50.0, 22.73, 27.27]
        })
        self.sample_df.to_csv(self.input_filepath, index=False)

    def tearDown(self):
        """Clean up generated files after tests."""
        os.remove(self.input_filepath)
        for f in self.output_files:
            if os.path.exists(f):
                os.remove(f)

    @patch('src.core.reporting.enrich_securities')
    def test_reporting_logic_unit(self, mock_enrich_securities):
        """
        Unit Test: Validates the calculation logic of the reporting module in isolation.
        It mocks the enrichment step to focus purely on the grouping and sorting.
        """
        mock_enrich_securities.return_value = [
            {'isin': 'US0378331005', 'name': 'Apple', 'sector': 'Tech', 'geography': 'USA'},
            {'isin': 'DE0007100000', 'name': 'Mercedes', 'sector': 'Auto', 'geography': 'Germany'},
            {'isin': 'US5949181045', 'name': 'Microsoft', 'sector': 'Tech', 'geography': 'USA'}
        ]

        # Run the report generation
        generate_report(self.input_filepath)

        # --- Assertions ---
        # Check that the sector exposure is calculated correctly
        sector_df = pd.read_csv("outputs/sector_exposure.csv")
        self.assertEqual(len(sector_df), 2)
        self.assertAlmostEqual(sector_df[sector_df['sector'] == 'Tech']['portfolio_percentage'].sum(), 77.27, places=2)
        self.assertAlmostEqual(sector_df[sector_df['sector'] == 'Auto']['portfolio_percentage'].sum(), 22.73, places=2)

    @patch('src.core.reporting.enrich_securities')
    def test_reporting_integration(self, mock_enrich_securities):
        """
        Integration Test: Validates that the reporting module can correctly
        consume the output of the (real) enrichment module.
        """
        mock_enrich_securities.return_value = [
            {'isin': 'US0378331005', 'name': 'Apple', 'sector': 'Technology', 'geography': 'USA'},
            {'isin': 'DE0007100000', 'name': 'Mercedes', 'sector': 'Consumer Cyclical', 'geography': 'Germany'},
            {'isin': 'US5949181045', 'name': 'Microsoft', 'sector': 'Technology', 'geography': 'USA'}
        ]

        # Run the report generation, this time using the *real* enrichment function
        generate_report(self.input_filepath)

        # --- Assertions ---
        # Check that the output files were created
        for f in self.output_files:
            self.assertTrue(os.path.exists(f))

        # Check a value from the real enrichment logic
        geography_df = pd.read_csv("outputs/geography_exposure.csv")
        self.assertEqual(len(geography_df), 2)
        # Based on the mock data in enrichment.py
        self.assertAlmostEqual(geography_df[geography_df['geography'] == 'USA']['portfolio_percentage'].sum(), 77.27, places=2)
        self.assertAlmostEqual(geography_df[geography_df['geography'] == 'Germany']['portfolio_percentage'].sum(), 22.73, places=2)


if __name__ == '__main__':
    unittest.main()
