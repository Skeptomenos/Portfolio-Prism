import unittest
from unittest.mock import patch
import pandas as pd
import os


from src.adapters.vaneck import VanEckAdapter
from src.adapters.ishares import ISharesAdapter
from src.adapters.xtrackers import XtrackersAdapter

class TestAdapters(unittest.TestCase):

    def get_fixture_path(self, name):
        return os.path.join(project_root, 'tests', 'fixtures', name)

    @patch('requests.get')
    def test_vaneck_adapter_contract(self, mock_get):
        """
        Contract Test: Validates the VanEckAdapter against a saved local fixture.
        """
        # Mock the response from requests.get
        fixture_path = self.get_fixture_path('vaneck_holdings.xlsx')
        with open(fixture_path, 'rb') as f:
            mock_get.return_value.content = f.read()
        
        adapter = VanEckAdapter(isin="IE000YYE6WK5")
        df = adapter.fetch_holdings(isin="IE000YYE6WK5")

        # Assert the contract
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)
        self.assertIn('name', df.columns)
        self.assertIn('ticker', df.columns)
        self.assertIn('weight_percentage', df.columns)
        self.assertTrue(pd.api.types.is_numeric_dtype(df['weight_percentage']))

    @patch('requests.get')
    def test_ishares_adapter_contract(self, mock_get):
        """
        Contract Test: Validates the ISharesAdapter against a saved local fixture.
        """
        # Mock the response from requests.get
        fixture_path = self.get_fixture_path('ishares_holdings.csv')
        with open(fixture_path, 'r') as f:
            mock_get.return_value.text = f.read()

        adapter = ISharesAdapter()
        df = adapter.fetch_holdings(isin="IE00B4L5Y983")

        # Assert the contract
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)
        self.assertIn('name', df.columns)
        self.assertIn('ticker', df.columns)
        self.assertIn('weight_percentage', df.columns)
        self.assertTrue(pd.api.types.is_numeric_dtype(df['weight_percentage']))

    # @patch('requests.get')
    # def test_xtrackers_adapter_contract(self, mock_get):
    #     """
    #     Contract Test: Validates the XtrackersAdapter against a saved local fixture.
    #     (Skipped for now due to download issues)
    #     """
    #     # Mock the response from requests.get
    #     fixture_path = self.get_fixture_path('xtrackers_holdings.csv')
    #     with open(fixture_path, 'r') as f:
    #         mock_get.return_value.text = f.read()

    #     adapter = XtrackersAdapter()
    #     df = adapter.fetch_holdings(isin="IE00B1CD3B44")

    #     # Assert the contract
    #     self.assertIsInstance(df, pd.DataFrame)
    #     self.assertFalse(df.empty)
    #     self.assertIn('name', df.columns)
    #     self.assertIn('ticker', df.columns)
    #     self.assertIn('weight_percentage', df.columns)
    #     self.assertTrue(pd.api.types.is_numeric_dtype(df['weight_percentage']))

if __name__ == '__main__':
    unittest.main()
